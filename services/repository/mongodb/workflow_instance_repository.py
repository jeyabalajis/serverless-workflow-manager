from typing import Dict

from pymongo.database import Database

from domain.workflow import Workflow
from services.config.config_manager import ConfigManager
from services.config.env_util import EnvUtil
from services.database.mongo_db_db_util import MongoDbDatabaseUtil
from services.utils.dict_util import DictUtil
import logging
import json
from services.repository.abstract_workflow_instance_repository import WorkflowInstanceRepository
from services.database.abstract_db_util import DatabaseUtil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDbWorkflowInstanceRepository(WorkflowInstanceRepository):
    TABLE_NAME = "wf_workflow_instance"

    def __init__(self, *, database_util: DatabaseUtil):
        super().__init__(database_util=database_util)

    def find_one_by_business_ref_no(self, *, business_ref_no: str) -> Workflow:
        super(MongoDbWorkflowInstanceRepository, self).find_one_by_business_ref_no(business_ref_no=business_ref_no)
        db: Database = self.database_util.get_db_object()
        workflow_instance = db[self.TABLE_NAME]
        workflow_instance_record = workflow_instance.find_one(
            {
                "business_ref_no": business_ref_no
            },
            {
                "_id": 0
            }
        )

        return Workflow.from_json(workflow_instance_record)

    def upsert(self, *, workflow: Workflow):
        super(MongoDbWorkflowInstanceRepository, self).upsert(workflow=workflow)
        workflow_dict: Dict = workflow.get_dict()
        DictUtil.remove_key(workflow_dict, "version")
        DictUtil.remove_key(workflow_dict, "updated_at")

        db: Database = self.database_util.get_db_object()
        wf_workflow_instance: Database = db[self.TABLE_NAME]
        wf_workflow_instance.find_one_and_update(
            {
                "business_ref_no": workflow_dict["business_ref_no"]
            },
            {
                "$set": workflow_dict,
                "$inc": {"version": 1},
                "$currentDate": {"updated_at": {"$type": "date"}}
            },
            upsert=True)
