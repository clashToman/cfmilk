from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# SECRET_KEY = os.getenv("SECRET_KEY")
# ALGORITHM = os.getenv("ALGORITHM")
# DATABASE_URL = os.getenv("DATABASE_URL")
load_dotenv()
ADMIN_PHONE = os.getenv("ADMIN_PHONE")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

USERNAME = os.getenv("USERNAME")
HOST = os.getenv("HOST")
DB_NAME = os.getenv("DB_NAME")
PASSWORD = os.getenv("PASSWORD")

DATABASE_URL = f"mysql+mysqlconnector://sql12804224:{PASSWORD}@{HOST}/{DB_NAME}"


engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


try:
    with engine.connect() as connection:
        print("Database Connected Successfully..!")
except Exception as e:
    print("Databadw Unable to connected", e)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
