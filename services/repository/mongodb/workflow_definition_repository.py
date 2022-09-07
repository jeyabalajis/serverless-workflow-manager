from pymongo.database import Database

from domain.workflow import Workflow
from services.database.abstract_db_util import DatabaseUtil
from services.repository.abstract_workflow_definition_repository import WorkflowDefinitionRepository


class MongoDbWorkflowDefinitionRepository(WorkflowDefinitionRepository):
    TABLE_NAME = "wf_workflow_definition"

    def __init__(self, *, database_util: DatabaseUtil):
        super().__init__(database_util=database_util)

    def find_one_by_component_name(self, *, component_name: str) -> Workflow:
        super(MongoDbWorkflowDefinitionRepository, self).find_one_by_component_name(component_name=component_name)
        db: Database = self.database_util.get_db_object()
        workflow_definition = db[self.TABLE_NAME]
        workflow_def_record = workflow_definition.find_one(
            {
                "component_name": component_name
            },
            {
                "_id": 0
            }
        )

        return Workflow.from_json_template(workflow_def_record)
