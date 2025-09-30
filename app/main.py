from fastapi import FastAPI
from app.database import engine, Base
from app import users
from app import locations, models

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users.router)
app.include_router(locations.router)

@app.get("/")
def read_root():
    return {"message": "Hello World", "status": "Backend is working!"}

