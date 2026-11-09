# AsignacionesApp (backend) — project memory

Django 5.1 + DRF + SQLite, run with Docker. Serves the Expo app in `../asignacionesMobileApp`
(that repo has its own CLAUDE.md). Notes written from the working session of Nov 2026; the UI/API language is Spanish.

## Run / test
- Dev: `docker compose up -d` → `runserver` on :8000, code bind-mounted (`.:/code`), `.env` (gitignored) sets `SQL_FILE=db.sqlite3` and `SECRET_KEY`. **Rebuild the image (`docker compose up -d --build`) when `requirements.txt` changes** (whitenoise was added; the settings now import it).
- Real data lives in `db.sqlite3` (tracked in git). `central.sqlite3` is empty. Switch DB with `SQL_FILE`.
- **Try risky changes on a copy**, never the real DB:
  `docker compose run --rm -T web sh -c 'cp db.sqlite3 /tmp/t.sqlite3 && SQL_FILE=../tmp/t.sqlite3 python manage.py shell'`
  (pipe a script to stdin; `migrate -v0` first if the schema changed). Take a backup before touching the real DB.
- Migrations: `docker compose run --rm -T web python manage.py makemigrations <app>` then `migrate`. Applied so far: asignaciones 0010–0013, programa_privilegios 0001–0002, vymc 0001–0002.
- No Python tooling on the host (no pip, no openpyxl). For one-off scripts install into a temp dir through the container: `pip install --target /scratch/pylib …` and mount a scratch folder.

## Apps
- `asignaciones`: `Person` (name, gender M/F, `rol` publicador|siervo_ministerial|anciano, `permisos` JSON list, `user` OneToOne→auth User, visible…), `AsignationType`, `Asignation` (person, helper, number 3–7, date, room 1/2, attended, notes, `tiempo` = real duration in **seconds**, `tiempo_display` m:ss).
- `programa_privilegios`: `ProgramaPrivilegio`, one row per meeting day (**Thursday or Saturday only**, unique date) with 10 FKs to Person: oracion_inicio, oracion_final, entrada, auditorio, microfono1, microfono2, plataforma, audio, presidente, lector.
- `vymc` (Vida y Ministerio Cristiano): `SemanaVyMC` (`fecha_inicio` = a **Monday**, end = +6 days, label "Semana 9 – 15 de noviembre" is generated; lectura_semanal, presidente, consejero, 3 songs, conductor_estudio, tiempo_estudio) and `ParteVyMC` (numero, seccion tesoros|maestros|vida, titulo, minutos, `asignada`, persona, `tiempo`).
- `api`: all DRF serializers/views/urls (single module each). `men` is legacy.

## Business rules (enforced in model `clean()`/forms, not by the DB — ORM imports bypass them)
- Permission values: `lectura_libro, oracion, acomodador, lectura_atalaya, entrada_y_auditorio, audio, presidente`.
- Privilegio → required permission: oraciones→oracion; entrada/auditorio→entrada_y_auditorio; micrófonos/plataforma→acomodador; audio→audio; presidente→presidente **and** rol siervo_ministerial/anciano; lector→lectura_libro on Thursday, lectura_atalaya on Saturday. Only male, visible people.
- VyMC presidente/consejero/part persona/conductor: male, visible, rol siervo_ministerial or anciano (rol only, no permission check).
- **All "Seamos mejores maestros" parts (and part 3, Lectura de la Biblia) are `asignada=True`: participants come from `Asignation`**, matched by part number and an `asignation_date` inside the Mon–Sun week; room 1 = main, room 2 = auxiliar. Parts 1, 2, 7 and the study conductor are set directly in VyMC. Oraciones and lector come from the **Thursday** privilegios row of that week.
- One user ↔ one Person (OneToOne; admin shows "Este usuario ya está vinculado a otra persona.").
- SQLite has no JSONField `contains`: eligibility is filtered in Python (`eligible_ids`). `limit_choices_to` callables must be `@deconstructible` classes (a lambda breaks `makemigrations`).

