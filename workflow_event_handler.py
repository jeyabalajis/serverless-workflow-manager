import json
import logging
import os
import time

import boto3
from pymongo import ReturnDocument

from config import config
from config.config import load_config
from database import db_utils

__logger = logging.getLogger(__name__)
__logger.setLevel(logging.INFO)

__db = None


def __acquire_db_connection(p_db_name):
    """
    Acquire database connection for a database name
    :return:
    """
    if p_db_name == 'workflow_db':
        global __db
        if __is_empty(__db):
            __db = db_utils.get_db_object('workflow_db')


def __is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True


def __get_workflow_definition(component_name):
    """
    Fetch the workflow definition template from database.

    :param component_name:
    :return:
    """

    __acquire_db_connection("workflow_db")

    wf_workflow_definition = __db['wf_workflow_definition']
    workflow_def_record = wf_workflow_definition.find_one(
        {
            "component_name": component_name
        },
        {
            "_id": 0
        }
    )

    return workflow_def_record


def get_workflow_instance(business_ref_no):
    """
    Get a workflow instance for a business_ref_no
    :param business_ref_no:
    :return:
    """

    __acquire_db_connection("workflow_db")
    wf_workflow_instance = __db['wf_workflow_instance']
    wf_instance_record = wf_workflow_instance.find_one(
        {
            "business_ref_no": business_ref_no
        },
        {
            "_id": 0
        }
    )
    return wf_instance_record


def __create_workflow_instance(workflow_instance):
    """
    Create a fresh workflow instance.
    :param workflow_instance:
    :return:
    """

    __acquire_db_connection("workflow_db")
    result = __db["wf_workflow_instance"].find_one_and_update(
        {
            "business_ref_no": workflow_instance["business_ref_no"]
        },
        {
            "$set": workflow_instance,
            "$inc": {"version": 1}
        },
        upsert=True,
        return_document=ReturnDocument.AFTER)

    if not __is_empty(result):
        return True
    else:
        return False


def __initiate_workflow(p_message):
    """

    This function is called when the workflow manager receives a StartWorkflow event.
    It creates a fresh instance out of the workflow definition template.
    :param p_message:
    :return:
    """

    if "component_name" in p_message:
        __logger.info("retrieving workflow definition for component:")
        __logger.info(p_message["component_name"])

        workflow_definition = __get_workflow_definition(p_message["component_name"])

        if workflow_definition:

            workflow_instance = workflow_definition
            workflow_instance["business_ref_no"] = p_message["business_ref_no"]
            if "stages" in workflow_instance:

                for (ind, stage) in enumerate(workflow_instance["stages"]):
                    if ind == 0:
                        stage["status"] = "ACTIVE"
                    else:
                        stage["status"] = "NOT STARTED"

                    if "tasks" in stage:
                        for _task in stage["tasks"]:
                            _task["status"] = "PENDING"

            __logger.info("creating workflow instance in db!!!")
            __create_workflow_instance(workflow_instance)
            return workflow_instance
        else:
            return {}
    else:
        __logger.error("Component name is not part of the message. Cannot instantiate workflow")
        __logger.info(json.dumps(p_message, indent=4, sort_keys=True, default=str))
        return {}


def remove_key(d, key):
    r = dict(d)
    if key in r:
        del r[key]
    return r


