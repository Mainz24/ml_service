import os
from dotenv import load_dotenv

load_dotenv()

db_password = os.getenv("DB_PASSWORD")
rabbitmq_host = os.getenv("RABBITMQ_HOST")
