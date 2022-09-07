from typing import Dict

from domain.event import Event
from services.events.abstract_event_manager import EventManager


class AwsSqsEventManager(EventManager):
    SQS_EVENT_TYPE = "SQS"

    def __init__(self, *, message: Dict):
        super().__init__(message=message)
        self.message = message
        self.__validate_event_dict()

    def __validate_event_dict(self):
        assert (self.message is not None and "Records" in self.message and self.message["Records"] is not None)

        for event_record in self.message.get("Records"):
            assert "body" in event_record and event_record["body"] is not None

            message = event_record["body"]
            assert "event_name" in message

    def get_events(self) -> [Event]:
        """
        extract records from SQS Message and convert them to standard Events
        :return:
        """
        event_records = self.message.get("Records")

        events = []
        for event_record in event_records:
            message = event_record["body"]

            events.append(super(AwsSqsEventManager, self).get_event_from_event_record(event_record=message))

        return events
