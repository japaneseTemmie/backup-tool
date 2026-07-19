class Error:
    def __init__(self, msg: str, exc: Exception | None=None) -> None:
        self.msg = msg
        self.exc = exc
