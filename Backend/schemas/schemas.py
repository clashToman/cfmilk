from pydantic import BaseModel, Field
from typing import Literal, Optional


class PhoneRequest(BaseModel):
    phone: str


class OtpVerification(BaseModel):
    phone: str = Field(min_length=10, max_length=15)
    otp: int


class CreateUserRequest(BaseModel):
    user_name: str = Field(min_length=3, max_length=50, pattern="^[a-zA-Z]")
    phone: str = Field(min_length=10, max_length=15)
    role_name: str = Literal["customer", "supplier", "delivery"]  # type: ignore


class CreateCategoryRequest(BaseModel):
    category_name: str = Field(min_length=3, max_length=50, pattern="^[a-zA-Z]")
    description: str
    status: bool = True


class CreateProductRequest(BaseModel):
    product_name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    price: float
    unit: str
    stock: int = 0
    category_name: str
    supplier_id: Optional[int] = None
    image_url: Optional[str] = None
    status: bool = True


class UpdateProductStockRequest(BaseModel):
    product_name: str
    new_stock: int


class CustomerUpdate(BaseModel):
    user_name: Optional[str] = None
    phone: Optional[str] = None
    address: dict | None = None

    class Config:
        orm_mode = True


class CustomerResponse(BaseModel):
    user_name: str
    phone: str
    address: Optional[str] = None

    class Config:
        orm_mode = True


class CustomerOrders(BaseModel):
    name: str
    quantity: int
