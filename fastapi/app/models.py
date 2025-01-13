from pydantic import BaseModel
from typing import List, Optional

class Item(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: float
    quantity: int

class User(BaseModel):
    id: str
    username: str
    email: str

class Order(BaseModel):
    id: str
    user_id: str
    items: List[Item]
    total_price: float