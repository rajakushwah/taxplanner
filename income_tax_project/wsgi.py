"""
WSGI config for income_tax_project project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'income_tax_project.settings')

application = get_wsgi_application()
