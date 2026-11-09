import datetime as d
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from vymc.models import ParteVyMC, SemanaVyMC

# Thursday of the meeting -> title of part 7 (15 mins.). The study (part 8) has a fixed title in the app.
TITULOS = {
    d.date(2026, 11, 12): 'Nuestras donaciones le dan gloria al gran nombre de Jehová',
    d.date(2026, 11, 19): 'No nos olvidemos de nuestros hermanos inactivos',
    d.date(2026, 11, 26): 'Ayudemos a los cuidadores a no rendirse',
    d.date(2026, 12, 3): 'Necesidades de la congregación',
    d.date(2026, 12, 10): 'Necesidades de la congregación',
    d.date(2026, 12, 17): '¿Por qué no participamos en ceremonias nacionalistas?',
    d.date(2026, 12, 24): 'Imagina cómo acabará la historia',
    d.date(2026, 12, 31): '“Te salvarás a ti mismo y también a los que te escuchan”',
}


class Command(BaseCommand):
    help = (
        'Pone el título y los minutos (15) de la parte 7 de Nuestra vida cristiana en las semanas de '
        'noviembre 2026 a enero 2027. Se puede repetir sin problema. Usa --dry-run para ver los cambios sin guardar. '
        'Requiere SQL_FILE para que quede claro qué base se edita.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Muestra los cambios sin guardar nada.')

    def handle(self, *args, **options):
        if not os.environ.get('SQL_FILE'):
            raise CommandError('Define SQL_FILE con la base a editar, p. ej. SQL_FILE=data/prod.sqlite3')
        dry = options['dry_run']
        self.stdout.write(f"Base de datos: {settings.DATABASES['default']['NAME']}")

        problemas = []
        with transaction.atomic():
            for jueves, titulo in TITULOS.items():
                lunes = jueves - d.timedelta(days=3)
                semana = SemanaVyMC.objects.filter(fecha_inicio=lunes).first()
                parte = ParteVyMC.objects.filter(semana=semana, numero=7).first() if semana else None
                if parte is None:
                    problemas.append(f'{lunes}: no existe la semana o la parte 7 (no se tocó)')
                    continue
                antes = parte.titulo or '(vacío)'
                parte.titulo, parte.minutos = titulo, 15
                parte.save(update_fields=['titulo', 'minutos'])
                self.stdout.write(f'{semana.semana}: {antes!r} -> {titulo!r}')
            if dry:
                transaction.set_rollback(True)

        for p in problemas:
            self.stdout.write(self.style.WARNING(f'AVISO: {p}'))
        if dry:
            self.stdout.write(self.style.WARNING('\n--dry-run: no se guardó nada.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nListo: {len(TITULOS) - len(problemas)} partes actualizadas.'))
