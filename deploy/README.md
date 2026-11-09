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

## 3. APK de la app móvil (otra carpeta: asignacionesMobileApp)
```bash
npx eas-cli login                                   # una vez
./scripts/build-apk.sh https://api.midominio.com    # APK con esa URL del backend
```
