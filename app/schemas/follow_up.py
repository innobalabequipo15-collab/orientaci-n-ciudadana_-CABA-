from pydantic import BaseModel, Field


class FollowUpRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000, examples=["¿Qué documentos necesito?"])


class FollowUpResponse(BaseModel):
    follow_up_id: str
    consultation_id: str
    question: str
    answer: str
    message: str | None = None
