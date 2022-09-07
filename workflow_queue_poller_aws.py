import json
import logging

import workflow_event_handler_aws
from services.config.config_manager import ConfigManager
from services.config.env_util import EnvUtil
from services.queue.aws_sqs_queue_manager import AwsSqsQueueManager
from services.signal.signal_handler import SignalHandler

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    signal_handler = SignalHandler()
    while not signal_handler.received_signal:
        env = EnvUtil().get_env()

        config_manager = ConfigManager(environment=env)
        workflow_queue_name = config_manager.get_config("workflow_queue_name")
        region_name = config_manager.get_config("region_name")
        profile_name = config_manager.get_config("profile_name")

        sqs_manager = AwsSqsQueueManager(
            profile_name=profile_name,
            region=region_name
        )

        while not signal_handler.received_signal:
            logger.info("poll for sqs messages from queue: {}".format(workflow_queue_name))
            messages = sqs_manager.receive_messages(queue_name=workflow_queue_name, max_no_of_messages=10)

            if messages is None or len(messages) <= 0:
                continue

            message_records = []
            for message in messages:
                logger.info("{} {} {}".format(str(message.body), str(message.__dict__), message.receipt_handle))
                logger.info("messages: {}".format(json.dumps(message.body, sort_keys=True, indent=4)))

                message_records.append({"body": json.loads(message.body)})
                sqs_manager.delete_message(queue_name=workflow_queue_name, message=message)

            event = dict(Records=message_records)

            workflow_event_handler_aws.process_messages(event)