# Jeya@04-Sep-2018 a new parameter p_reason has been added
def __update_task(business_ref_no, p_stage_name, p_task_name, p_status, p_message, p_reason=None):
    """
    There is no support to update a second level array element in Mongo DB.
    So this approach takes all the tasks for a stage, modifies the appropriate task's status
    and pushes the entire doc back down the throat of mongo.
    we can re visit this logic when mongo upgrades to solve this issue.
    :type p_reason: basestring
    :param business_ref_no:
    :param stage:
    :param task:
    :param status:
    :return:
    """
    __logger.info(
        "Updating Task " + p_task_name + " belonging to stage " + p_stage_name +
        ' as: ' + p_status + " for " + business_ref_no)

    try:
        __acquire_db_connection("workflow_db")
        wf_workflow_instance = __db['wf_workflow_instance']

        workflow_stage_obj = wf_workflow_instance.find_one(
            {
                "business_ref_no": business_ref_no
            }
        )

        if (
                not __is_empty(workflow_stage_obj)
                and "stages" in workflow_stage_obj
                and not __is_empty(workflow_stage_obj["stages"])
        ):
            _no_retries = 10
            while _no_retries > 1:

                # Retrieve the version and remove it from the object
                _version = 0
                if "version" in workflow_stage_obj:
                    _version = workflow_stage_obj["version"]
                    del workflow_stage_obj["version"]

                # Remove updated_at. it will be freshly stamped during update
                if "updated_at" in workflow_stage_obj:
                    del workflow_stage_obj["updated_at"]

                # Update task status
                for stage in workflow_stage_obj["stages"]:
                    if (
                            stage["stage_name"] == p_stage_name
                            and "tasks" in stage
                            and not __is_empty(stage["tasks"])
                    ):
                        for _task in stage["tasks"]:
                            if _task["task_name"] == p_task_name:
                                _task["status"] = p_status
                                _task["reason"] = p_reason
                                _task["last_updated_time_pretty"] = time.strftime('%c')
                                if "version" in _task:
                                    del _task["version"]

                # Find the instance for the current version and update
                # If data not found, fetch fresh record and retry until retries are exhausted
                result = wf_workflow_instance.update_one(
                    {
                        "business_ref_no": business_ref_no,
                        "version": _version
                    },
                    {
                        "$set": workflow_stage_obj,
                        "$inc": {"version": 1},
                        "$currentDate": {"updated_at": {"$type": "date"}}
                    },
                    upsert=False
                )

                if result.matched_count > 0:
                    if result.modified_count <= 0:
                        __logger.info("Nothing was modified. Push it into a dead letter queue")
                    else:
                        __logger.info("Task updated successfully!")
                    break
                else:
                    __logger.info("Workflow instance version has changed!")
                    _no_retries -= 1
                    __logger.info("no of retries remaining: " + str(_no_retries))
                    workflow_stage_obj = wf_workflow_instance.find_one(
                        {
                            "business_ref_no": business_ref_no
                        }
                    )
    except:
        import traceback
        __logger.error("Update Task crashed!!")
        __logger.error(traceback.format_exc())


def __schedule_task(
        business_ref_no,
        stage,
        pending_task,
        task_queue_name,
        post_status,
        message_body
):
    """

    Schedule a task by pushing the event into the task queue.

    :param business_ref_no:
    :param stage:
    :param pending_task:
    :param task_queue_name:
    :param post_status:
    :param message_body
    :return:
    """
    try:
        task_queue = __fn_get_queue(task_queue_name)
        message_body = json.dumps(message_body, indent=4, sort_keys=True, default=str)
        response = task_queue.send_message(MessageBody=message_body)
        if not __is_empty(response):
            __logger.info("Task " + pending_task["task_name"] + " scheduled to queue successfully")
            __update_task(
                business_ref_no,
                stage["stage_name"],
                pending_task["task_name"],
                post_status,
                message_body
            )
            __logger.info("Task " + pending_task["task_name"] + " marked as scheduled in db successfully")
    except:
        __logger.error("Failed while scheduling message into QUEUE")
        import traceback

        __logger.error(traceback.format_exc())


def schedule_tasks(
        component_name,
        business_ref_no,
        stage,
        pending_tasks
):
    """

    :param component_name
    :param business_ref_no:
    :param stage:
    :param pending_tasks:
    :return:
    """

    if not __is_empty(pending_tasks) and len(pending_tasks) > 0:
        for pending_task in pending_tasks:
            task_queue_name = pending_task["task_queue"]

            message_body = {
                "component_name": component_name.split('-')[0],
                "business_ref_no": business_ref_no,
                "event_name": "StartTask",
                "stage_name": stage["stage_name"],
                "task_name": pending_task["task_name"],
                "task_type": pending_task["task_type"],
            }

            _additional_fields = [
                "fanout_topic_arn_on_schedule",
                "fanout_topic_arn_on_complete",
                "fanout_topic_arn_on_fail",
                "notification_type",
                "task_owner",
                "ignore_task_failure"
            ]

            for _key in _additional_fields:
                if _key in pending_task:
                    message_body[_key] = pending_task[_key]

            __schedule_task(
                business_ref_no,
                stage,
                pending_task,
                task_queue_name,
                "SCHEDULED",
                message_body
            )


def __get_task_record(p_stage_name, p_task_name, workflow_instance):
    """

    :param p_stage_name:
    :param p_task_name:
    :param workflow_instance:
    :return:
    """
    if not __is_empty(workflow_instance):
        if (
                "stages" in workflow_instance
                and not __is_empty(workflow_instance["stages"])
        ):
            for stage in workflow_instance["stages"]:
                if stage["stage_name"] == p_stage_name:
                    if (
                            "tasks" in stage
                            and not __is_empty(stage["tasks"])
                    ):
                        for _task in stage["tasks"]:
                            if _task["task_name"] == p_task_name:
                                return _task
    return {}


