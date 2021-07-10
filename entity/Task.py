from typing import Dict

from exceptions.WorkflowValueError import WorkflowValueError
from services.utils.StringUtil import StringUtil


class Task:
    SERVICE_TASK = "SERVICE"
    HUMAN_TASK = "HUMAN"

    PENDING_STATUS = "PENDING"
    SCHEDULED_STATUS = "SCHEDULED"
    COMPLETED_STATUS = "COMPLETED"
    FAILED_STATUS = "FAILED"

    def __init__(self, *,
                 task_name: str,
                 task_type: str = None,
                 task_queue: str = None,
                 parent_task: [str] = None,
                 status: str = None,
                 **kwargs):
        self.task_name = task_name
        self.task_type = task_type
        self.task_queue = task_queue
        if parent_task is not None:
            self.parent_task = parent_task
        else:
            self.parent_task = []

        if status is not None:
            self.status = status
        else:
            self.status = self.PENDING_STATUS

        self.__validate_task_type()
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __validate_task_type(self):
        if self.task_type not in (self.SERVICE_TASK, self.HUMAN_TASK):
            raise WorkflowValueError("task_type must be SERVICE or HUMAN")

    def mark_as_scheduled(self):
        self.status = self.SCHEDULED_STATUS

    def mark_as_completed(self):
        self.status = self.COMPLETED_STATUS

    def mark_as_failed(self):
        self.status = self.FAILED_STATUS

    def set_misc_attributes(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

    @classmethod
    def from_json(cls, task_dict: Dict):
        return Task(**task_dict)

    def __str__(self):
        return StringUtil.dict_to_str(self.__dict__)
