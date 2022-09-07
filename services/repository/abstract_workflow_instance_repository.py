from abc import ABC
from services.database.abstract_db_util import DatabaseUtil
from domain.workflow import Workflow


class WorkflowInstanceRepository(ABC):
    def __init__(self, *, database_util: DatabaseUtil):
        self.database_util = database_util

    def find_one_by_business_ref_no(self, *, business_ref_no: str) -> Workflow:
        """
        abstract method
        :param business_ref_no:
        :return:
        """
        pass

    def upsert(self, *, workflow: Workflow):
        """
        abstract method
        :param workflow:
        :return:
        """
        pass
