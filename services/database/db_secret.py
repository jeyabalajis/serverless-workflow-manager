import json


class DatabaseSecret:
    def __init__(self, *, db_url: str, user_name: str, password: str):
        self.db_url = db_url
        self.user_name = user_name
        self.password = password

    @classmethod
    def from_dict(cls, *, db_secret_dict: dict):
        return DatabaseSecret(**db_secret_dict)

    @classmethod
    def from_json_string(cls, *, db_secret_json_string: str):
        return cls.from_dict(db_secret_dict=json.loads(db_secret_json_string))
