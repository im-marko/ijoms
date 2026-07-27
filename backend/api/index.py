import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ijoms.wsgi import application

app = application
