import os
from ap_vercel_django import vercel_app

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")  # adjust if your settings module is different

app = vercel_app()