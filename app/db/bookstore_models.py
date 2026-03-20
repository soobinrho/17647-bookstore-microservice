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
    ISBN: str
    title: str
    author: str
    description: str
    genre: str
    price: str
    quantity: str


class CustomerRequestBody(BaseModel):
    userId: str
    name: str
    phone: str
    address: str
    address2: str | None = None
    city: str
    state: str
    zipcode: str
