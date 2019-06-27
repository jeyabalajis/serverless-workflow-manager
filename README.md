# Serverless Workflow Manager
A **lightweight** yet **powerful**, _event driven_ workflow orchestration manager for micro-services.

# Introduction
Micro-services are key building blocks of a cloud native, scalable distributed application. They are, by definition, 
independent cohesive components that execute _a small but an independent_ part of a larger whole. 

However, from a business perspective, there is a single business goal that has to be accomplished irrespective of the 
number of micro - services employed under the hood or how they are deployed.

Consider the example of fulfilling a food order. There are a anumber of complex micro services under the hood interacting
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
1. The execution of stages is strictly serial. I.e. until a stage is completed, the workflow manager does not move to the next stage.
2. The tasks under a stage can be configured either as independent tasks (or) dependent tasks.
3. A task can be dependent on more than one task. In this case, the workflow manager waits for all the dependent tasks 
to be completed before it executes this task.
4. A task can be of type HUMAN or SERVICE. For workflow manager, it does not make a difference. It just schedules
the task. One can write independent module for handling human tasks as per the requirements.

Consider the example of a pizza delivery workflow. The different stages and tasks involved can be pictorially depicted as follows:
 