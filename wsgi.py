from asgi2wsgi import ASGI2WSGI
from api import app  # Ensure that your FastAPI app is defined in api.py as 'app'

# This variable 'application' is what PythonAnywhere will use as the WSGI application.
application = ASGI2WSGI(app)
