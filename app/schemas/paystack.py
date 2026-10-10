from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class PaystackCustomer(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[int] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class PaystackTransaction(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    reference: str
    status: str
    amount: int
    currency: str
    paid_at: Optional[str] = None
    customer: Optional[PaystackCustomer] = None
    metadata: Optional[Any] = None


class VerifyResponse(BaseModel):
    status: bool
    message: str
    data: Optional[PaystackTransaction] = None
