#!/usr/bin/env bash
# Deploys the backend on a Linux server: installs Docker if missing, restores the SQLite backup
# and starts the production stack (gunicorn) with docker compose.
#
# Copy the project folder (including deploy/prod.sqlite3) to the server, then:
#   ./deploy/deploy.sh --host api.midominio.com
#
# Options:
#   --db FILE      SQLite backup to restore            (default: deploy/prod.sqlite3)
#   --host H,H     ALLOWED_HOSTS for a new .env        (default: *, accepts any host)
#   --origin URL   extra CSRF_TRUSTED_ORIGINS, e.g. https://api.midominio.com (comma-separated)
#   --port N       port published on the server        (default: 8000)
#   --force        overwrite an existing database without asking (a copy is always kept)
#   --no-restore   keep the database already in ./data and only (re)start the stack
set -euo pipefail
cd "$(dirname "$0")/.."

DB="deploy/prod.sqlite3"; HOSTS="*"; ORIGINS=""; PORT="8000"; FORCE=0; RESTORE=1
while [ $# -gt 0 ]; do
  case "$1" in
    --db) DB="$2"; shift 2 ;;
    --host) HOSTS="$2"; shift 2 ;;
    --origin) ORIGINS="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --no-restore) RESTORE=0; shift ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "Opción desconocida: $1" >&2; exit 1 ;;
  esac
done

log() { printf '\n==> %s\n' "$*"; }
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"

# 1) Docker -------------------------------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  log "Docker no está instalado: instalando con el script oficial (get.docker.com)"
  command -v curl >/dev/null 2>&1 || { $SUDO apt-get update -y && $SUDO apt-get install -y curl; }
  curl -fsSL https://get.docker.com | $SUDO sh
  $SUDO systemctl enable --now docker 2>/dev/null || true
fi
DOCKER="docker"
docker info >/dev/null 2>&1 || DOCKER="$SUDO docker"   # user not in the docker group yet
$DOCKER compose version >/dev/null 2>&1 || { echo "Falta el plugin 'docker compose'. Instálalo (docker-compose-plugin)." >&2; exit 1; }
COMPOSE="$DOCKER compose -f docker-compose.prod.yml"

# 2) .env ---------------------------------------------------------------------------------------
if [ ! -f .env ]; then
  log "Creando .env de producción"
  SECRET="$(head -c 48 /dev/urandom | base64 | tr -d '\n=+/')"
  {
    echo "DEBUG=0"
    echo "SECRET_KEY=$SECRET"
    echo "ALLOWED_HOSTS=$HOSTS"
    echo "CSRF_TRUSTED_ORIGINS=$ORIGINS"
    echo "PORT=$PORT"
  } > .env
  chmod 600 .env
  [ "$HOSTS" = "*" ] && echo "AVISO: ALLOWED_HOSTS=* acepta cualquier host. Vuelve a ejecutar con --host tu.dominio o edita .env."
else
  log "Usando el .env existente (no se modifica)"
  grep -q '^SECRET_KEY=.\+' .env || { echo "El .env existente no tiene SECRET_KEY (obligatoria en producción)." >&2; exit 1; }
  grep -q '^ALLOWED_HOSTS=' .env || echo "AVISO: .env sin ALLOWED_HOSTS: se aceptan todos los hosts. Añade ALLOWED_HOSTS=tu.dominio"
  grep -q '^PORT=' .env && PORT="$(grep '^PORT=' .env | cut -d= -f2)"
fi
export PORT

# 3) Restore the database -------------------------------------------------------------------------
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
    $COMPOSE down 2>/dev/null || true      # nothing may write while the file is replaced
  fi
  log "Restaurando $DB -> $TARGET"
  cp "$DB" "$TARGET"; rm -f "$TARGET-wal" "$TARGET-shm"
  chmod 666 "$TARGET"; chmod 777 data      # the container user must be able to write the file and its journal
else
  [ -f "$TARGET" ] || { echo "No hay $TARGET: ejecuta sin --no-restore para restaurar un respaldo." >&2; exit 1; }
fi

# 4) Build, check the database, start ------------------------------------------------------------
log "Construyendo la imagen"
$COMPOSE build
log "Comprobando la base de datos"
$COMPOSE run --rm --no-deps web python - <<'PY'
import sqlite3
c = sqlite3.connect("/data/prod.sqlite3")
assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "integrity_check falló"
n = c.execute("SELECT count(*) FROM auth_user").fetchone()[0]
print(f"base OK ({n} usuario(s))")
PY
log "Levantando el servicio (migraciones + collectstatic + gunicorn)"
$COMPOSE up -d

# 5) Health check -----------------------------------------------------------------------------------
log "Esperando a que responda"
for i in $(seq 1 45); do
  code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/admin/login/" || true)"
  [ "$code" = "200" ] && { echo "Servicio arriba (HTTP 200)"; break; }
  sleep 2
  [ "$i" -eq 45 ] && { echo "No respondió a tiempo. Revisa: $COMPOSE logs --tail=100 web" >&2; exit 1; }
done

cat <<MSG

Listo.
  Admin:  http://<IP-del-servidor>:$PORT/admin/
  API:    http://<IP-del-servidor>:$PORT/api/
  Logs:   $COMPOSE logs -f web
  Parar:  $COMPOSE down
  Base:   $(pwd)/$TARGET   (haz copias de este archivo)
Para la app móvil usa esa URL (o la de tu proxy HTTPS) en deploy: ../asignacionesMobileApp/scripts/build-apk.sh
MSG
