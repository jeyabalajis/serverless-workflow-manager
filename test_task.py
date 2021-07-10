import json
from unittest import TestCase

from entity.task import Task


class TestTask(TestCase):
    def test_set_misc_attributes(self):
        task = Task(task_name="TEST", task_type="SERVICE", parent_tasks=[])

        misc_attr = {"reason": "general"}
        task.set_misc_attributes(**misc_attr)

        print(json.dumps(task.__dict__))
        assert task.__dict__["reason"] == "general"

    def test_from_json(self):
        task_json = dict(
            task_name="TEST",
            task_type="SERVICE",
            parent_tasks=[],
            reason="general"
        )

        task = Task.from_json(task_json)

        assert task.__dict__["task_name"] == "TEST" and task.__dict__["reason"] == "general"
