from abc import ABC
from services.database.abstract_db_util import DatabaseUtil
from domain.workflow import Workflow


class WorkflowDefinitionRepository(ABC):
    def __init__(self, *, database_util: DatabaseUtil):
        self.database_util = database_util

    def find_one_by_component_name(self, *, component_name: str) -> Workflow:
        """
        abstract method
        :param component_name:
        :return:
        """
        pass

