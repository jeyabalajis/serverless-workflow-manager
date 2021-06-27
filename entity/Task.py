from exceptions.WorkflowValueError import WorkflowValueError


class Task:
    SERVICE_TASK = "SERVICE"
    HUMAN_TASK = "HUMAN"

    PENDING_STATUS = "PENDING"
    SCHEDULED_STATUS = "SCHEDULED"
    COMPLETED_STATUS = "COMPLETED"
    FAILED_STATUS = "FAILED"

    def __init__(self, *, task_name: str, task_type: str, parent_tasks: [str], **kwargs):
        self.task_name = task_name
        self.task_type = task_type
        self.parent_tasks = parent_tasks
        self.__validate_task_type()
        self.status = self.PENDING_STATUS
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __validate_task_type(self):
        if self.task_type not in (self.SERVICE_TASK, self.HUMAN_TASK):
            raise WorkflowValueError("task_type must be SERVICE or HUMAN")

    def mark_as_scheduled(self):
        self.status = self.SCHEDULED_STATUS

    def mark_as_completed(self):
        self.status = self.COMPLETED_STATUS

    def mark_as_failed(self):
        self.status = self.FAILED_STATUS

    def set_misc_attributes(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

