from typing import Dict
from domain.event import Event
from domain.start_workflow_event import StartWorkflowEvent
from domain.task import Task
from domain.task_event import TaskEvent


class EventManager:
    def __init__(self, *, message: Dict):
        self.message = message

    def get_events(self) -> [Event]:
        """
        abstract method
        :return:
        """
        pass

    @classmethod
    def get_event_from_event_record(cls, *, event_record: Dict) -> Event:

        assert "event_name" in event_record
        assert "business_ref_no" in event_record
        assert "component_name" in event_record

        assert event_record["event_name"] in (
            "StartWorkflow",
            "TaskCompleted",
            "TaskPending",
            "TaskFailed"
        )

        if event_record["event_name"] == "StartWorkflow":
            return StartWorkflowEvent(
                business_ref_no=event_record.get("business_ref_no"),
                component_name=event_record.get("component_name")
            )

        status = None
        if event_record["event_name"] == "TaskCompleted":
            status = Task.COMPLETED_STATUS

        if event_record["event_name"] == "TaskPending":
            status = Task.PENDING_STATUS

        if event_record["event_name"] == "TaskFailed":
            status = Task.FAILED_STATUS

        assert status is not None

        return TaskEvent(
            business_ref_no=event_record.get("business_ref_no"),
            component_name=event_record.get("component_name"),
            stage_name=event_record.get("stage_name"),
            task=Task(
                task_name=event_record.get("task_name"),
                status=status
            )
        )
