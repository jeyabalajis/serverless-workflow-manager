from abc import ABC, abstractmethod
from typing import Dict
from exceptions.WorkflowValueError import WorkflowValueError
from exceptions.WorkflowTypeError import WorkflowTypeError


class Event:
    def __init__(self, *, business_ref_no: str, component_name: str, **kwargs):
        self.business_ref_no = business_ref_no
        self.component_name = component_name
        self._event_type = "Event"

        for key, val in kwargs.items():
            setattr(self, key, val)

    @classmethod
    @abstractmethod
    def from_json(cls, *, event_json: Dict):

        if not isinstance(event_json, Dict):
            raise WorkflowTypeError("event_json must be a dict")

        if "business_ref_no" not in event_json:
            raise WorkflowValueError("business_ref_no is mandatory")

        if "component_name" not in event_json:
            raise WorkflowValueError("component_name is mandatory")

        return Event(**event_json)
