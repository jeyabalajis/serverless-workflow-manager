import logging

from domain.start_workflow_event import StartWorkflowEvent
from domain.task import Task
from domain.task_event import TaskEvent
from services.config.config_manager import ConfigManager
from services.config.env_util import EnvUtil
from services.database.db_secret import DatabaseSecret
from services.database.mongo_db_db_util import MongoDbDatabaseUtil
from services.events.event_manager_aws_sqs import AwsSqsEventManager
from services.queue.aws_sqs_queue_manager import AwsSqsQueueManager
from services.repository.mongodb.workflow_definition_repository import MongoDbWorkflowDefinitionRepository
from services.repository.mongodb.workflow_instance_repository import MongoDbWorkflowInstanceRepository
from services.secrets.aws_secrets_manager import AwsSecretsManager
from services.workflow.workflow_manager import WorkflowManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def process_messages(event, context=None):
    """
    process_messages is invoked by a serverless component based on an event.
    Here we have handled SQS events triggering this function.
    Based on the type of event, this function either starts a workflow or updates a task.
    :param event:
    :param context:
    :return:
    """

    event_manager = AwsSqsEventManager(message=event)

    events = event_manager.get_events()

    if events is None:
        logger.info("no event is sent")
        return

    logger.info("context: {}".format(str(context)))

    config_manager = ConfigManager(environment=EnvUtil().get_env())

    region_name = config_manager.get_config("region_name")
    profile_name = config_manager.get_config("profile_name")
    workflow_db_name = config_manager.get_config("workflow_db")
    secret_name = config_manager.get_config("db_credentials_id")

    sqs_queue_manager = AwsSqsQueueManager(
        profile_name=profile_name,
        region=region_name
    )

    db_secret_json_string = AwsSecretsManager(
        profile_name=profile_name,
        region=region_name
    ).get_secret(secret_name=secret_name)

    db_secret: DatabaseSecret = DatabaseSecret.from_json_string(db_secret_json_string=db_secret_json_string)

    mongo_db_database_util = MongoDbDatabaseUtil(db_name=workflow_db_name, db_secret=db_secret)
    workflow_definition_repo = MongoDbWorkflowDefinitionRepository(database_util=mongo_db_database_util)
    workflow_instance_repo = MongoDbWorkflowInstanceRepository(database_util=mongo_db_database_util)

    for event in events:
        workflow_manager = WorkflowManager(
            event=event,
            queue_manager=sqs_queue_manager,
            workflow_definition_repository=workflow_definition_repo,
            workflow_instance_repository=workflow_instance_repo
        )
        workflow_manager.execute_event()
