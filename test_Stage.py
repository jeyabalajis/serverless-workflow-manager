from unittest import TestCase
from entity.Stage import Stage


class TestStage(TestCase):

    def test_stage_incomplete(self):
        return {
            "stage_name": "PREPARE",
            "stage_order": 2.0,
            "tasks": [
                {
                    "task_name": "make_food",
                    "parent_task": [],
                    "task_type": "SERVICE",
                    "task_queue": "make_food_queue",
                    "status": "SCHEDULED",
                    "last_updated_time_pretty": "Fri Jun 28 10:45:42 2019"
                },
                {
                    "task_name": "assign_executive",
                    "parent_task": [],
                    "task_queue": "assign_executive_queue",
                    "task_type": "SERVICE",
                    "status": "SCHEDULED",
                    "last_updated_time_pretty": "Fri Jun 28 10:45:42 2019"
                },
                {
                    "task_name": "confirm_delivery",
                    "parent_task": [
                        "make_food",
                        "assign_executive"
                    ],
                    "task_queue": "confirm_delivery_queue",
                    "task_type": "SERVICE",
                    "business_status": "FOOD ON THE WAY",
                    "status": "PENDING"
                }
            ],
            "status": "ACTIVE"
        }

    def test_all_tasks_completed(self):
        test_stage = self.test_stage_incomplete()

        stage_object = Stage.from_json(test_stage)
        assert stage_object.all_tasks_completed() is False
