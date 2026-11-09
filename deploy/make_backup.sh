#!/usr/bin/env bash
# Creates deploy/prod.sqlite3: a consistent copy of the local SQLite database.
# Uses SQLite's online backup API, so it is safe even while the app is running.
#   ./deploy/make_backup.sh [source.sqlite3]     (default: db.sqlite3)
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="${1:-db.sqlite3}"
DEST="deploy/prod.sqlite3"
[ -f "$SRC" ] || { echo "No existe $SRC" >&2; exit 1; }

python3 - "$SRC" "$DEST" <<'PY'
import os, sqlite3, sys
src, dest = sys.argv[1], sys.argv[2]
if os.path.exists(dest):
    os.remove(dest)
a = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
b = sqlite3.connect(dest)
a.backup(b)
b.execute("PRAGMA journal_mode=DELETE")   # one self-contained file, no -wal/-shm companions
result = b.execute("PRAGMA integrity_check").fetchone()[0]
tables = b.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
b.close(); a.close()
if result != "ok":
    sys.exit(f"integrity_check failed: {result}")
print(f"OK: {dest} ({os.path.getsize(dest)} bytes, {tables} tablas, integrity_check=ok)")
PY
chmod 600 "$DEST"
echo "Contiene usuarios (hashes de contraseña) y nombres de personas: no lo subas a un repositorio público."