def __all_deps_completed(stage, task, workflow_instance):
    """

    :param stage:
    :param task:
    :return:
    """

    if "parent_task" in task and not __is_empty(task["parent_task"]):
        all_parents_completed = True
        for parent in task["parent_task"]:
            parent_task = __get_task_record(
                stage["stage_name"],
                parent,
                workflow_instance
            )
            if not __is_empty(parent_task) and 'status' in parent_task and "COMPLETED" != parent_task['status']:
                all_parents_completed = False
                break
        return all_parents_completed
    else:
        return True


def __get_pending_tasks(active_stage, workflow_instance):
    """

    return all tasks with status as PENDING from a stage.

    :param active_stage:
    :return:
    """
    pending_tasks = []
    if not __is_empty(active_stage) and "tasks" in active_stage:
        for task in active_stage["tasks"]:
            if (
                    "status" in task
                    and task["status"] == "PENDING"
                    and __all_deps_completed(
                        active_stage,
                        task,
                        workflow_instance
                    )
            ):
                pending_tasks.append(task)
    return pending_tasks


def __update_stage(business_ref_no, p_stage, p_status):
    """

    :param business_ref_no:
    :param p_stage:
    :return:
    """
    __acquire_db_connection("workflow_db")
    result = __db["wf_workflow_instance"].find_one_and_update(
        {
            "business_ref_no": business_ref_no,
            "stages.stage_name": p_stage["stage_name"]
        },
        {
            "$set": {
                "stages.$.status": p_status
            },
            "$inc": {
                "version": 1
            }
        },
        upsert=False)

    if not __is_empty(result):
        __logger.info("instance id:")
        __logger.info(result)


def __resolve_next_active_stage(business_ref_no):
    """

    :param business_ref_no:
    :return:
    """
    __logger.info("*** RESOLVE NEXT STAGE ***")
    try:
        workflow_instance = get_workflow_instance(business_ref_no)
        active_stage = {}

        if not __is_empty(workflow_instance) and "stages" in workflow_instance:
            for stage in workflow_instance["stages"]:
                if "status" in stage and stage["status"] != "COMPLETED":
                    active_stage = stage
                    __logger.info("active stage found: " + active_stage["stage_name"])
                    __logger.info("update stage as active")
                    __update_stage(business_ref_no, active_stage, "ACTIVE")
                    break

        return active_stage
    except:
        __logger.error("*** RESOLVE NEXT STAGE FAILED!!!***")
        import traceback
        __logger.error(traceback.format_exc())
        return {}


def __get_active_stage(stages):
    """

    :param stages:
    :return:
    """
    if not __is_empty(stages):
        for stage in stages:
            if stage["status"] == "ACTIVE":
                active_stage = stage
                return active_stage
    else:
        return {}


def __all_tasks_completed(p_active_stage, workflow_instance):
    """

    :param p_active_stage:
    :param workflow_instance:
    :return:
    """
    if not __is_empty(p_active_stage):
        if "tasks" in p_active_stage and not __is_empty(p_active_stage["tasks"]):
            all_tasks_done = True
            for task in p_active_stage["tasks"]:
                task = __get_task_record(
                    p_active_stage["stage_name"],
                    task["task_name"],
                    workflow_instance
                )
                if (
                        not __is_empty(task)
                        and 'status' in task
                        and task['status'] != "COMPLETED"
                ):
                    all_tasks_done = False
                    break
            return all_tasks_done
        else:
            return True
    else:
        return True


