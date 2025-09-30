# filepath: vsls:/app/schemas.py
from pydantic import BaseModel
from typing import List

class LocationBase(BaseModel):
    latitude: float
    longitude: float

class LocationCreate(LocationBase):
    pass

class Location(LocationBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    locations: List[Location] = []

    class Config:
        orm_mode = True