from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.mysql import LONGTEXT
from pydantic import BaseModel


# I know str doesn't make sense for some of these columns, but the instruction
# calls for us not to add any validation layer. Thus, str is used for all columns.
class Books(SQLModel, table=True):
    ISBN: str = Field(primary_key=True)
    title: str
    author: str
    description: str
    genre: str
    price: str
    quantity: str
    summary: str | None = Field(default=None, sa_column=Column(LONGTEXT))


class Customers(SQLModel, table=True):
    customer_id: int = Field(primary_key=True)
    userId: str
    name: str
    phone: str
    address: str
    address2: str | None = Field(default=None)
    city: str
    state: str
    zipcode: str


# These are for HTTP request bodies.
class BookRequestBody(BaseModel):
    ISBN: str | int | float | bool
    title: str | int | float | bool
    Author: str | int | float | bool
    description: str | int | float | bool
    genre: str | int | float | bool
    price: str | int | float | bool
    quantity: str | int | float | bool


class CustomerRequestBody(BaseModel):
    userId: str | int | float | bool
    name: str | int | float | bool
    phone: str | int | float | bool
    address: str | int | float | bool
    address2: str | int | float | bool | None = None
    city: str | int | float | bool
    state: str | int | float | bool
    zipcode: str | int | float | bool
