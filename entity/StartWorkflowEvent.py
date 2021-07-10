from entity.Event import Event
from typing import Dict


class StartWorkflowEvent(Event):
    def __init__(self, *, business_ref_no: str, component_name: str, **kwargs):
        super().__init__(business_ref_no=business_ref_no, component_name=component_name, **kwargs)
        self._event_type = "StartWorkflow"

    @classmethod
    def from_json(cls, *, event_json: Dict):
        super(StartWorkflowEvent, cls).from_json(event_json=event_json)

