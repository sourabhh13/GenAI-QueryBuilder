import os
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Database credentials
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "test_db")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")

# Connection String
DATABASE_URL = (
    f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)

# Create SQLAlchemy engine
try:
    logging.debug(f"Connecting to MySQL at {MYSQL_HOST}:{MYSQL_PORT}")
    engine = create_engine(DATABASE_URL, echo=True)
    logging.debug("Database connection successful")
except Exception as e:
    logging.error(f"Database connection failed: {str(e)}")
    exit()


    # Function to list tables in a specific database
def list_tables(database_name):
    """Return a list of all tables in the given database."""
    try:
        with engine.connect() as connection:
            connection.execute(text(f"USE `{database_name}`;"))
            result = connection.execute(text("SHOW TABLES;")).fetchall()
            return {"tables": [row[0] for row in result]}
    except Exception as e:
        return {"error": str(e)}


# Function to list databases
def list_databases():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SHOW DATABASES;")).fetchall()
            return {"databases": [row[0] for row in result]}
    except Exception as e:
        return {"error": str(e)}

# Function to list columns
def list_columns(database_name, table_name):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(f"SHOW COLUMNS FROM `{database_name}`.`{table_name}`;")
            ).fetchall()
            return {"columns": [row[0] for row in result]}
    except Exception as e:
        return {"error": str(e)}
