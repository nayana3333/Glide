from pydantic import BaseModel, Field


class BufferAmount(BaseModel):
    amount: float = Field(gt=0)


class BufferTransactionResponse(BaseModel):
    id: int
    week_start: str
    kind: str
    amount: float
    balance_after: float

    class Config:
        from_attributes = True


class BufferStateResponse(BaseModel):
    balance: float
    transactions: list[BufferTransactionResponse]
