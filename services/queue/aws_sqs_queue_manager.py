import json
import logging
import os
from typing import Dict

import boto3

from services.config.config_manager import ConfigManager
from services.config.env_util import EnvUtil
from services.queue.abstract_queue_manager import QueueManager
from services.boto.boto_service import BotoService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AwsSqsQueueManager(QueueManager):
    SERVICE_NAME = 'sqs'

    def __init__(self, *, profile_name: str, region: str):
        super().__init__(
            profile_name=profile_name,
            region=region
        )
        self.boto_sqs_client = BotoService(
            profile_name=profile_name,
            region_name=region,
            service_name=BotoService.SQS_SERVICE_NAME
        ).get_client()

    def send_message(self, *, queue_name: str, message_body: Dict) -> str:
        super(AwsSqsQueueManager, self).send_message(queue_name=message_body)
        queue_client = self.boto_sqs_client.get_queue_by_name(QueueName=queue_name)
        message_body = json.dumps(message_body, indent=4, sort_keys=True, default=str)
        response = queue_client.send_message(MessageBody=message_body)
        if response and isinstance(response, Dict):
            return response.get("MessageId")

    def receive_messages(self, *, queue_name: str, max_no_of_messages: int = 1, wait_time_seconds: int = 10):
        """

        :param queue_name:
        :param max_no_of_messages: 1. Use this parameter to batch receipt of messages.
        :param wait_time_seconds: 10. Use this parameter to implement long polling
        :return:
        """
        super(AwsSqsQueueManager, self).receive_messages(
            max_no_of_messages=max_no_of_messages,
            wait_time_seconds=wait_time_seconds
        )
        queue_client = self.boto_sqs_client.get_queue_by_name(QueueName=queue_name)
        return queue_client.receive_messages(
            MaxNumberOfMessages=max_no_of_messages,
            WaitTimeSeconds=wait_time_seconds
        )

    def delete_message(self, *, queue_name: str, message):
        queue_client = self.boto_sqs_client.get_queue_by_name(QueueName=queue_name)
        queue_client.delete_message(message)

