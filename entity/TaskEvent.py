from entity.Event import Event
from typing import Dict
from exceptions.WorkflowValueError import WorkflowValueError
from entity.Task import Task


class TaskFailed(Event):
    def __init__(self, *, business_ref_no: str, component_name: str, **kwargs):
        super().__init__(business_ref_no=business_ref_no, component_name=component_name, **kwargs)
        self._event_type = "TaskPending"
        self._status = Task.FAILED_STATUS

    @classmethod
    def from_json(cls, *, event_json: Dict):
        if "stage_name" not in event_json:
            raise WorkflowValueError("stage_name is mandatory")

        if "task_name" not in event_json:
            raise WorkflowValueError("task_name is mandatory")

        super(TaskFailed, cls).from_json(event_json=event_json)
