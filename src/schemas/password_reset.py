from pydantic import BaseModel

class ResetPasswordRequest(BaseModel):
    token: str
    password: str
