from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from Backend.schemas.schemas import CustomerUpdate, CustomerResponse, CustomerOrders
from Backend.Models.model import User as UserModel, Customer, Product, Order
from Backend.config import SessionLocal
from Backend.Routes.auth import get_current_user


customer_router = APIRouter(prefix="/customer", tags=["Customer"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@customer_router.get("/profile", response_model=CustomerResponse)
async def get_customer_profile(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    customer = (
        db.query(Customer).filter(Customer.user_id == current_user.user_id).first()
    )

    if not customer:
        raise HTTPException(status_code=404, detail="Customer profile not found")

    return customer


@customer_router.put("/profile", response_model=CustomerResponse)
def update_customer_profile(
    cust_upt: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    user = db.query(UserModel).filter(UserModel.user_id == current_user.user_id).first()
    customer = (
        db.query(Customer).filter(Customer.user_id == current_user.user_id).first()
    )

    if not user or not customer:
        raise HTTPException(status_code=404, detail="User or Customer not found")

    update_data = cust_upt.dict(exclude_unset=True)

    # Update User
    if "user_name" in update_data:
        user.user_name = update_data["user_name"]
        customer.user_name = update_data["user_name"]

    # Update Customer
    if "phone" in update_data:
        customer.phone = update_data["phone"]
    if "address" in update_data:
        customer.address = update_data["address"]

    user.updated_at = datetime.utcnow()  # type: ignore
    customer.updated_at = datetime.utcnow()  # type: ignore

    db.commit()
    db.refresh(user)
    db.refresh(customer)

    return CustomerResponse(
        user_name=user.user_name,  # type:ignore
        phone=customer.phone,  # type:ignore
        address=customer.address,  # type:ignore
    )


@customer_router.get("/products")
async def list_products(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    products = db.query(Product).filter(Product.status == 1).all()
    return {"products": products}


@customer_router.post("/order")
async def place_order(
    order: CustomerOrders,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    # Check if product exists
    product = db.query(Product).filter(Product.name == order.name).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check stock availability
    if product.stock < order.quantity:  # type: ignore
        raise HTTPException(status_code=400, detail="Insufficient stock available")

    # Calculate total amount
    total_amount = float(product.price) * order.quantity  # type: ignore

    # Create order entry
    new_order = Order(
        customer_id=current_user.user_id,
        product_id=product.product_id,
        unit=str(order.quantity),
        total_amount=total_amount,
        status="Pending",
        payment_status="Pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(new_order)

    # Reduce stock
    product.stock -= order.quantity  # type: ignore

    db.commit()
    db.refresh(new_order)
    db.refresh(product)

    return {
        "message": f"Order placed successfully for {order.quantity} x {product.name}",
        "order_id": new_order.id,
        "total_amount": total_amount,
        "remaining_stock": product.stock,
        "status": new_order.status,
    }


@customer_router.get("/orders")
async def get_customer_orders(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    orders = db.query(Order).filter(Order.customer_id == current_user.user_id).all()

    return {"orders": orders}
