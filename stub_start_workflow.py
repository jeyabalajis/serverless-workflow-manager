import workflow_event_handler_aws
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ['env'] = "sandbox"
env_name = os.environ.get('env')
logger.info("env name: {}".format(env_name))

if __name__ == '__main__':
    with open("./samples/sample_sqs_message.json") as sample_sqs_message:
        event_dict = json.load(sample_sqs_message)
        assert event_dict is not None

        workflow_event_handler_aws.process_messages(event_dict)
