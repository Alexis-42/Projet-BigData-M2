from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

class Item(BaseModel):
    id: str
    name: str
    description: str

items_db = []

@router.post("/items/", response_model=Item)
def create_item(item: Item):
    items_db.append(item)
    return item

@router.get("/items/", response_model=List[Item])
def read_items():
    return items_db

@router.get("/items/{item_id}", response_model=Item)
def read_item(item_id: str):
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")