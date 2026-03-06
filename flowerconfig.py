from dotenv import dotenv_values
from websockets.sync.server import basic_auth

config = dotenv_values(".env")

# flower config
port = 5555
max_tasks = 10000
auto_refresh = True
# db = 'flower.db'  # SQLlite database for persistent storage

# Authentication
basic_auth = [f'admin:{config["CELERY_FLOWER_PASSWORD"]}']
