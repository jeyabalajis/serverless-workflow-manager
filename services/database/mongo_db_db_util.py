import json
import logging

from pymongo import MongoClient

from services.config.config_manager import ConfigManager
from services.config.env_util import EnvUtil
from services.database.db_cache import DatabaseCache
from services.secrets.aws_secrets_manager import AwsSecretsManager
from services.database.db_secret import DatabaseSecret
from services.database.abstract_db_util import DatabaseUtil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDbDatabaseUtil(DatabaseUtil):
    def __init__(self, *, db_name: str, db_secret: DatabaseSecret):
        super().__init__(db_name=db_name, db_secret=db_secret)

    def get_db_object(self):
        """
        :return: pymongo client object
        """

        db_handle = DatabaseCache.get_db_cache(db_name=self.db_name)

        # Serve from cache, if available        
        if db_handle is not None:
            return db_handle

        db_uri = self.db_secret.db_url + "/" + self.db_name

        logger.info("db_name: {} uri: {}".format(self.db_name, db_uri))

        client = MongoClient(db_uri, username=self.db_secret.user_name, password=self.db_secret.password)
        db = client[self.db_name]

        DatabaseCache.set_db_cache(db_name=self.db_name, db_connection=db)
        return db
