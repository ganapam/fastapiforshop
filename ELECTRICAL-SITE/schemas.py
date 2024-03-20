from pydantic import BaseModel
from fastapi import UploadFile
from typing import Optional
from datetime import datetime
class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AdminLogin(BaseModel):
    username: str
    password: str
class CursoleSchema(BaseModel):
    id: int
    filename: str
    data: bytes
    position: int
class ProductSchema(BaseModel):
    id: int
    filename: str
    data: bytes
    position: int
class WireSchema(BaseModel):
    id: int
    filename: str
    data: bytes
    position: int
    Price:str
class PipesSchema(BaseModel):
    id: int
    filename: str
    data: bytes
    position: int
    Price:str
class WaterpipesSchema(BaseModel):
    id: int
    filename: str
    data: bytes
    position: int
    Price:str
class BlubsSchema(BaseModel):
    id: int
    filename: str
    data: bytes
    position: int
    Price:str
class PlastictapsSchema(BaseModel):
    id: int
    filename: str
    data: bytes
    position: int
    Price:str
class ShopStatus(BaseModel):
    status: bool
    updated_at: datetime
    message: Optional[str] = None
class ShopStatusUpdate(BaseModel):
    status: bool
class ContactBase(BaseModel):
    name: str
    email: str
    message: str

# Pydantic Schema for input validation
class ContactCreate(ContactBase):
    pass

# Pydantic Schema for output validation
class Contact(ContactBase):
    id: int

    class Config:
        orm_mode = True
class NewsBase(BaseModel):
    title: str
    content: str
    uploadfile: bytes
    date: datetime
    position_id: int

class NewsGet(BaseModel):
    id: int
    title: str
    content: str
    uploadfile: bytes  # Ensure that uploadfile is handled as bytes
    date: datetime
    position_id: int


class NewsGet(NewsBase):
    id: int

    class Config:
        orm_mode = True