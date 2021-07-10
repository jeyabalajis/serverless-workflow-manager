from unittest import TestCase

from entity.Stage import Stage
from entity.Workflow import Workflow


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

    def test_mark_stage_as_completed(self):
        workflow_object = Workflow.from_json(workflow_json=self.test_workflow())
        current_active_stage = workflow_object.get_active_stage()
        workflow_object.mark_stage_as_completed(stage=current_active_stage)
        next_active_stage = workflow_object.get_active_stage()

        print("current: {} next: {}".format(current_active_stage.stage_name, next_active_stage.stage_name))
        assert next_active_stage.stage_order == current_active_stage.stage_order + 1
        assert (
                current_active_stage.status == Stage.COMPLETED_STATUS
                and next_active_stage.status == Stage.ACTIVE_STATUS
        )

        workflow_object.mark_stage_as_completed(stage=next_active_stage)

        next_next_active_stage = workflow_object.get_active_stage()
        assert next_next_active_stage is None

    def test_find_and_schedule_tasks(self):
        workflow_object = Workflow.from_json(workflow_json=self.test_workflow())

        workflow_object.find_and_schedule_tasks()
        active_stage = workflow_object.get_active_stage()
        pending_tasks = active_stage.get_pending_tasks()
        assert pending_tasks is not None and len(pending_tasks) == 1

        scheduled_tasks = active_stage.get_scheduled_tasks()
        for task in scheduled_tasks:
            workflow_object.mark_task_as_completed(stage=active_stage, task=task)

        workflow_object.find_and_schedule_tasks()
        active_stage = workflow_object.get_active_stage()
        pending_tasks = active_stage.get_pending_tasks()
        scheduled_tasks = active_stage.get_scheduled_tasks()
        assert len(pending_tasks) == 0 and len(scheduled_tasks) == 1
