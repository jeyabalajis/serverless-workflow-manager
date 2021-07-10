from unittest import TestCase
from services.config.ConfigManager import ConfigManager


class TestConfigManager(TestCase):
    def test_get_config(self):
        config_manager = ConfigManager("prod")

        assert config_manager.get_config("profile_name") == "sandbox"
        assert config_manager.get_config("region_name") == "ap-south-1"
