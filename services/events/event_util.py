import json
from typing import Dict

from entity.event import Event
from entity.start_workflow_event import StartWorkflowEvent
from entity.task import Task
from entity.task_event import TaskEvent
from exceptions.workflow_value_error import WorkflowValueError


class EventManager:
    SQS_EVENT_TYPE = "SQS"

    def __init__(self, *, event_dict: Dict, event_type: str):
        self.event_dict = event_dict
        self.__validate_event_dict()

        if event_type not in self.SQS_EVENT_TYPE:
            raise WorkflowValueError("Only SQS supported as event_type")

        self.event_type = event_type

    def __validate_event_dict(self):
        assert (self.event_dict is not None and "Records" in self.event_dict and self.event_dict["Records"] is not None)

        for event_record in self.event_dict.get("Records"):
            assert "body" in event_record and event_record["body"] is not None

            message = event_record["body"]
            assert "event_name" in message

    def get_events(self) -> [Event]:
        if self.event_type == "SQS":
            return self.__get_events_from_sqs_event()

    def __get_events_from_sqs_event(self) -> [Event]:

        event_records = self.event_dict.get("Records")

        event_objects = []
        for event_record in event_records:
            message = event_record["body"]

            event_objects.append(self.__get_event(message=message))

        return event_objects

    @classmethod
    def __get_event(cls, *, message: Dict) -> Event:
        if message["event_name"] == "StartWorkflow":
            return StartWorkflowEvent(
                business_ref_no=message.get("business_ref_no"),
                component_name=message.get("component_name")
            )

        status = None
        if message["event_name"] == "TaskCompleted":
            status = Task.COMPLETED_STATUS

        if message["event_name"] == "TaskPending":
            status = Task.PENDING_STATUS

        if message["event_name"] == "TaskFailed":
            status = Task.FAILED_STATUS

        assert status is not None

        return TaskEvent(
            business_ref_no=message.get("business_ref_no"),
            component_name=message.get("component_name"),
            stage_name=message.get("stage_name"),
            task=Task(
                task_name=message.get("task_name"),
                status=status
            )
        )
