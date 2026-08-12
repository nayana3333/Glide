from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str
    phone: str
    password: str = Field(min_length=6)
    archetype: str = Field(description="full_time_driver | part_time_delivery | multi_platform")
    platform: str
    demo_worker_id: int | None = Field(
        default=None,
        description="Optional: seed this account with a synthetic worker's earnings history for demo purposes",
    )


class LoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    phone: str
    archetype: str
    platform: str

    class Config:
        from_attributes = True
