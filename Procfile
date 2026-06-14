web: python manage.py migrate --noinput && python manage.py setup_initial_data && gunicorn income_tax_project.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
