from unittest import TestCase
from unittest.mock import patch

from services.queue.queue_manager import QueueManager


class TestQueueManager(TestCase):
    def test_send_message(self):
        with patch.object(QueueManager, '__init__', return_value=None):
            with patch.object(QueueManager, 'send_message', return_value="123") as mock_method:
                my_queue_manager = QueueManager(queue_name="test_queue")
                my_queue_manager.send_message({"name": "test"})
            mock_method.assert_called_once_with({"name": "test"})
