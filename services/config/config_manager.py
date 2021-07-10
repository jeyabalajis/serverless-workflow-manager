import configparser
import logging

from exceptions.workflow_run_time_error import WorkflowRunTimeError


class ConfigManager:
    def __init__(self, environment: str):
        self.__config = configparser.ConfigParser()
        self.environment = environment
        self.__load_config()

    def __load_config(self):
        """

        :return:
        """
        __logger = logging.getLogger(__name__)
        __logger.info("inside load config")

        try:
            path = "config.ini"

            self.__config.read(path, encoding='utf-8')

        except OSError:
            import traceback
            __logger.error("UNABLE TO READ CONFIGURATION!!!!!!!!!!!!")
            __logger.error(traceback.format_exc())
            raise WorkflowRunTimeError("Unable to read config file. {}".format(traceback.format_exc()))

    def get_config(self, key: str) -> str:
        """

        :param key:
        :return:
        """

        if (
                self.__config.has_section(self.environment)
                and key in self.__config[self.environment]
        ):
            return self.__config[self.environment][key]

        return "unknown"
