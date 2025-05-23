import os

# utilizamos el arreglo os.environ para obtener las variables de entorno, que vendrian de la capa
# superior: docker-compose, kubernetes, etc.

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "default_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "default_password")
DB_NAME = os.environ.get("DB_DATABASE", "default_db")

SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("SERVER_PORT", 8000))

# paginacion

DEFAULT_PAGE_NUMBER = 1
DEFAULT_PAGE_SIZE = 10

DEFAULT_YEAR_FILTER = 2019
