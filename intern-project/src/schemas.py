from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class RegisterRequest(BaseModel):
    email:str
    password: str = Field(min_length=6)

class LoginRequest(BaseModel):
    email:str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id : int
    email: str
    created_at: datetime

class TicketCreate(BaseModel):
    message: str = Field(min_length=1)

class DecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    action: str
    reason: str
    confidence: float
    sources: list[str]
    created_at: datetime


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    message: str
    created_at: datetime
    decision: DecisionResponse | None = None