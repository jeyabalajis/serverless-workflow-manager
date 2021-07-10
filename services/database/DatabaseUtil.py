import json
import logging

from pymongo import MongoClient
from pymongo.database import Database

from services.config.ConfigManager import ConfigManager
from services.config.EnvUtil import EnvUtil
from services.database.DatabaseCache import DatabaseCache
from services.secrets.SecretsManager import SecretsManager

__logger = logging.getLogger(__name__)


class DatabaseUtil:
    def __init__(self, *, db_name: str, aws_profile_name: str = None):
        self.db_name = db_name
        self.aws_profile_name = aws_profile_name

    def get_db_object(self) -> Database:
        """
        :return: pymongo client object
        """

        db_handle = DatabaseCache.get_db_cache(db_name=self.db_name)

        # Serve from cache, if available        
        if db_handle is not None:
            return db_handle

        env = EnvUtil().get_env()

        config_manager = ConfigManager(environment=env)
        db_credentials_id = config_manager.get_config("db_credentials_id")

        # Connect to DB and get database handle, if cache not available.        
        secrets_manager: SecretsManager = SecretsManager(aws_profile_name=self.aws_profile_name)
        db_secrets = secrets_manager.get_secret(secret_name=db_credentials_id)
        db_secrets = json.loads(db_secrets)

        db_uri = db_secrets["db_url"] + "/" + self.db_name
        db_username = db_secrets["user_name"]
        db_pwd = db_secrets["password"]

        client = MongoClient(db_uri, username=db_username, password=db_pwd)
        db = client[self.db_name]

        DatabaseCache.set_db_cache(db_name=self.db_name, db_connection=db)
        return db
