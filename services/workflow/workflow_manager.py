from typing import Union

from database.workflow_definition_repository import WorkflowDefinitionRepository
from database.workflow_instance_repository import WorkflowInstanceRepository
from entity.event import Event
from entity.task_event import TaskEvent
from entity.workflow import Workflow
from services.queue.queue_manager import QueueManager


class WorkflowManager:
    def __init__(self, *, event: Union[Event, TaskEvent]):
        self.event = event

    def start_workflow(self):
        """
        start_workflow performs the following:
        1. find a workflow template based on the component name sent in the event.
        2. Create a workflow instance based on the template
        3. Find and schedule tasks
        :return:
        """
        workflow: Workflow = WorkflowDefinitionRepository.find_one_by_component_name(
            component_name=self.event.component_name
        )

        workflow.set_business_ref_no(business_ref_no=self.event.business_ref_no)
        WorkflowInstanceRepository.upsert(workflow=workflow)

        self.__find_and_schedule_tasks(workflow=workflow)

    def mark_task_as_completed(self):
        workflow: Workflow = WorkflowInstanceRepository.find_one_by_business_ref_no(
            business_ref_no=self.event.business_ref_no)

        current_stage = workflow.get_stage_by_name(stage_name=self.event.stage_name)
        assert current_stage is not None

        current_task = workflow.get_task_by_name(stage=current_stage, task_name=self.event.task.task_name)
        assert current_task is not None

        workflow.mark_task_as_completed(stage=current_stage, task=current_task)
        self.__find_and_schedule_tasks(workflow=workflow)

    def mark_task_as_pending(self):
        workflow: Workflow = WorkflowInstanceRepository.find_one_by_business_ref_no(
            business_ref_no=self.event.business_ref_no)

        current_stage = workflow.get_stage_by_name(stage_name=self.event.stage_name)
        assert current_stage is not None

        current_task = workflow.get_task_by_name(stage=current_stage, task_name=self.event.task.task_name)
        assert current_task is not None

        workflow.mark_task_as_pending(stage=current_stage, task=current_task)
        self.__find_and_schedule_tasks(workflow=workflow)

    def mark_task_as_failed(self):
        workflow: Workflow = WorkflowInstanceRepository.find_one_by_business_ref_no(
            business_ref_no=self.event.business_ref_no)

        current_stage = workflow.get_stage_by_name(stage_name=self.event.stage_name)
        assert current_stage is not None

        current_task = workflow.get_task_by_name(stage=current_stage, task_name=self.event.task.task_name)
        assert current_task is not None

        workflow.mark_task_as_failed(stage=current_stage, task=current_task)
        self.__find_and_schedule_tasks(workflow=workflow)

    def __find_and_schedule_tasks(self, *, workflow: Workflow):
        workflow.find_and_schedule_tasks()

        WorkflowInstanceRepository.upsert(workflow=workflow)

        self.__schedule_tasks_to_queue(workflow=workflow)

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

            QueueManager(queue_name=task.task_queue).send_message(task_event.get_dict())
