# Serverless Workflow Manager
A **lightweight** yet **powerful**, _event driven_ workflow orchestration manager for micro-services.

# Key Features
1. Ability to *declaratively* author business workflows for distributed micro-services.
2. Supports easy modeling of complex dependencies across micro-services.
3. All the events processed are persisted in a separate collection, making the entire workflow **observable** and **auditable**.  
4. Ability to __replay__ events for a specific stage or task multiple times when required. I.e. the workflow can be __resumed__ at any point in time.
5. Uses AWS Simple Queue Service (Amazon SQS), a fully managed message queuing service that makes it easy to decouple and scale micro-services.
7. The workflow manager is server less! - perfect for hosting it as an independent micro-service.
8. Written in Python 3.6 with minimal requirements. Uses MongoDB as a database backing service. 