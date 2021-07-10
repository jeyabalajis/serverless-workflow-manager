import logging

from entity.StartWorkflowEvent import StartWorkflowEvent
from entity.Task import Task
from entity.TaskEvent import TaskEvent
from services.events.EventUtil import EventManager
from services.workflow.WorkflowManager import WorkflowManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def process_messages(event, context=None):
    """

    :param event:
    :param context:
    :return:
    """

    logger.info("event: {} context: {}".format(str(event), str(context)))

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
