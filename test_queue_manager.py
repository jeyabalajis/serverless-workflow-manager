from unittest import TestCase
from unittest.mock import patch

from services.queue.aws_sqs_queue_manager import AwsSqsQueueManager


class TestQueueManager(TestCase):
    def test_send_message(self):
        with patch.object(AwsSqsQueueManager, '__init__', return_value=None):
            with patch.object(AwsSqsQueueManager, 'send_message', return_value="123") as mock_method:
                my_queue_manager = AwsSqsQueueManager(profile_name="test", region="ap-south-1")
                my_queue_manager.send_message(queue_name="test_queue", message_body={"name": "test"})
            mock_method.assert_called_once_with(queue_name="test_queue", message_body={"name": "test"})
