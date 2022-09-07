from typing import Union

from services.repository.abstract_workflow_definition_repository import WorkflowDefinitionRepository
from services.repository.abstract_workflow_instance_repository import WorkflowInstanceRepository
from domain.event import Event
from domain.workflow import Workflow
from services.queue.abstract_queue_manager import QueueManager
import logging
from domain.start_workflow_event import StartWorkflowEvent
from domain.task import Task
from domain.task_event import TaskEvent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowManager:
    def __init__(self, *,
                 event: Union[Event, TaskEvent],
                 queue_manager: QueueManager,
                 workflow_definition_repository: WorkflowDefinitionRepository,
                 workflow_instance_repository: WorkflowInstanceRepository
                 ):
        self.event = event
        self.queue_manager = queue_manager
        self.workflow_definition_repository = workflow_definition_repository
        self.workflow_instance_repository = workflow_instance_repository

    def start_workflow(self):
        """
        start_workflow performs the following:
        1. find a workflow template based on the component name sent in the event.
        2. Create a workflow instance based on the template
        3. Find and schedule tasks
        :return:
        """
        workflow: Workflow = self.workflow_definition_repository.find_one_by_component_name(
            component_name=self.event.component_name
        )

        workflow.set_business_ref_no(business_ref_no=self.event.business_ref_no)
        self.workflow_instance_repository.upsert(workflow=workflow)

        self.__find_and_schedule_tasks(workflow=workflow)

    def mark_task_as_completed(self):
        workflow: Workflow = self.workflow_instance_repository.find_one_by_business_ref_no(
            business_ref_no=self.event.business_ref_no)

        current_stage = workflow.get_stage_by_name(stage_name=self.event.stage_name)
        assert current_stage is not None

        current_task = workflow.get_task_by_name(stage=current_stage, task_name=self.event.task.task_name)
        assert current_task is not None

        workflow.mark_task_as_completed(stage=current_stage, task=current_task)
        self.__find_and_schedule_tasks(workflow=workflow)

    def mark_task_as_pending(self):
        workflow: Workflow = self.workflow_instance_repository.find_one_by_business_ref_no(
            business_ref_no=self.event.business_ref_no)

        current_stage = workflow.get_stage_by_name(stage_name=self.event.stage_name)
        assert current_stage is not None

        current_task = workflow.get_task_by_name(stage=current_stage, task_name=self.event.task.task_name)
        assert current_task is not None

        workflow.mark_task_as_pending(stage=current_stage, task=current_task)
        self.__find_and_schedule_tasks(workflow=workflow)

    def mark_task_as_failed(self):
        workflow: Workflow = self.workflow_instance_repository.find_one_by_business_ref_no(
            business_ref_no=self.event.business_ref_no)

        current_stage = workflow.get_stage_by_name(stage_name=self.event.stage_name)
        assert current_stage is not None

        current_task = workflow.get_task_by_name(stage=current_stage, task_name=self.event.task.task_name)
        assert current_task is not None

        workflow.mark_task_as_failed(stage=current_stage, task=current_task)
        self.__find_and_schedule_tasks(workflow=workflow)

    def execute_event(self):
        if isinstance(self.event, StartWorkflowEvent):
            self.start_workflow()

        if isinstance(self.event, TaskEvent):
            if self.event.task.status == Task.COMPLETED_STATUS:
                self.mark_task_as_completed()

            if self.event.task.status == Task.PENDING_STATUS:
                self.mark_task_as_pending()

            if self.event.task.status == Task.FAILED_STATUS:
                self.mark_task_as_failed()

    def __find_and_schedule_tasks(self, *, workflow: Workflow):
        workflow.find_and_schedule_tasks()

        self.__schedule_tasks_to_queue(workflow=workflow)
        self.workflow_instance_repository.upsert(workflow=workflow)

    def __schedule_tasks_to_queue(self, *, workflow: Workflow):
        active_stage = workflow.get_active_stage()
        scheduled_tasks = active_stage.get_scheduled_tasks()
        for task in scheduled_tasks:
            task_event: TaskEvent = TaskEvent(
                business_ref_no=self.event.business_ref_no,
                component_name=self.event.component_name,
                stage_name=active_stage.stage_name,
                task=task
            )

            self.queue_manager.send_message(queue_name=task.task_queue, message_body=task_event.get_dict())
