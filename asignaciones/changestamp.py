"""Marca de "último cambio": un archivo de texto con un timestamp ISO (UTC).

Se reescribe cada vez que cambia algo que muestra la app (privilegios, VyMC, asignaciones, personas);
la app lo consulta cada minuto por `GET /api/ultimo-cambio/` y solo recarga los datos si cambió.
Sin Redis ni base de datos: un archivo junto a la base (`data/last_change.txt` en producción), o el
que indique la variable de entorno LAST_CHANGE_FILE.
"""
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings

log = logging.getLogger(__name__)


def stamp_path() -> Path:
    custom = os.getenv('LAST_CHANGE_FILE')
    if custom:
        return Path(custom)
    return Path(settings.DATABASES['default']['NAME']).parent / 'last_change.txt'


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def touch() -> None:
    """Escribe el timestamp actual (de forma atómica). Un fallo al escribir nunca debe romper un guardado."""
    path = stamp_path()
    try:
        tmp = path.with_name(path.name + '.tmp')
        tmp.write_text(_now() + '\n')
        os.replace(tmp, path)
    except OSError:
        log.warning('No se pudo escribir %s', path, exc_info=True)


def read() -> str:
    """Timestamp actual; si el archivo no existe todavía lo crea (así hay una referencia estable)."""
    path = stamp_path()
    try:
        return path.read_text().strip()
    except FileNotFoundError:
        touch()
        try:
            return path.read_text().strip()
        except OSError:
            return ''
    except OSError:
        log.warning('No se pudo leer %s', path, exc_info=True)
        return ''
