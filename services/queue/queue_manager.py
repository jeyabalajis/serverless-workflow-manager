import json
import logging
import os
from typing import Dict

import boto3

from services.config.config_manager import ConfigManager
from services.config.env_util import EnvUtil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueueManager:
    SERVICE_NAME = 'sqs'

    def __init__(self, *, queue_name: str):
        env = EnvUtil().get_env()
        config_manager = ConfigManager(environment=env)

        region_name = config_manager.get_config("region_name")
        profile_name = config_manager.get_config("profile_name")

        logger.info("env {} region: {} profile: {}".format(env, region_name, profile_name))

        # Create a SQS client. For local executions, use a specific named aws configuration profile
        # When executed through Lambda, use default profile
        if 'FRAMEWORK' in os.environ and os.environ['FRAMEWORK'] in ('Zappa', 'CircleCi'):
            session = boto3.session.Session()
        else:
            session = boto3.session.Session(profile_name=profile_name)

        self.queue_name = queue_name
        self.sqs_session = session.resource(service_name=self.SERVICE_NAME, region_name=region_name)
        self.queue = self.sqs_session.get_queue_by_name(QueueName=queue_name)

    def send_message(self, message_body: Dict) -> str:

        message_body = json.dumps(message_body, indent=4, sort_keys=True, default=str)
        response = self.queue.send_message(MessageBody=message_body)
        if response and isinstance(response, Dict):
            return response.get("MessageId")

    def receive_messages(self, max_no_of_messages: int = 1, wait_time_seconds: int = 10):

        return self.queue.receive_messages(
            MaxNumberOfMessages=max_no_of_messages,
            WaitTimeSeconds=wait_time_seconds
        )

    @classmethod
    def delete_message(cls, message):
        message.delete()
