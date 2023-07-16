from pydantic import BaseModel


class Item(BaseModel):
    name: str
    price: int
    quantity: int


class User(BaseModel):
    name: str
    address: str
