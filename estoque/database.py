from pathlib import Path
from contextlib import contextmanager
import os
import sqlite3


ROOT_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT_DIR / "banco.sql"
DEFAULT_DB_PATH = ROOT_DIR / "estoque.db"


def get_database_path():
    return Path(os.environ.get("ESTOQUE_DB_PATH", DEFAULT_DB_PATH))


@contextmanager
def connect(database_path=None):
    path = Path(database_path) if database_path is not None else get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize(database_path=None):
    with connect(database_path) as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
