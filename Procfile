web: gunicorn UsingDataWizAPI.wsgi
web: python UsingDataWizAPI/manage.py collectstatic --noinput; bin/gunicorn_django --workers=4 --bind=0.0.0.0:$PORT UsingDataWizAPI/settings.py