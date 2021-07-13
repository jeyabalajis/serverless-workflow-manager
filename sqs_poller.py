import logging

from services.config.config_manager import ConfigManager
from services.config.env_util import EnvUtil
from services.queue.queue_manager import QueueManager
from services.signal.signal_handler import SignalHandler
from workflow_event_handler import process_messages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if __name__ == '__main__':
    signal_handler = SignalHandler()
    while not signal_handler.received_signal:
        env = EnvUtil().get_env()

        config_manager = ConfigManager(environment=env)
        workflow_queue_name = config_manager.get_config("workflow_queue_name")

        sqs_manager = QueueManager(queue_name=workflow_queue_name)

        while not signal_handler.received_signal:
            logger.info("poll for sqs messages")
            messages = sqs_manager.receive_message()
            process_messages(messages)
