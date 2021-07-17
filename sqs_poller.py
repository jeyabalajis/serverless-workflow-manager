import logging

from services.config.config_manager import ConfigManager
from services.config.env_util import EnvUtil
from services.queue.queue_manager import QueueManager
from services.signal.signal_handler import SignalHandler
from workflow_event_handler import process_messages
from typing import List
import json

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    signal_handler = SignalHandler()
    while not signal_handler.received_signal:
        env = EnvUtil().get_env()

        config_manager = ConfigManager(environment=env)
        workflow_queue_name = config_manager.get_config("workflow_queue_name")

        sqs_manager = QueueManager(queue_name=workflow_queue_name)

        while not signal_handler.received_signal:
            logger.info("poll for sqs messages from queue: {}".format(workflow_queue_name))
            messages = sqs_manager.receive_messages()

            if messages is not None and isinstance(messages, List) and len(messages) > 0:
                message_records = []
                for message in messages:
                    logger.info("{} {} {}".format(str(message.body), str(message.__dict__), message.receipt_handle))
                    logger.info("messages: {}".format(json.dumps(message.body, sort_keys=True, indent=4)))
                    QueueManager.delete_message(message)
                    message_records.append({"body": json.loads(message.body)})

                event = {
                    "Records": message_records
                }

                process_messages(event)
