# Despliegue

## 1. Generar el respaldo (en tu máquina)
```bash
./deploy/make_backup.sh            # copia consistente de db.sqlite3 -> deploy/prod.sqlite3
```

## 2. Copiar al servidor y desplegar
```bash
rsync -av --exclude .git --exclude data --exclude '/*.sqlite3*' --exclude .env \
  ./ usuario@servidor:~/asignaciones/
ssh usuario@servidor
cd ~/asignaciones
./deploy/deploy.sh --host api.midominio.com --origin https://api.midominio.com
```
El script instala Docker si falta, crea `.env` (DEBUG=0, SECRET_KEY aleatoria), restaura `deploy/prod.sqlite3`
en `data/prod.sqlite3`, construye la imagen, levanta gunicorn y espera a que responda.

- Volver a ejecutarlo con una base existente pregunta antes de reemplazarla y guarda `data/prod.sqlite3.antes-<fecha>`.
- Actualizar el código sin tocar los datos: copia los archivos de nuevo y `./deploy/deploy.sh --no-restore`.
- Opciones: `--db`, `--host`, `--origin`, `--port`, `--force`, `--no-restore`.
- HTTPS: pon un proxy (Caddy, nginx, Cloudflare) delante del puerto 8000 y usa su URL `https://…` en la app.

## Alternativa sin Docker: proyecto uv + systemd (Debian/Ubuntu)
`pyproject.toml` + `uv.lock` definen las dependencias (mismas versiones que `requirements.txt`, ya resueltas y fijadas).
```bash
# como usuario normal con sudo, en la carpeta del proyecto (con deploy/prod.sqlite3 dentro)
./deploy/deploy-uv.sh --host central.admincong.online --origin https://central.admincong.online
```
Instala las librerías del sistema (Pango, poppler), uv, crea `.venv` con `uv sync --frozen`, restaura la base en
`data/prod.sqlite3`, corre `migrate` + `collectstatic` y deja gunicorn como servicio systemd `asignaciones`
escuchando en `127.0.0.1:8000` (usa nginx delante; `--public` para escuchar en 0.0.0.0).
Mismas opciones que `deploy.sh` (`--db --host --origin --port --force --no-restore`) más `--no-service`.
Para actualizar el código: copia los archivos y `./deploy/deploy-uv.sh --no-restore`.
Si cambias dependencias: edita `pyproject.toml`, `uv lock` y haz commit de `uv.lock` (y actualiza `requirements.txt` si usas Docker).

## 3. APK de la app móvil (otra carpeta: asignacionesMobileApp)
```bash
npx eas-cli login                                   # una vez
./scripts/build-apk.sh https://api.midominio.com    # APK con esa URL del backend
```
