from typing import Dict, List, Union

from entity.stage import Stage
from entity.task import Task
from exceptions.workflow_type_error import WorkflowTypeError
from exceptions.workflow_value_error import WorkflowValueError
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Workflow:
    def __init__(self, *, workflow_name: str, component_name: str, stages: [Stage], **kwargs):
        self.workflow_name = workflow_name
        self.component_name = component_name
        self.stages = stages
        self.__validate_stages_type()
        self.business_ref_no = None

        for key, val in kwargs.items():
            setattr(self, key, val)

    @classmethod
    def from_json(cls, workflow_json: Dict):
        if "stages" not in workflow_json:
            raise WorkflowValueError("stages node is mandatory")

        if not isinstance(workflow_json["stages"], List):
            raise WorkflowTypeError("stages node must be a List")

        stages = [Stage.from_json(stage_json=stage_json) for stage_json in workflow_json["stages"]]

        return Workflow(
            workflow_name=workflow_json["workflow_name"],
            component_name=workflow_json["component_name"],
            stages=stages
        )

    @classmethod
    def from_json_template(cls, workflow_json_template: Dict):
        workflow: Workflow = cls.from_json(workflow_json_template)

        for (ind, stage) in enumerate(workflow.stages):
            if ind == 0:
                stage.status = Stage.ACTIVE_STATUS
            else:
                stage.status = Stage.NOT_STARTED_STATUS

            for task in stage.tasks:
                task.status = Task.PENDING_STATUS

        return workflow

    def set_business_ref_no(self, *, business_ref_no: str):
        self.business_ref_no = business_ref_no

    def get_dict(self):
        return json.loads(json.dumps(self, default=lambda o: o.__dict__))

    def __validate_stages_type(self):
        for stage in self.stages:
            if not isinstance(stage, Stage):
                raise WorkflowTypeError("all elements of stages must be of type Stage")

    def all_dependencies_completed_for_a_task(self, *, stage: Stage, task: Task) -> bool:
        if not task.parent_task:
            return True

        all_parents_completed = True
        for parent_task in task.parent_task:
            parent_task_record = self.get_task_by_name(stage=stage, task_name=parent_task)
            all_parents_completed = all_parents_completed and (parent_task_record.status == Task.COMPLETED_STATUS)

        return all_parents_completed

    def get_stage_by_name(self, *, stage_name: str) -> [Stage, None]:
        for stage in self.stages:
            if stage.stage_name == stage_name:
                return stage
        return None

    def get_stage_by_order(self, *, stage_order: int) -> [Stage, None]:
        for stage in self.stages:
            if stage.stage_order == stage_order:
                return stage
        return None

    def get_active_stage(self) -> Stage:
        for stage in self.stages:
            if stage.status == Stage.ACTIVE_STATUS:
                return stage

    def get_task_by_name(self, *, stage: Stage, task_name: str) -> Union[Task, None]:
        for workflow_stage in self.stages:
            if not workflow_stage.stage_name == stage.stage_name:
                continue

            for workflow_task in workflow_stage.tasks:
                if not workflow_task.task_name == task_name:
                    continue
                return workflow_task
        return None

    def mark_stage_as_completed(self, *, stage: Stage):
        """
        Mark the stage passed in as COMPLETED and ACTIVATE the next stage (if any)
        :param stage:
        :return:
        """
        for workflow_stage in self.stages:
            if workflow_stage.stage_name == stage.stage_name:
                workflow_stage.status = Stage.COMPLETED_STATUS

                next_stage = self.get_stage_by_order(stage_order=workflow_stage.stage_order + 1)
                if next_stage is not None:
                    next_stage.status = Stage.ACTIVE_STATUS

    def mark_task_as_completed(self, *, stage: Stage, task: Task):
        self.__update_task(stage=stage, task=task, status=Task.COMPLETED_STATUS)

    def mark_task_as_pending(self, *, stage: Stage, task: Task):
        self.__update_task(stage=stage, task=task, status=Task.PENDING_STATUS)

    def mark_task_as_failed(self, *, stage: Stage, task: Task):
        self.__update_task(stage=stage, task=task, status=Task.PENDING_STATUS)

    def mark_task_as_scheduled(self, *, stage: Stage, task: Task):
        self.__update_task(stage=stage, task=task, status=Task.SCHEDULED_STATUS)

    def __update_task(self, *, stage: Stage, task: Task, status: str):
        for workflow_stage in self.stages:
            if workflow_stage.stage_name == stage.stage_name:
                for workflow_task in workflow_stage.tasks:
                    if workflow_task.task_name == task.task_name:
                        workflow_task.status = status

    def schedule_pending_tasks_for_stage(self, *, stage: Stage, pending_tasks: [Task]):
        for pending_task in pending_tasks:
            if self.all_dependencies_completed_for_a_task(stage=stage, task=pending_task):
                self.mark_task_as_scheduled(stage=stage, task=pending_task)

    def find_and_schedule_tasks(self):
        """

        :return:
        The workflow instance is organized as a set of stages & a set of tasks inside each stage.
        At any point in time, only one stage is ACTIVE.
        Logic:
        For the instance, get the current active stage.
        if active stage is found
            [1] get pending tasks & schedule them, provided their dependencies are completed
            if no pending tasks, mark current stage as closed, get the next active stage & repeat [1]
            if no active stage, just close the workflow and return
        if active stage is not found
            this is an instance with no active stage, just close the workflow and return

        Please note that the workflow manager DOES NOT WAIT or SLEEP. It reacts based on events.
        Upon StartWorkflow message_body, the tasks eligible to be scheduled are scheduled.
        When these tasks are marked completed (TaskCompleted), the next set of eligible tasks on the task are scheduled
        When there are no more tasks to schedule in a stage, the next stage is activated & the process repeated.

        """

        find_tasks = True
        while find_tasks:
            active_stage = self.get_active_stage()

            # If no active stages are found, the whole workflow is done
            if active_stage is None:
                find_tasks = False
                continue

            # Get pending tasks for the active stage
            pending_tasks = active_stage.get_pending_tasks()

            if pending_tasks:
                self.schedule_pending_tasks_for_stage(stage=active_stage, pending_tasks=pending_tasks)
                find_tasks = False
            else:
                # If all tasks are completed, mark stage as completed and go to the next stage
                if active_stage.all_tasks_completed():
                    self.mark_stage_as_completed(stage=active_stage)
                else:
                    # Tasks are SCHEDULED and yet to be done.
                    find_tasks = False

        print("done scheduling")
