from abc import ABC
from services.database.db_secret import DatabaseSecret


class DatabaseUtil(ABC):
    def __init__(self, *, db_name: str, db_secret: DatabaseSecret):
        self.db_name = db_name
        self.db_secret = db_secret

    def get_db_object(self):
        """
        abstract method
        :return:
        """
        pass