## API (JWT, everything needs a token)
`POST /api/auth/token/` and `/api/auth/token/refresh/` (simplejwt, access 30 min, refresh 7 days; default permission IsAuthenticated; CORS open).
Read-only: `GET /api/programa-privilegios/?month=&year=`, `GET /api/vymc/?month=&year=` (weeks that touch the month; full program incl. parts with `tiempo`, `estudio_biblico`, `acomodadores` — **Saturday rows are excluded on purpose**), `GET /api/mis-partes/` (privilegios + VyMC parts + asignaciones of the logged-in user's Person, today → +3 months, grouped by day; `person: null` if the user has no Person).
Writable: persons, asignation-types, asignations, `asignations-edit`, and `POST /api/vymc/{id}/tiempo/` body `{numero, tiempo}` (stores seconds on the part, or on the week for the study = last number + 1).

## Data loaded (Nov 2026)
- From `LectoresAcomodadores…xlsx` (sheets Datos, Permisos): 31 men's permissions, 15 people created, privilegios Nov 7 → Jan 2 2027, 8 VyMC weeks (Nov 9 → Dec 28) with presidente, parts 1/2/7 people and conductor; titles/minutes of parts 4–6, lectura semanal, part-1 titles and songs from the user's paste and `mwb_S_202611.pdf`.
- **Provisional:** the 8 people with the Presidente permission were set to `siervo_ministerial` — the sheet does not say who is anciano. Parts 1 and 7 titles are partly blank; parts 4–6 have no assignees because no Asignaciones exist yet for Nov–Dec.
- 7 privilegios in the Excel break its own permission rules (4 lectores without Lectura Libro; Jonathan Centeno only has Audio but appears in Entrada/Auditorio; Dec 24 he is also in Audio). They were loaded as-is.
- The admin's custom view `asignations/` is broken from before (template `admin/asignation_list.html` is looked up but the file is `asignaciones/templates/asignation_list.html`).

## Deploy (`deploy/`)
- `deploy/make_backup.sh` → `deploy/prod.sqlite3` (SQLite online backup; contains user hashes and personal data, gitignored).
- `deploy/deploy.sh` (run on the server): installs Docker if missing, creates a prod `.env`, restores the backup to `data/prod.sqlite3`, builds, `docker compose -f docker-compose.prod.yml up -d` (migrate + collectstatic + gunicorn, whitenoise), health-checks. Options `--host --origin --port --force --no-restore --db`. Verified locally on a throwaway copy. `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SECRET_KEY` come from env; prod compose forces `DEBUG=0`.
- **uv alternative (no Docker):** `pyproject.toml` + `uv.lock` (29 packages, Python ≥3.12; `requirements.txt` still feeds the Dockerfile — keep both in sync) and `deploy/deploy-uv.sh` (apt libs for WeasyPrint/poppler, uv, `uv sync --frozen --no-dev`, restore DB, migrate, collectstatic, systemd unit `asignaciones` with gunicorn on 127.0.0.1:8000). Tested in a clean `debian:bookworm-slim` container with `--no-service`; the systemd part is untested. nginx config: `deploy/nginx-central.admincong.online.conf`.
- **One-off data fixes are management commands** (they ship with the app and need no loose file): `python manage.py titulos_vida_cristiana [--dry-run]` sets the part-7 titles for Nov 2026 → Jan 2027; it requires `SQL_FILE` so the target DB is explicit. In prod: `SQL_FILE=data/prod.sqlite3 uv run --no-sync --env-file .env python manage.py titulos_vida_cristiana --dry-run`.
- Not done: HTTPS (put Caddy/nginx in front), phone access over the LAN from WSL2 (needs a Windows portproxy + firewall rule; the WSL IP changes after reboot).

## Working preferences
- Reply in the user's language (Spanish or English). Keep changes minimal and scoped; say clearly what was **not** verified (nothing mobile was run on a device — the user sends screenshots).
- Don't print the `SECRET_KEY`. Real-data imports: dry-run on a DB copy, back up, then apply; report anomalies in the user's data instead of silently fixing them.
