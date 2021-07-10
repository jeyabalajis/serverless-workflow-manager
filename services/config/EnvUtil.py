import os
from services.config.ConfigManager import ConfigManager

class EnvUtil:
    def __init__(self):
        """
        singleton class
        """
        pass

    @classmethod
    def get_env(cls):
        env_name = os.environ.get('env')

        if not env_name:
            env_name = 'prod'

        return env_name

    @classmethod
    def get_aws_profile_name(cls):
        """ return either None or local aws profile name based on environment variables. """
        if 'FRAMEWORK' in os.environ and os.environ['FRAMEWORK'] == 'Zappa':
            return None

        if 'FRAMEWORK' in os.environ and os.environ['FRAMEWORK'] == 'CircleCi':
            return None

        return ConfigManager(cls.get_env()).get_config("profile_name")
