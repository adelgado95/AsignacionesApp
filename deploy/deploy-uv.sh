#!/usr/bin/env bash
# Deploys the backend WITHOUT Docker, as a uv project: system libraries + uv + virtualenv from uv.lock,
# restores the SQLite backup, and runs gunicorn as a systemd service (Debian/Ubuntu).
#
# Copy the project folder (including deploy/prod.sqlite3) to the server and, as a normal user with sudo:
#   ./deploy/deploy-uv.sh --host central.admincong.online --origin https://central.admincong.online
#
# Options:
#   --db FILE      SQLite backup to restore            (default: deploy/prod.sqlite3)
#   --host H,H     ALLOWED_HOSTS for a new .env        (default: *, accepts any host)
#   --origin URL   extra CSRF_TRUSTED_ORIGINS (comma-separated)
#   --port N       gunicorn port                       (default: 8000)
#   --public       listen on 0.0.0.0 instead of 127.0.0.1 (default is localhost: put nginx in front)
#   --force        overwrite an existing database without asking (a copy is always kept)
#   --no-restore   keep the database already in ./data and only update/restart
#   --no-service   do not create the systemd unit (also allows running as root, e.g. in a container)
set -euo pipefail
cd "$(dirname "$0")/.."
APP_DIR="$(pwd)"

DB="deploy/prod.sqlite3"; HOSTS="*"; ORIGINS=""; PORT="8000"; BIND="127.0.0.1"; FORCE=0; RESTORE=1; SERVICE=1
while [ $# -gt 0 ]; do
  case "$1" in
    --db) DB="$2"; shift 2 ;;
    --host) HOSTS="$2"; shift 2 ;;
    --origin) ORIGINS="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --public) BIND="0.0.0.0"; shift ;;
    --force) FORCE=1; shift ;;
    --no-restore) RESTORE=0; shift ;;
    --no-service) SERVICE=0; shift ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    *) echo "Opción desconocida: $1" >&2; exit 1 ;;
  esac
done

log() { printf '\n==> %s\n' "$*"; }
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
if [ "$(id -u)" -eq 0 ] && [ "$SERVICE" -eq 1 ]; then
  echo "Ejecuta este script como un usuario normal con sudo (el servicio correrá con ese usuario), o usa --no-service." >&2
  exit 1
fi
SERVICE_NAME="asignaciones"
RUN_USER="$(id -un)"

# 1) System libraries (WeasyPrint needs Pango; pdf2image needs poppler) ----------------------------
if command -v apt-get >/dev/null 2>&1; then
  NEED=""
  for pkg in curl ca-certificates libpango-1.0-0 libpangoft2-1.0-0 poppler-utils; do
    dpkg -s "$pkg" >/dev/null 2>&1 || NEED="$NEED $pkg"
  done
  if [ -n "$NEED" ]; then
    log "Instalando paquetes del sistema:$NEED"
    $SUDO apt-get update -y
    $SUDO apt-get install -y $NEED
  fi
else
  echo "AVISO: sin apt-get. Instala a mano Pango (libpango-1.0-0, libpangoft2-1.0-0) y poppler-utils." >&2
fi

# 2) uv --------------------------------------------------------------------------------------------
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  log "Instalando uv (instalador oficial de astral.sh)"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
log "uv $(uv --version | cut -d' ' -f2): creando .venv desde uv.lock"
uv sync --frozen --no-dev        # --frozen: exactly what is in uv.lock; uv downloads Python 3.12 if the system lacks it

# 3) .env ------------------------------------------------------------------------------------------
if [ ! -f .env ]; then
  log "Creando .env de producción"
  SECRET="$(head -c 48 /dev/urandom | base64 | tr -d '\n=+/')"
  { echo "DEBUG=0"; echo "SECRET_KEY=$SECRET"; echo "ALLOWED_HOSTS=$HOSTS"; echo "CSRF_TRUSTED_ORIGINS=$ORIGINS"; } > .env
  chmod 600 .env
  [ "$HOSTS" = "*" ] && echo "AVISO: ALLOWED_HOSTS=* acepta cualquier host. Vuelve a ejecutar con --host tu.dominio o edita .env."
else
  log "Usando el .env existente (no se modifica)"
  grep -q '^SECRET_KEY=.\+' .env || { echo "El .env existente no tiene SECRET_KEY (obligatoria en producción)." >&2; exit 1; }
  grep -q '^ALLOWED_HOSTS=' .env || echo "AVISO: .env sin ALLOWED_HOSTS: se aceptan todos los hosts. Añade ALLOWED_HOSTS=tu.dominio"
