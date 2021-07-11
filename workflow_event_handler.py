import logging

from entity.start_workflow_event import StartWorkflowEvent
from entity.task import Task
from entity.task_event import TaskEvent
from services.events.event_util import EventManager
from services.workflow.workflow_manager import WorkflowManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def process_messages(event, context=None):
    """
    process_messages is invoked by a serverless component based on an event.
    Here we have handled SQS events triggering this function.
    Based on the type of event, this function either starts a workflow or updates a task.
    :param event:
    :param context:
    :return:
    """

    event_manager = EventManager(event_dict=event, event_type=EventManager.SQS_EVENT_TYPE)

    events = event_manager.get_events()

    if events is None:
        logger.info("no event is sent")

    for event in events:
        if isinstance(event, StartWorkflowEvent):
            WorkflowManager(event=event).start_workflow()

        if isinstance(event, TaskEvent):
            if event.task.status == Task.COMPLETED_STATUS:
                WorkflowManager(event=event).mark_task_as_completed()

            if event.task.status == Task.PENDING_STATUS:
                WorkflowManager(event=event).mark_task_as_pending()

            if event.task.status == Task.FAILED_STATUS:
                WorkflowManager(event=event).mark_task_as_failed()
