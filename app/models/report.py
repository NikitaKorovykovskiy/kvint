from pydantic import BaseModel


class TaskRequest(BaseModel):
    correlation_id: str
    phones: list[int]
