from pydantic import BaseModel


class GraphRequest(BaseModel):
    thread_id: str
    message: str | None = None


class GraphResponse(BaseModel):
    message: str
    thread_id: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str

