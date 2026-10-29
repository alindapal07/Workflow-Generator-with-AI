class WorkflowException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class WorkflowNotFoundException(WorkflowException):
    def __init__(self, message: str = "Workflow not found"):
        super().__init__(message=message, status_code=404)

class ExecutionNotFoundException(WorkflowException):
    def __init__(self, message: str = "Execution not found"):
        super().__init__(message=message, status_code=404)

class InvalidWorkflowInputException(WorkflowException):
    def __init__(self, message: str = "Invalid workflow input"):
        super().__init__(message=message, status_code=400)

