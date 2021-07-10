from pymongo.database import Database

from entity.workflow import Workflow
from services.config.config_manager import ConfigManager
from services.config.env_util import EnvUtil
from services.database.db_util import DatabaseUtil


class WorkflowDefinitionRepository:
    __TABLE_NAME = "wf_workflow_definition"
    __DB_NAME = ConfigManager(EnvUtil.get_env()).get_config("workflow_db")
    db: Database = DatabaseUtil(db_name=__DB_NAME).get_db_object()

    @classmethod
    def find_one_by_component_name(cls, *, component_name: str) -> Workflow:
        workflow_definition = cls.db[cls.__TABLE_NAME]
        workflow_def_record = workflow_definition.find_one(
            {
                "component_name": component_name
            },
            {
                "_id": 0
            }
        )

        return Workflow.from_json_template(workflow_def_record)
