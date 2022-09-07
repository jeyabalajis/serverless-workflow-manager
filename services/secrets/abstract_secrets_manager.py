from abc import ABC


class SecretsManager(ABC):
    def __init__(self, *, profile_name: str = None, region: str = "ap-south-1"):
        self.profile_name = profile_name
        self.region = region

    def get_secret(self, *, secret_name: str):
        """
        abstract method
        :param secret_name:
        :return:
        """
        pass
