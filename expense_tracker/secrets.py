import os
from dotenv import load_dotenv


load_dotenv()

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
