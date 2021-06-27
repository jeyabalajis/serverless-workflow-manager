from entity.Stage import Stage
from entity.Task import Task
from typing import Dict, List
from exceptions.WorkflowTypeError import WorkflowTypeError
from exceptions.WorkflowValueError import WorkflowValueError


class Workflow:
    def __init__(self, *, workflow_name: str, component_name: str, stages: [Stage]):
        self.workflow_name = workflow_name
        self.component_name = component_name
        self.stages = stages
        self.__validate_stages_type()

    @classmethod
    def from_json(cls, workflow_json: Dict):
        if "stages" not in workflow_json:
            raise WorkflowValueError("stages node is mandatory")

        if not isinstance(workflow_json["stages"], List):
            raise WorkflowTypeError("stages node must be a List")

        stages = [Stage.from_json(stage_json=stage_json) for stage_json in workflow_json["stages"]]

        return Workflow(
            workflow_name=workflow_json["workflow_name"],
            component_name=workflow_json["component_name"],
            stages=stages
        )

    def __validate_stages_type(self):
        for stage in self.stages:
            if not isinstance(stage, Stage):
                raise WorkflowTypeError("all elements of stages must be of type Stage")

    def all_dependencies_completed_for_a_task(self, *, stage: Stage, task: Task) -> bool:
        if not task.parent_task:
            return True

        all_parents_completed = True
        for parent_task in task.parent_task:
            parent_task_record = self.get_task_by_name(stage=stage, task_name=parent_task)
            all_parents_completed = all_parents_completed and (parent_task_record.status == Task.COMPLETED_STATUS)

        return all_parents_completed

    def get_stage_by_name(self, *, stage_name: str):
        for stage in self.stages:
            if stage.stage_name == stage_name:
                return stage

    def get_active_stage(self):
        for stage in self.stages:
            if stage.status == Stage.ACTIVE_STATUS:
                return stage

    def get_task_by_name(self, *, stage: Stage, task_name: str):
        for workflow_stage in self.stages:
            if not workflow_stage.stage_name == stage.stage_name:
                continue

            for workflow_task in workflow_stage.tasks:
                if not workflow_task.task_name == task_name:
                    continue
                return workflow_task
        return None
