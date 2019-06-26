# Serverless Workflow Manager
A **lightweight** yet **powerful**, _event driven_ workflow orchestration manager for micro-services.

# Introduction
Micro-services are key components of a cloud native, scalable distributed application. Micro services, by definition 
are independent cohesive blocks that execute _a small but an independent_ part of a larger whole. 

However, from the business perspective, there is a single business goal that has to be accomplished irrespective of the 
number of micro - services employed under the hood or how they are deployed.

Consider the example of fulfilling a food order delivery. There are complex micro services under the hood interacting
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