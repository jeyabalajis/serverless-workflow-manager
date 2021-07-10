from unittest import TestCase

from entity.Stage import Stage
from entity.Workflow import Workflow
import json


class TestWorkflow(TestCase):

    @classmethod
    def get_sample_workflow_instance(cls):
        with open("./samples/sample_workflow_instance.json") as workflow_instance_file:
            return json.load(workflow_instance_file)

    def test_all_dependencies_completed_false(self):
        workflow_object = Workflow.from_json(workflow_json=self.get_sample_workflow_instance())

        stage = workflow_object.get_stage_by_name(stage_name="PREPARE")
        task = workflow_object.get_task_by_name(stage=stage, task_name="confirm_delivery")
        all_deps_completed = workflow_object.all_dependencies_completed_for_a_task(stage=stage, task=task)

        assert all_deps_completed is False

    def test_all_dependencies_completed_true(self):
        workflow_object = Workflow.from_json(workflow_json=self.get_sample_workflow_instance())

        stage = workflow_object.get_stage_by_name(stage_name="ORDER")
        task = workflow_object.get_task_by_name(stage=stage, task_name="confirm_order")
        all_deps_completed = workflow_object.all_dependencies_completed_for_a_task(stage=stage, task=task)

        assert all_deps_completed is True

    def test_get_active_stage(self):
        workflow_object = Workflow.from_json(workflow_json=self.get_sample_workflow_instance())
        active_stage = workflow_object.get_active_stage()
        assert active_stage.status == Stage.ACTIVE_STATUS

    def test_mark_stage_as_completed(self):
        workflow_object = Workflow.from_json(workflow_json=self.get_sample_workflow_instance())
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
        workflow_object = Workflow.from_json(workflow_json=self.get_sample_workflow_instance())

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