fi
# Forced for every command and for the service, so a development .env can never turn DEBUG on or pick another database.
export DEBUG=0 SQL_FILE=data/prod.sqlite3
manage() { uv run --no-sync --env-file .env python manage.py "$@"; }

# 4) Restore the database ---------------------------------------------------------------------------
mkdir -p data
TARGET="data/prod.sqlite3"
if [ "$RESTORE" -eq 1 ]; then
  [ -f "$DB" ] || { echo "No encuentro el respaldo $DB (usa --db o --no-restore)" >&2; exit 1; }
  if [ -f "$TARGET" ]; then
    if [ "$FORCE" -ne 1 ]; then
      read -r -p "Ya existe $TARGET. ¿Reemplazarla con $DB? [s/N] " ans
      case "$ans" in s|S|y|Y) ;; *) echo "Cancelado: no se tocó la base de datos."; exit 1 ;; esac
    fi
    KEEP="$TARGET.antes-$(date +%Y%m%d-%H%M%S)"
    cp -p "$TARGET" "$KEEP"; echo "Copia de la base anterior: $KEEP"
    $SUDO systemctl stop "$SERVICE_NAME" 2>/dev/null || true     # nothing may write while the file is replaced
  fi
  log "Restaurando $DB -> $TARGET"
  cp "$DB" "$TARGET"; rm -f "$TARGET-wal" "$TARGET-shm"; chmod 600 "$TARGET"
else
  [ -f "$TARGET" ] || { echo "No hay $TARGET: ejecuta sin --no-restore para restaurar un respaldo." >&2; exit 1; }
fi

log "Comprobando la base de datos"
uv run --no-sync python - <<'PY'
import sqlite3
c = sqlite3.connect("data/prod.sqlite3")
assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "integrity_check falló"
print(f"base OK ({c.execute('SELECT count(*) FROM auth_user').fetchone()[0]} usuario(s))")
PY

# 5) Migrations and static files -------------------------------------------------------------------
log "migrate + collectstatic"
manage migrate --noinput
manage collectstatic --noinput | tail -1

# 6) Service ---------------------------------------------------------------------------------------
GUNICORN_ARGS="app.wsgi:application --bind $BIND:$PORT --workers 3 --timeout 60"
GUNICORN="$APP_DIR/.venv/bin/gunicorn $GUNICORN_ARGS"
if [ "$SERVICE" -eq 1 ]; then
  log "Instalando el servicio systemd '$SERVICE_NAME' (usuario $RUN_USER)"
  $SUDO tee "/etc/systemd/system/$SERVICE_NAME.service" >/dev/null <<UNIT
[Unit]
Description=Asignaciones backend (gunicorn)
After=network.target

[Service]
User=$RUN_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
Environment=DEBUG=0
Environment=SQL_FILE=data/prod.sqlite3
ExecStart=$GUNICORN
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT
  $SUDO systemctl daemon-reload
  $SUDO systemctl enable "$SERVICE_NAME" >/dev/null 2>&1
  $SUDO systemctl restart "$SERVICE_NAME"

  log "Esperando a que responda"
  for i in $(seq 1 30); do
    code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/admin/login/" || true)"
    [ "$code" = "200" ] && { echo "Servicio arriba (HTTP 200)"; break; }
    sleep 2
    [ "$i" -eq 30 ] && { echo "No respondió. Revisa: sudo journalctl -u $SERVICE_NAME -n 100 --no-pager" >&2; exit 1; }
  done
  cat <<MSG

Listo ($BIND:$PORT).
  Estado:  sudo systemctl status $SERVICE_NAME
  Logs:    sudo journalctl -u $SERVICE_NAME -f
  Reiniciar tras actualizar el código:  ./deploy/deploy-uv.sh --no-restore
  Base:    $APP_DIR/$TARGET   (haz copias de este archivo)
Pon nginx delante (deploy/nginx-central.admincong.online.conf) y luego certbot para HTTPS.
MSG
else
  cat <<MSG

Listo (sin servicio). Para arrancarlo a mano:
  cd $APP_DIR && DEBUG=0 SQL_FILE=data/prod.sqlite3 uv run --no-sync --env-file .env gunicorn $GUNICORN_ARGS
MSG
fi
