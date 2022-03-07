# Serverless Workflow Manager
A **lightweight** yet **powerful**, _event driven_ workflow orchestration manager for micro-services.

It is fault tolerant, horizontally scalable &amp; deployable as microservice. It has already powered more than a million workflows and has been open sourced under MIT License.                                    
                                               
# Key Features
1. Ability to *declaratively* author business workflows for distributed micro-services, including Human in the loop approvals.
2. Enables modeling of any complex inter-service dependency with ease, with an additional benefit of providing versioning and audit trail.
3. All the events processed are persisted in a separate collection, making the entire workflow **observable** and **auditable**.  
4. Ability to __replay__ events for a specific stage or task multiple times when required. I.e. the workflow can be __resumed__ at any point in time.
5. Uses AWS Simple Queue Service (Amazon SQS), a fully managed message queuing service that makes it easy to decouple and scale micro-services.

# Underlying Concepts

## Workflow Template

The workflow manager uses a JSON based workflow template to acquire an orchestration plan. The workflow template is 
conceptually organized as a __series of stages__, with each stage containing one or many __tasks__.

> A task is a micro - service that is responsible for executing the intended business logic and maintain state.

> A task may have to wait for one or more tasks to complete before it can start. 

> A stage provides a logical separation between certain groups of tasks.

> The execution of stages is strictly serial. I.e. until a stage is completed, the workflow manager does not move to the next stage.

> The workflow manager controls when a task is scheduled through dependency resolution from the workflow template

> Each task receives instructions to start execution through a specific designated queue, which is configured in the template

> A task can be of type HUMAN or SERVICE. For workflow manager, it does not make a difference. It just schedules
the task. One can write independent module for handling human tasks as per the requirements.

Consider the example of a pizza delivery workflow. The different stages and tasks involved can be pictorially depicted as follows:
 ![Food delivery workflow](/images/food_delivery_workflow_revised.png)
 
The following are the significant points from this image:
- The tasks to be executed are contained in specific stages. This enables a simple but robust way to control execution for a _group of tasks_.
For example, Make food task __will never get executed__ until the (ingredients) availability is confirmed from the restaurant.
- There are some tasks that may execute independently & there may be some tasks that are dependent on completion of certain other task(s)

The workflow template for this image will look as follows:
```json
{  
    "workflow_name" : "Deliver Pizza", 
    "component_name" : "ITALIAN", 
    "stages" : [
        {
            "stage_name" : "START", 
            "stage_order" : 0.0
        }, 
        {
            "stage_name" : "ORDER", 
            "stage_order" : 1.0, 
            "tasks" : [
                {
                    "task_name" : "confirm_order", 
                    "parent_task" : [], 
                    "task_queue" : "confirm_order_queue", 
                    "task_type" : "SERVICE", 
                    "business_status" : "ORDER CONFIRMED"
                }
            ]
        }, 
        {
            "stage_name" : "PREPARE", 
            "stage_order" : 2.0, 
            "tasks" : [
                {
                    "task_name" : "make_food", 
                    "parent_task" : [], 
                    "task_type" : "SERVICE", 
                    "task_queue" : "make_food_queue"
                }, 
                {
                    "task_name" : "assign_executive", 
                    "parent_task" : [], 
                    "task_queue" : "assign_executive_queue", 
                    "task_type" : "SERVICE"
                }, 
                {
                    "task_name" : "confirm_delivery", 
                    "parent_task" : [
                        "make_food", 
                        "assign_executive"
                    ], 
                    "task_queue" : "confirm_delivery_queue", 
                    "task_type" : "SERVICE", 
                    "business_status" : "FOOD ON THE WAY"
                }
            ]
        }, 
        {
            "stage_name" : "DELIVER", 
            "stage_order" : 3.0, 
            "tasks" : [
                {
                    "task_name" : "deliver_food", 
                    "parent_task" : [], 
                    "task_type" : "HUMAN", 
                    "task_queue" : "deliver_food_queue", 
                    "assigned_to" : "delivery_executive", 
                    "business_status" : "FOOD DELIVERED"
                }
            ]
        }
    ]
}
```

