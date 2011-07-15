import os, sys
sys.stdout = sys.stderr
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
#sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
os.environ['PYTHON_EGG_CACHE'] = '/tmp/'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()


