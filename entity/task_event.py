from typing import Dict

from entity.event import Event
from entity.task import Task
from exceptions.workflow_value_error import WorkflowValueError


class TaskEvent(Event):
    def __init__(self, *, business_ref_no: str, component_name: str, stage_name: str, task: Task, **kwargs):
        super().__init__(business_ref_no=business_ref_no, component_name=component_name, **kwargs)
        self.stage_name = stage_name
        self.task = task

    @classmethod
    def from_json(cls, *, event_json: Dict):
        if "stage_name" not in event_json:
            raise WorkflowValueError("stage_name is mandatory")

        if "task_name" not in event_json:
            raise WorkflowValueError("task_name is mandatory")

        super(TaskEvent, cls).from_json(event_json=event_json)

    def get_dict(self) -> Dict:
        return dict(
            business_ref_no=self.business_ref_no,
            component_name=self.component_name,
            event_name=self.__get_event_name(),
            stage_name=self.stage_name,
            task_name=self.task.task_name,
            task_type=self.task.task_type
        )

    def __get_event_name(self):
        if self.task.status == Task.SCHEDULED_STATUS:
            return "StartTask"
