from Consts import ErrorCode


class BusinessException(Exception):
    """业务逻辑异常，用于表示业务规则违反等可预期的错误"""

    def __init__(self, error_code: ErrorCode, message: str = ""):
        self.error_code = error_code
        self.message = message
        super().__init__(self.message or f"Business error: {error_code.name}")