> The workflow JSON template allows you to model any complex workflow using the above concepts of stage segregation & tasks dependencies.    

> Modeling the workflow template as a JSON provides additional flexibility to pack in fields which are required by the task.
 - For example, in the above JSON template, deliver_food task contains an additional field assigned_to, which specifies
the specific roles which can complete this human task. The human task implementation may use this field to enforce access control. 
 - You may also want to notify customer when the last task of a stage gets completed.
The JSON template allows you extend the core workflow scheduling to suit your needs.

## Workflow Instance

The workflow manager persists and tracks the current state of the workflow (i.e. the workflow instance) in a separate database collection. 
This enables another retry component to either retry a specific task (or) replay the entire workflow in a standard way.

For example, in the case of the pizza delivery workflow depicted above, let us say that the order has been confirmed and the PREPARE stage is currently active.

Under PREPARE stage, make_food and assign_executive tasks will be scheduled simultaneously.

The workflow instance will look as follows:
```json
{  
    "business_ref_no" : "ORDER-001", 
    "component_name" : "ITALIAN", 
    "stages" : [
        {
            "stage_name" : "START", 
            "stage_order" : 0.0, 
            "status" : "COMPLETED"
        }, 
        {
            "stage_name" : "ORDER", 
            "stage_order" : 1.0, 
            "tasks" : [
                {
                    "task_name" : "confirm_order", 
                    "parent_task" : [], 
                    "task_queue" : "confirm_order_queue", 
                    "task_type" : "SERVICE", 
                    "business_status" : "ORDER CONFIRMED", 
                    "status" : "COMPLETED", 
                    "reason" : "", 
                    "last_updated_time_pretty" : "Fri Jun 28 10:45:41 2019"
                }
            ], 
            "status" : "COMPLETED"
        }, 
        {
            "stage_name" : "PREPARE", 
            "stage_order" : 2.0, 
            "tasks" : [
                {
                    "task_name" : "make_food", 
                    "parent_task" : [], 
                    "task_type" : "SERVICE", 
                    "task_queue" : "make_food_queue", 
                    "status" : "SCHEDULED", 
                    "reason" : null, 
                    "last_updated_time_pretty" : "Fri Jun 28 10:45:42 2019"
                }, 
                {
                    "task_name" : "assign_executive", 
                    "parent_task" : [], 
                    "task_queue" : "assign_executive_queue", 
                    "task_type" : "SERVICE", 
                    "status" : "SCHEDULED", 
                    "reason" : null, 
                    "last_updated_time_pretty" : "Fri Jun 28 10:45:42 2019"
                }, 
                {
                    "task_name" : "confirm_delivery", 
                    "parent_task" : [
                        "make_food", 
                        "assign_executive"
                    ], 
                    "task_queue" : "confirm_delivery_queue", 
                    "task_type" : "SERVICE", 
                    "business_status" : "FOOD ON THE WAY", 
                    "status" : "PENDING"
                }
            ], 
            "status" : "ACTIVE"
        }, 
        {
            "stage_name" : "DELIVER", 
            "stage_order" : 3.0, 
            "tasks" : [
                {
                    "task_name" : "deliver_food", 
                    "parent_task" : [], 
                    "task_type" : "HUMAN", 
                    "task_queue" : "deliver_food_queue", 
                    "assigned_to" : "delivery_executive", 
                    "business_status" : "FOOD DELIVERED", 
                    "status" : "PENDING"
                }
            ], 
            "status" : "NOT STARTED"
        }
    ], 
    "version" : 18, 
    "workflow_name" : "Deliver Pizza", 
    "updated_at" : "2019-06-28T10:45:43.012+0000"
}
```

> The retry manager can be implemented for specific micro - services as per the needs. The retry manager may also track the number of
retries done for a task and implement exponential back-off etc.

> Since the workflow instance contains the current state of the business flow, it can be used in the front-end to visualise and monitor business flows.

## Workflow events

The workflow manager listens to a specific queue onto which other components communicate through events, as follows.