def __find_and_schedule_tasks(workflow_instance):
    """

    :param workflow_instance:
    :return:
    The workflow instance is organized as a set of stages & a set of tasks inside each stage.
    At any point in time, only one stage is ACTIVE.
    For the active stage, the system keeps scheduling tasks which are ready to be scheduled.
    When there are dependent tasks on a task, dependent tasks will wait until the parent task is completed.

    When all tasks for a stage are completed, the corresponding stage is marked as COMPLETED
    and the next stage is activated.

    This is repeated until the system can no more find any active stage at all.

    Please note that the workflow manager DOES NOT WAIT or SLEEP. It reacts based on events.
    Upon StartWorkflow event, the tasks eligible to be scheduled are scheduled.
    When these tasks are marked completed (TaskCompleted), the next set of eligible tasks on the task are scheduled
    When there are no more tasks to schedule in a stage, the next stage is activated & the process repeated.

    Logic:
    For the instance, get the current active stage.
    if active stage is found
        [1] get pending tasks & schedule them
        if no pending tasks, get the next active stage & repeat [1]
        if no active stage, just close the workflow and return
    if active stage is not found
        this is an instance with no active stage, just close the workflow and return
    """
    __logger.info('***** inside find and schedule tasks *****')

    try:
        find_tasks = True
        if not __is_empty(workflow_instance):
            business_ref_no = workflow_instance["business_ref_no"]

            component_name = ""
            if "component_name" in workflow_instance:
                component_name = workflow_instance["component_name"]

            __logger.info("business ref no: " + str(business_ref_no))

            if "stages" in workflow_instance:
                stages = workflow_instance["stages"]

                active_stage = __get_active_stage(stages)

                if not __is_empty(active_stage):
                    # keep searching until you find pending tasks
                    if "stage_name" in active_stage:
                        __logger.info("Find Tasks to schedule for stage: " + active_stage["stage_name"])

                    while find_tasks:
                        # obtained active stage. get the tasks pending to be scheduled now.
                        pending_tasks = __get_pending_tasks(
                            active_stage,
                            workflow_instance
                        )
                        if not __is_empty(pending_tasks):
                            __logger.info("PENDING TASKS FOUND!")
                            __logger.info(pending_tasks)
                            __logger.info("Schedule pending tasks now...")
                            schedule_tasks(component_name, business_ref_no, active_stage, pending_tasks)
                            find_tasks = False
                        else:
                            if __all_tasks_completed(
                                    active_stage,
                                    workflow_instance
                            ):
                                # no tasks in this stage. go to the next stage.
                                __logger.info("marking stage " + active_stage["stage_name"] + " as COMPLETED:")
                                __update_stage(business_ref_no, active_stage, "COMPLETED")

                                __logger.info("get next active stage")
                                active_stage = __resolve_next_active_stage(business_ref_no)
                                if __is_empty(active_stage):
                                    __logger.info("there is no next active stage. stop searching!!!")
                                    find_tasks = False
                            else:
                                __logger.info("scheduled tasks are not yet done. sleep for now")
                                find_tasks = False
    except:
        __logger.error('***** find and schedule tasks FAILED!!! *****')
        import traceback
        __logger.error(traceback.format_exc())


def __start_workflow(p_message):
    """

    This function gets a workflow instance for the component for which workflow has been started.
    Then it finds the tasks that must be scheduled for the workflow instance and schedules them.

    :param p_message:
    :return:
    """
    try:
        __logger.info(" initiating workflow .....")
        workflow_instance = __initiate_workflow(p_message)

        __logger.info(" find and schedule tasks for the workflow instance .....")
        __find_and_schedule_tasks(workflow_instance)
    except:
        __logger.error('***** start workflow FAILED!!! *****')
        import traceback
        __logger.error(traceback.format_exc())


def __get_tasks_for_a_stage(p_business_ref_no, p_stage_name):
    """

    :param p_business_ref_no:
    :param p_stage_name:
    :return:
    """
    __acquire_db_connection("workflow_db")
    workflow_stage_obj = __db["wf_workflow_instance"].find_one(
        {
            "business_ref_no": p_business_ref_no,
            "stages.stage_name": p_stage_name
        }
    )

    return workflow_stage_obj


def __fn_get_sns_client():
    """

    Acquire a SNS handle.
    :return:
    """
    region_name = config.get_config("region_name")

    sns_client = boto3.client(
        'sns',
        region_name=region_name
    )
    return sns_client


def __fan_out_message(message, status):
    """

    This procedure will publish the message to a fan out topic, if configured.

    Any SQS subscribers subscribed to this topic can consume the message and perform
    additional activity.

    :param message:
    :return:
    """
    if message:
        _fanout_topic_arn = None
        if status == "COMPLETED":
            if "fanout_topic_arn_on_complete" in message:
                _fanout_topic_arn = message["fanout_topic_arn_on_complete"]

        if status == "FAILED":
            if "fanout_topic_arn_on_fail" in message:
                _fanout_topic_arn = message["fanout_topic_arn_on_fail"]

        __logger.info('_fanout_topic_arn: ' + str(_fanout_topic_arn))
        if _fanout_topic_arn:
            _sns_client = __fn_get_sns_client()

            request_body_str = json.dumps(message, indent=4, sort_keys=True, default=str)
            response = _sns_client.publish(
                TopicArn=str(_fanout_topic_arn),
                Message=request_body_str,
            )

            __logger.info('response: ' + str(response))


