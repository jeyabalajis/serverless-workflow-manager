from typing import Dict

from pymongo.database import Database

from entity.workflow import Workflow
from services.config.config_manager import ConfigManager
from services.config.env_util import EnvUtil
from services.database.db_util import DatabaseUtil
from services.utils.dict_util import DictUtil
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowInstanceRepository:
    __TABLE_NAME = "wf_workflow_instance"
    __DB_NAME = ConfigManager(EnvUtil.get_env()).get_config("workflow_db")
    db: Database = DatabaseUtil(db_name=__DB_NAME).get_db_object()

    @classmethod
    def find_one_by_business_ref_no(cls, *, business_ref_no: str) -> Workflow:
        workflow_instance = cls.db[cls.__TABLE_NAME]
        workflow_instance_record = workflow_instance.find_one(
            {
                "business_ref_no": business_ref_no
            },
            {
                "_id": 0
            }
        )

        return Workflow.from_json(workflow_instance_record)

    @classmethod
    def upsert(cls, *, workflow: Workflow):
        workflow_dict: Dict = workflow.get_dict()
        DictUtil.remove_key(workflow_dict, "version")
        DictUtil.remove_key(workflow_dict, "updated_at")

        wf_workflow_instance: Database = cls.db[cls.__TABLE_NAME]
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
