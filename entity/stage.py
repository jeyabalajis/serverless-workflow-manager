from typing import Dict, List

from entity.task import Task
from exceptions.workflow_type_error import WorkflowTypeError
from exceptions.workflow_value_error import WorkflowValueError
from services.utils.string_util import StringUtil


class Stage:
    ACTIVE_STATUS = "ACTIVE"
    COMPLETED_STATUS = "COMPLETED"
    NOT_STARTED_STATUS = "NOT STARTED"

    def __init__(self, *,
                 stage_name: str,
                 stage_order: int,
                 tasks: [Task],
                 status: str = None,
                 **kwargs):
        self.stage_name = stage_name
        self.stage_order = stage_order
        self.tasks = tasks
        if status is not None:
            self.status = status
        else:
            self.status = self.ACTIVE_STATUS

        self.__validate_tasks_type()
        self.__validate_status()
        for key, val in kwargs.items():
            setattr(self, key, val)

    @classmethod
    def from_json(cls, stage_json: Dict):
        if "tasks" not in stage_json:
            stage_json["tasks"] = []

        if not isinstance(stage_json["tasks"], List):
            raise WorkflowTypeError("tasks node must be a List")

        tasks = [Task.from_json(task_dict=task_json) for task_json in stage_json["tasks"]]

        status = stage_json["status"] if "status" in stage_json else None

        return Stage(
            stage_name=stage_json["stage_name"],
            stage_order=stage_json["stage_order"],
            tasks=tasks,
            status=status
        )

    def __validate_tasks_type(self):
        for task in self.tasks:
            if not isinstance(task, Task):
                raise WorkflowTypeError("All elements of tasks must be of type Task")

    def __validate_status(self):
        if self.status not in (self.ACTIVE_STATUS, self.COMPLETED_STATUS, self.NOT_STARTED_STATUS):
            raise WorkflowValueError("status must be in ACTIVE or COMPLETED")

    def all_tasks_completed(self):
        tasks_completed = True
        for task in self.tasks:
            tasks_completed = tasks_completed and (task.status == Task.COMPLETED_STATUS)

        return tasks_completed

    def get_pending_tasks(self):
        return [task for task in self.tasks if task.status == Task.PENDING_STATUS]

    def get_scheduled_tasks(self):
        return [task for task in self.tasks if task.status == Task.SCHEDULED_STATUS]

    def __str__(self):
        return StringUtil.dict_to_str(self.__dict__)
