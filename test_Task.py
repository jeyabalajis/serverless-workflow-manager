from unittest import TestCase
from entity.Task import Task
import json


class TestTask(TestCase):
    def test_set_misc_attributes(self):
        task = Task(task_name="TEST", task_type="SERVICE", parent_tasks=[])

        misc_attr = {"reason": "general"}
        task.set_misc_attributes(**misc_attr)

        print(json.dumps(task.__dict__))
        assert task.__dict__["reason"] == "general"