def __update_task_from_message(p_message, p_status):
    """

    Persist the task response (Failed or Completed) from the micro service
    and schedule fresh set of tasks as applicable.

    :param p_message:
    :param p_status:
    :return:
    """
    __logger.info('validating message data')
    if "business_ref_no" in p_message and "stage_name" in p_message and "task_name" in p_message:
        __logger.info('mark task as ' + p_status)

        reason = ''
        if "reason" in p_message:
            reason = p_message["reason"]

        __update_task(
            p_message["business_ref_no"],
            p_message["stage_name"],
            p_message["task_name"],
            p_status,
            p_message,
            reason
        )

        __logger.info('task is updated! now check if something more has to be scheduled')

        __logger.info('acquire workflow instance and schedule new tasks')
        workflow_instance = get_workflow_instance(p_message["business_ref_no"])
        if not __is_empty(workflow_instance):
            __logger.info('find and schedule tasks')
            __find_and_schedule_tasks(workflow_instance)
        else:
            __logger.error('workflow instance not there for: ' + p_message["business_ref_no"])
    else:
        __logger.error('Mandatory fields not present in message')


def __fn_get_queue(queue_name):
    """

    Acquire a queue handle.
    :param queue_name:
    :return:
    """

    region_name = config.get_config("region_name")
    profile_name = config.get_config("profile_name")

    # Create a SQS client. For local executions, use a specific named aws configuration profile
    # When executed through Lambda, use default profile
    if 'FRAMEWORK' in os.environ and os.environ['FRAMEWORK'] in ('Zappa', 'CircleCi'):
        session = boto3.session.Session()
    else:
        session = boto3.session.Session(profile_name=profile_name)

    __sqs = session.resource(service_name='sqs', region_name=region_name)

    queue = __sqs.get_queue_by_name(QueueName=queue_name)
    return queue


def process_messages(event, context):
    """
    Zappa lambda handler calls this function passing the event and context.
    The event_name under event is used to process the corresponding event.
    The following events are supported:

    StartWorkflow:
        Start a workflow process. The workflow manager will start orchestrating micro services
        based on a workflow definition.
    TaskCompleted:
        This event is called by the constituent micro service signalling the completion of the task
        When a task is completed, the workflow manager automatically discovers the next set of tasks and schedules them

    TaskFailed
        This event is called by the constituent micro service signalling that failure of the task
        When a task is marked as failed, the workflow manager does not do any action.
        A separate re-trier service must diagnose the root cause of the failure.
        The workflow manager is completely functionality agnostic.

    TaskPending
        This event will mark the task as pending and retry the task.

    :param event:
    :param context:
    :return:
    """

    env_name = os.environ.get('env')

    if not env_name:
        env_name = 'prod'

    load_config(env_name)

    # Get records sent by SQS event
    if event and "Records" in event and event["Records"]:
        event_records = event["Records"]
        if event_records:
            for event_record in event_records:

                __logger.info("Message Body: " + event_record["body"])
                message = json.loads(event_record["body"])
                if message:
                    try:
                        __acquire_db_connection('workflow_db')
                        if "event_name" in message:

                            # Start workflow
                            if message["event_name"] == "StartWorkflow":
                                __logger.info('calling start workflow')
                                __start_workflow(message)

                            # Mark task as completed
                            if message["event_name"] == "TaskCompleted":
                                __logger.info('calling update task from message for completed task')
                                __update_task_from_message(message, "COMPLETED")

                                __logger.info('calling publish_fanout_message')
                                __fan_out_message(message, "COMPLETED")

                            # Mark Task as Failed
                            if message["event_name"] == "TaskFailed":
                                __logger.info('calling update task from message for failed task')
                                __update_task_from_message(message, "FAILED")

                                __fan_out_message(message, "FAILED")

                            # Mark Task as Pending. This will retry the task
                            if message["event_name"] == "TaskPending":
                                __logger.info('calling update task from message for failed task')
                                __update_task_from_message(message, "PENDING")
                    except:
                        import traceback
                        __logger.error(traceback.format_exc())

    else:
        print("event is empty! nothing to do")
        return "Success!"
