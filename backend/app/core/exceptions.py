from fastapi import HTTPException, status

class AppException(HTTPException):
    def __init__(self, detail: str, code: str = "APP_ERROR", status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail={"code": code, "message": detail})

class BusinessException(AppException):
    def __init__(self, detail: str, code: str = "BUSINESS_ERROR", status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail, code=code)

class BusinessValidationException(BusinessException):
    def __init__(self, detail: str, code: str = "VALIDATION_ERROR"):
        super().__init__(detail=detail, code=code, status_code=status.HTTP_400_BAD_REQUEST)

class NotFoundException(BusinessException):
    def __init__(self, entity_or_msg: str, identifier: any = None):
        if identifier is not None:
            detail = f"{entity_or_msg} with identifier '{identifier}' not found."
        else:
            detail = entity_or_msg
        super().__init__(
            detail=detail,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )

class DuplicateRecordException(BusinessException):
    def __init__(self, entity: str, field: str, value: any):
        super().__init__(
            detail=f"{entity} with {field} '{value}' already exists.",
            code="DUPLICATE_RECORD",
            status_code=status.HTTP_409_CONFLICT
        )

class WorkflowPermissionException(BusinessException):
    def __init__(self, action: str, current_role: str, required_roles: list[str]):
        super().__init__(
            detail=f"Role '{current_role}' is not authorized to perform workflow action '{action}'. Required roles: {', '.join(required_roles)}.",
            code="WORKFLOW_ACCESS_DENIED",
            status_code=status.HTTP_403_FORBIDDEN
        )

class InvalidStateTransitionException(BusinessException):
    def __init__(self, current_state: str, attempted_action: str):
        super().__init__(
            detail=f"Cannot perform action '{attempted_action}' while entity is in state '{current_state}'.",
            code="INVALID_STATE_TRANSITION",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

