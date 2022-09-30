# Serverless Workflow Manager

A **lightweight** yet **powerful**, _event driven_ workflow orchestration manager for micro-services. The workflow manager is built using [hexagonal architecture](https://netflixtechblog.com/ready-for-changes-with-hexagonal-architecture-b315ec967749)).

It is fault tolerant, horizontally scalable &amp; deployable as microservice. It has already powered more than a million workflows and has been open sourced under MIT License.                    

# Build Status

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/jeyabalajis/serverless-workflow-manager/tree/master.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/jeyabalajis/serverless-workflow-manager/tree/master)
                                               
# Key Features
1. Ability to *declaratively* author business workflows for distributed micro-services, including Human in the loop approvals.
2. Enables modeling of any complex inter-service dependency with ease, with an additional benefit of providing versioning and audit trail.
3. All the events processed are persisted in a separate collection, making the entire workflow **observable** and **auditable**.  
4. Ability to __replay__ events for a specific stage or task multiple times when required. I.e. the workflow can be __resumed__ at any point in time.

> The workflow manager is built based on [Onion Architecture](https://www.codeguru.com/csharp/understanding-onion-architecture/). The Message Queue handle and Database Repositories are injected into workflow manager, thus making the workflow manager [persistence ignorant](https://deviq.com/persistence-ignorance/) and [infrastructure ignorant](https://ayende.com/blog/3137/infrastructure-ignorance) 

# Source Code

[GitHub Repository](https://github.com/jeyabalajis/serverless-workflow-manager)

# Underlying Concepts

## Workflow State Machine

The workflow manager uses a workflow state machine template to acquire an orchestration plan. Here are the business rules for the workflow:

- A workflow is composed of multiple stages.
- A stage provides a logical separation between certain groups of tasks.
- The execution of stages is strictly serial. I.e. until a stage is completed, the workflow manager does not move to the next stage.
- A stage is composed of a set of tasks. A stage is not marked as complete until all tasks are completed.
- A task is a service that is responsible for executing some business logic. 
- Workflow is agnostic of the task. For the workflow, **message queue acts as an interface for the task**. The underlying implementation resides somewhere else.  
- A task can be of type HUMAN or SERVICE. For workflow manager, it does not make a difference. It just schedules the task.
- A task may be independent (or) dependent on multiple other tasks. Workflow manager does not schedule a dependent task until it's parent tasks are completed.  
- Workflow manager receives an event that specifies whether a task has been completed or failed. 
- Upon receiving this event, workflow manager advances the workflow state machine (i.e. a stage is marked complete & next stage is activated, tasks are scheduled etc.)

Consider the example of a pizza delivery workflow. The different stages and tasks involved can be pictorially depicted as follows:
 ![Food delivery workflow](/images/food_delivery_workflow_revised.png)
 
The workflow template for this image can be represented as a json as follows:
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

## Workflow Persistence

The workflow manager persists and tracks the current state of the workflow (i.e. the workflow instance) in a separate database collection.

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
