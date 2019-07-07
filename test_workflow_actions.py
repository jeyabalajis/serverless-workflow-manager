import json
import logging
import os
import uuid

from config.config import load_config
from workflow_event_handler import process_messages, get_workflow_instance

__logger = logging.getLogger(__name__)

__logger.info("Loading environment........")
env_name = os.environ.get('env')

if not env_name:
    env_name = 'sandbox'

load_config(env_name)


def __get_event(body):
    """

    :param body:
    :return:
    """
    _body_str = json.dumps(body)

    # Call Workflow Manager with StarWorkflow event
    _event = {
        "Records": [
            {
                "body": _body_str
            }
        ]
    }

    return _event


def test_workflow_scheduling():
    """
    Inject the following event messages and validate the workflow instance state
    1) Start Pizza delivery workflow and validate workflow instance state
    2) Mark tasks as completed and validate workflow instance state
    :return:
    """

    # Generate a unique reference number to act as a business reference number
    _business_ref_no = str(uuid.uuid4())

    _body = {
        "event_name": "StartWorkflow",
        "business_ref_no": _business_ref_no,
        "component_name": "ITALIAN"
    }
    _event = __get_event(_body)

    process_messages(_event, None)
    _workflow_instance = get_workflow_instance(_business_ref_no)

    # Assert whether the workflow has been initiated and START stage is completed
    assert (
            _workflow_instance
            and "stages" in _workflow_instance
            and type(_workflow_instance["stages"]).__name__ == 'list'
            and _workflow_instance["stages"][0]["status"] == "COMPLETED"
    )

    # Mark the first confirm_order as COMPLETED
    # and validate that the PREPARE stage is activated
    _body = {
        "business_ref_no": _business_ref_no,
        "component_name": "ITALIAN",
        "event_name": "TaskCompleted",
        "stage_name": "ORDER",
        "task_name": "confirm_order",
        "task_type": "SERVICE"
    }
    _event = __get_event(_body)

    process_messages(_event, None)
    _workflow_instance = get_workflow_instance(_business_ref_no)

    # Assert whether the ORDER stage is COMPLETED and PREPARE stage is ACTIVE now
    assert (
            _workflow_instance
            and "stages" in _workflow_instance
            and _workflow_instance["stages"][1]["status"] == "COMPLETED"
            and _workflow_instance["stages"][2]["status"] == "ACTIVE"
    )
