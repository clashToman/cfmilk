from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt, JWTError
import random
from typing import Annotated
from Backend.config import SessionLocal, ALGORITHM, SECRET_KEY
from Backend.schemas.schemas import PhoneRequest, OtpVerification
from Backend.Models.model import (
    User as UserModel,
    Role as RoleModel,
    Customer,
)

router = APIRouter(tags=["Login"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

ADMIN_PHONE = "8148530305"


# ---------------- Database Dependency ---------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict):
    """Generate JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # type: ignore


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # type: ignore
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    payload = decode_token(token)
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/token")
async def Token(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"Token": token}


# ---------------- OTP Login ----------------
@router.post("/login")
async def send_otp(request: PhoneRequest, db: Session = Depends(get_db)):
    phone = request.phone
    otp = random.randint(100000, 999999)
    expiry_time = datetime.utcnow() + timedelta(minutes=10)

    user = db.query(UserModel).filter(UserModel.phone == phone).first()

    # Determine role and username
    if phone == ADMIN_PHONE:
        role = db.query(RoleModel).filter(RoleModel.name == "admin").first()
        username = "Admin"
    elif user:
        role = db.query(RoleModel).filter(RoleModel.id == user.role_id).first()
        username = user.user_name
    else:
        # New customer
        role = db.query(RoleModel).filter(RoleModel.name == "customer").first()
        username = f"user{phone[-4:]}"

    if not role:
        raise HTTPException(status_code=400, detail="Role not found in database")

    if not user:
        last_user = db.query(UserModel).order_by(UserModel.id.desc()).first()
        next_id = 1001 if not last_user else int(last_user.user_id[4:]) + 1  # type:ignore
        user_id = f"user{next_id}"
        user = UserModel(
            user_id=user_id,
            phone=phone,
            user_name=username,
            role_id=role.id,
            otp=otp,
            otp_expiry=expiry_time,
            is_verified=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        if role.name == "customer":  # type:ignore
            existing_customer = (
                db.query(Customer).filter(Customer.user_id == user.user_id).first()
            )
            if not existing_customer:
                new_customer = Customer(
                    user_id=user.user_id,
                    user_name=username,
                    phone=phone,
                    address="",
                    created_at=datetime.utcnow(),
                )
                db.add(new_customer)
                db.commit()

    else:
        user.is_verified = True  # type:ignore
        access_token = create_access_token(
            {"user_id": user.user_id, "role_id": user.role_id}
        )
        db.commit()

        return {
            "verified": True,
            "user_name": user.user_name,
            "user_id": user.user_id,
            "role_id": user.role_id,
            "access_token": access_token,
            "token_type": "bearer",
        }

    print(f"[{role.name.upper()} OTP] Phone: {phone}, OTP: {otp}")
    return {"message": f"OTP sent successfully for {role.name}", "otp": otp}


# ---------------- OTP Verification ----------------
@router.post("/verify-otp")
async def verify_otp(request: OtpVerification, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.phone == request.phone).first()

    if not user or user.otp != request.otp or user.otp_expiry < datetime.utcnow():  # type:ignore
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user.is_verified = True  # type:ignore
    user.otp = None  # type:ignore
    user.otp_expiry = None  # type:ignore
    db.commit()

    access_token = create_access_token(
        {"user_id": user.user_id, "role_id": user.role_id}
    )

    role = db.query(RoleModel).filter(RoleModel.id == user.role_id).first()

    return {
        "verified": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "role_id": user.role_id,
        "role_name": role.name if role else "unknown",
        "message": f"{role.name.capitalize() if role else 'User'} verified successfully",
    }
