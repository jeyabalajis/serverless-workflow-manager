from pymongo import MongoClient


class DatabaseCache:
    db_cache = {}

    @classmethod
    def set_db_cache(cls, *, db_name: str, db_connection: MongoClient):
        cls.db_cache[db_name] = db_connection

    @classmethod
    def get_db_cache(cls, *, db_name: str):
        if db_name in cls.db_cache:
            return cls.db_cache[db_name]
        return None
