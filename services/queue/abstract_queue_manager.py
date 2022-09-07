from abc import ABC
from typing import Dict


class QueueManager(ABC):
    def __init__(self, *, profile_name: str, region: str):
        self.profile_name = profile_name
        self.region_name = region

    def send_message(self, *, queue_name: str, message_body: Dict) -> str:
        """
        abstract method
        :param queue_name:
        :param message_body:
        :return:
        """
        pass

    def receive_messages(self, *, queue_name: str, max_no_of_messages: int = 1, wait_time_seconds: int = 10):
        """
        abstract method
        :param queue_name:
        :param max_no_of_messages:
        :param wait_time_seconds:
        :return:
        """
        pass



