from fastapi import FastAPI
from Backend.config import engine, Base, SessionLocal
from Backend.Routes.auth import router
from Backend.Routes.admin import admin_router
from Backend.Routes.customer import customer_router
from Backend.Models.model import Role

app = FastAPI()


# Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    roles = [
        {"name": "admin", "description": "Administrator with full access"},
        {"name": "supplier", "description": "Supplier who provides milk products"},
        {"name": "delivery", "description": "Delivery person who delivers orders"},
        {"name": "customer", "description": "Customer who buys products"},
    ]
    for role in roles:
        exists = db.query(Role).filter(Role.name == role["name"]).first()
        if not exists:
            db.add(Role(**role))
    db.commit()
    db.close()


app.include_router(router)
app.include_router(admin_router)
app.include_router(customer_router)


@app.get("/")
def Root():
    return {"Hello Buddy....!"}
