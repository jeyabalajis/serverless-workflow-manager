# Serverless Workflow Manager
A **lightweight** yet **powerful**, _event driven_ workflow orchestration manager for micro-services.

# Introduction
Micro-services are key building blocks of a cloud native, scalable distributed application. They are, by definition, 
independent cohesive components that execute _a small but an independent_ part of a larger whole. 

However, from a business perspective, there is a single business goal that has to be accomplished irrespective of the 
number of micro - services employed under the hood or how they are deployed.

Consider the example of fulfilling a food order. There are a number of complex micro services under the hood interacting
with each other, coupled with human interactions. But the singular business objective in this case is to deliver the food on time.  

A work-queue based scheduler agent supervisor pattern (https://docs.microsoft.com/en-us/azure/architecture/patterns/scheduler-agent-supervisor) 
is a robust way to __coordinate__ a series of distributed actions as a __single operation__.

_Serverless Workflow Manager_ is an implementation of this pattern. There are two significant features that 
set apart this implementation:

- The workflow manager is built as a server less service. Hence, it can be deployed as an independent
_scalable_ micro - service. With this, the workflow manager __does not__ become a single point of failure.
- The workflow manager uses a simple, yet powerful workflow authoring template with which any complex service dependency can be modeled with ease.
With this powerful template, the workflows can be authored or modified easily, with an additional benefit of audit trail of changes.

The workflow authoring template also allows you to visualize the current state of the workflow in the front-end, thus providing an excellent way to monitor and control the flow.          

# Key Features
1. Ability to *declaratively* author business workflows for distributed micro-services.
2. Supports easy modeling of complex dependencies across micro-services.
3. All the events processed are persisted in a separate collection, making the entire workflow **observable** and **auditable**.  
4. Ability to __replay__ events for a specific stage or task multiple times when required. I.e. the workflow can be __resumed__ at any point in time.
5. Uses AWS Simple Queue Service (Amazon SQS), a fully managed message queuing service that makes it easy to decouple and scale micro-services.
7. The workflow manager is server less! - perfect for hosting it as an independent micro-service.
8. Written in Python 3.6 with minimal requirements. Uses MongoDB as a database backing service. 

# Underlying Concepts

## Workflow Template

The workflow manager uses a JSON based workflow template to acquire an orchestration plan. The workflow template is 
conceptually organized as a __series of stages__, with each stage containing one or many __tasks__.

> A task is a micro - service that is responsible for executing the intended business logic and maintain state.

> A task may have to wait for one or more tasks to complete before it can start. 

> A stage provides a logical separation between certain groups of tasks.
   
1. The execution of stages is strictly serial. I.e. until a stage is completed, the workflow manager does not move to the next stage.
2. The tasks under a stage can be configured either as independent tasks (or) dependent tasks.
3. A task can be dependent on more than one task. In this case, the workflow manager waits for all the dependent tasks 
to be completed before it executes this task.
4. A task can be of type HUMAN or SERVICE. For workflow manager, it does not make a difference. It just schedules
the task. One can write independent module for handling human tasks as per the requirements.

Consider the example of a pizza delivery workflow. The different stages and tasks involved can be pictorially depicted as follows:
 ![Food delivery workflow](/images/food_delivery_workflow_revised.png)
 
The following are the significant points from this image:
- The tasks to be executed are contained in specific stages. This enables a simple but robust way to control when some tasks are executed.
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
the specific roles which can complete this human task. 
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

## Workflow events

The workflow manager communicates with the outside world through a specific set of events, as follows.

| Event Name| Description|
| :-------: | :--------: |
| StartWorkflow | This event is sent by an API Service to start a workflow. Upon receiving this event, the workflow manager creates a workflow instance and schedules the tasks|
| TaskCompleted | This event is sent by a micro - service task to signal that the scheduled work has been completed. Upon receiving this event, the workflow manager looks for next set of tasks to schedule, if any. The workflow manager also advances the stages, if required. If all the tasks under all the stages are completed, the workflow is considered closed.|
| TaskFailed | This event is sent by a micro - service task to signal that the task has failed. Upon receiving this event, the workflow manager just persists this status to the workflow instance. A separate re-trier component may be implemented to functionally handle the retries of this task.|     
| TaskPending | This event is sent by a re-trier task to reschedule a task. Upon receiving this event, thw workflow manager reschedules this task.|

The workflow manager listens to a specific queue onto which other components communicate with events.

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