| Event Name| Description|
| :-------: | :--------: |
| StartWorkflow | This event is sent by an API Service to start a workflow. Upon receiving this event, the workflow manager creates a workflow instance and schedules the tasks|
| TaskCompleted | This event is sent by a micro - service task to signal that the scheduled work has been completed. Upon receiving this event, the workflow manager looks for next set of tasks to schedule, if any. The workflow manager also advances the stages, if required. If all the tasks under all the stages are completed, the workflow is considered closed.|
| TaskFailed | This event is sent by a micro - service task to signal that the task has failed. Upon receiving this event, the workflow manager just persists this status to the workflow instance. A separate re-trier component may be implemented to functionally handle the retries of this task.|     
| TaskPending | This event is sent by a re-trier task to reschedule a task. Upon receiving this event, thw workflow manager reschedules this task.|


![Food delivery workflow](/images/workflow_events.png)

### Workflow event samples

#### StartWorkflow
```json
{
    "business_ref_no" : "ORDER-001", 
    "component_name" : "ITALIAN", 
    "event_name": "StartWorkflow"
}
```

#### Payload from Workflow when a Task is scheduled
```json
{
    "business_ref_no": "ORDER-001",
    "component_name": "ITALIAN",
    "event_name": "StartTask",
    "stage_name": "ORDER",
    "task_name": "confirm_order",
    "task_type": "SERVICE"
}
```

> If a task contains additional fields configured in the workflow template, the workflow manager will pack them in this payload.

#### TaskCompleted signal from Task
```json
{
    "business_ref_no": "ORDER-001",
    "component_name": "ITALIAN",
    "event_name": "TaskCompleted",
    "stage_name": "ORDER",
    "task_name": "confirm_order",
    "task_type": "SERVICE"
}
```

#### TaskFailed signal from Task
```json
{
    "business_ref_no": "ORDER-001",
    "component_name": "ITALIAN",
    "event_name": "TaskPending",
    "stage_name": "ORDER",
    "task_name": "confirm_order",
    "task_type": "SERVICE"
}
```

#### TaskPending signal from Retry manager
```json
{
    "business_ref_no": "ORDER-001",
    "component_name": "ITALIAN",
    "event_name": "TaskPending",
    "stage_name": "ORDER",
    "task_name": "confirm_order",
    "task_type": "SERVICE"
}
```

# Deployment

### Pre-requisites

#### Database
1. The workflow templates must be stored in a MongoDB database. You can specify the database name under config.ini against the key **workflow_db**

|Key Name|Value|
|:------:|:---:|
|db_url|URI of the MongoDB Database|
|user_name|User name to login to the database|
|password|Password to login to the database|

#### AWS
1. Create a secret name prod/DBAuthentication with the following key value pairs to point to the rules database
2. Specify the correct aws credentials profile name against the key **profile_name** under config.ini
3. The workflow manager uses AWS SQS as a trigger event source. Ensure that correct _event_source_ _arn_ is configured under zappa_settings.json  
4. Ensure that the SQS queues that are referred to in the workflow template are configured under AWS SQS console. 

### Deploy instructions
1. Clone or download the project into your local repository.
2. Create a virtual environment with Python 3.6 or above and activate the same.
3. To deploy this as a FaaS through [AWS Lambda](https://aws.amazon.com/lambda/), use [Zappa](https://www.zappa.io/), a framework for Serverless Python Web Services - Powered by AWS Lambda and API Gateway
    - Modify the configuration under zappa_settings.json ans change the parameters appropriately before initiating a deploy. 

# Reliability considerations

## Database

1. Due to the inherent stateless nature of AWS Lambda service, there is no guarantee that the Lambda preserves database connections across different invocations. You may want to consider deplying workflow manager under _Elastic Container Service (Fargate)_ if you are looking at having _one instance always available_, with options for auto-scaling.
2. Ensure that the workflow manager deployed as a lambda uses only a specific number of **reserved concurrency** under AWS Lambda console, depending on the size of the MongoDB instance.
3. Ensure that unique index is created on business_ref_no, stages.stage_name and tasks.task_name on workflow instance collection for optimal performance.
4. You may want to purge old workflow instances as the size grows.
