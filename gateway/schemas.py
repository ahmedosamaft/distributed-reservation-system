from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class BookingCreate(BaseModel):
    user_id: int
    slot_id: str