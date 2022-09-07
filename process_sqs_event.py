from __future__ import print_function
from typing import Dict
from workflow_event_handler_aws import process_messages


def lambda_handler(event, context):
    if event and isinstance(event, Dict) and 'Records' in event:
        # Print event_record body
        for record in event['Records']:
            payload = record["body"]
            print(str(payload))

    process_messages(event)
