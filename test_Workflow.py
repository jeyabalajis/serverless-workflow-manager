from unittest import TestCase
from entity.Workflow import Workflow
from entity.Task import Task
from entity.Stage import Stage
import pytest


class TestWorkflow(TestCase):

    def test_workflow(self):
        return {
            "business_ref_no": "ORDER-001",
            "component_name": "ITALIAN",
            "stages": [
                {
                    "stage_name": "START",
                    "stage_order": 0.0,
                    "status": "COMPLETED",
                },
                {
                    "stage_name": "ORDER",
                    "stage_order": 1.0,
                    "tasks": [
                        {
                            "task_name": "confirm_order",
                            "parent_task": [],
                            "task_queue": "confirm_order_queue",
                            "task_type": "SERVICE",
                            "business_status": "ORDER CONFIRMED",
                            "status": "COMPLETED",
                            "reason": "",
                            "last_updated_time_pretty": "Fri Jun 28 10:45:41 2019"
                        }
                    ],
                    "status": "COMPLETED"
                },
                {
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
                },
                {
                    "stage_name": "DELIVER",
                    "stage_order": 3.0,
                    "tasks": [
                        {
                            "task_name": "deliver_food",
                            "parent_task": [],
                            "task_type": "HUMAN",
                            "task_queue": "deliver_food_queue",
                            "assigned_to": "delivery_executive",
                            "business_status": "FOOD DELIVERED",
                            "status": "PENDING"
                        }
                    ],
                    "status": "NOT STARTED"
                }
            ],
            "version": 18,
            "workflow_name": "Deliver Pizza",
            "updated_at": "2019-06-28T10:45:43.012+0000"
        }

    def test_all_dependencies_completed_false(self):
        workflow_object = Workflow.from_json(workflow_json=self.test_workflow())

        stage = workflow_object.get_stage_by_name(stage_name="PREPARE")
        task = workflow_object.get_task_by_name(stage=stage, task_name="confirm_delivery")
        all_deps_completed = workflow_object.all_dependencies_completed_for_a_task(stage=stage, task=task)

        assert all_deps_completed is False

    def test_all_dependencies_completed_true(self):
        workflow_object = Workflow.from_json(workflow_json=self.test_workflow())

        stage = workflow_object.get_stage_by_name(stage_name="ORDER")
        task = workflow_object.get_task_by_name(stage=stage, task_name="confirm_order")
        all_deps_completed = workflow_object.all_dependencies_completed_for_a_task(stage=stage, task=task)

        assert all_deps_completed is True

    def test_get_active_stage(self):
        workflow_object = Workflow.from_json(workflow_json=self.test_workflow())
        active_stage = workflow_object.get_active_stage()
        assert active_stage.status == Stage.ACTIVE_STATUS
