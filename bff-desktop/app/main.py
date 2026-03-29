from fastapi import FastAPI, status, Response, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlmodel import Session, SQLModel, create_engine, select
from app.shared_library.models import (
    Books,
    Customers,
    BookRequestBody,
    CustomerRequestBody,
)
from app.shared_library.input_data_validations import (
    check_is_valid_price,
    check_is_valid_email,
    check_is_valid_quantity,
    check_is_valid_state_abbr,
)
import os


# ============================================
# FastAPI Automatic API Documentation Metadata
# ============================================
# Reference: https://fastapi.tiangolo.com/tutorial/metadata/
description = """
## Bookstore BFF (Backend For Frontend) for Desktop

Reference: https://github.com/soobinrho/17647-bookstore-microservice

<br>
"""

tags_metadata = [
    {
        "name": "books",
        "description": "RESTful API's for books data.",
    },
    {
        "name": "customers",
        "description": "RESTful API's for customers data.",
    },
    {
        "name": "uncategorized",
        "description": "Other API endpoints.",
    },
]

app = FastAPI(
    title="Bookstore BFF (Backend For Frontend) for Desktop",
    description=description,
    contact={
        "name": "Soobin Rho",
        "url": "https://github.com/soobinrho",
        "email": "soobinrho@gmail.com",
    },
)


# ================
# Helper Functions
# ================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # By default, FastAPI returns 422. This function switches it to 400 because
    # the assignment requires 400 instead of 422. By the way, I observed that there's a bug
    # in the automatic API documentation page in which it still shows up as 422.
    # Source: https://stackoverflow.com/a/75958273
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors()},
    )


# =====
# Books
# =====
@app.post("/books", tags=["books"], status_code=status.HTTP_201_CREATED)
async def post_books(
    book_request_body: BookRequestBody, background_tasks: BackgroundTasks
):
    if not check_is_valid_price(book_request_body.price):
        return RESPONSE_INVALID_PRICE

    if not check_is_valid_quantity(book_request_body.quantity):
        return RESPONSE_INVALID_QUANTITY

    if check_does_ISBN_exist(book_request_body.ISBN):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"message": "This ISBN already exists in the system."},
        )

    book = Books(
        ISBN=book_request_body.ISBN,
        title=book_request_body.title,
        author=book_request_body.Author,
        description=book_request_body.description,
        genre=book_request_body.genre,
        price=book_request_body.price,
        quantity=book_request_body.quantity,
    )
    create_book(book)
    book = get_book_by_ISBN(book_request_body.ISBN)
    background_tasks.add_task(
        background_task_generate_summary, book.title, book.author, book.ISBN
    )
    return {
        "ISBN": str(book.ISBN),
        "title": str(book.title),
        "Author": str(book.author),
        "description": str(book.description),
        "genre": str(book.genre),
        "price": float(book.price),
        "quantity": float(book.quantity),
    }


@app.put("/books/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def put_books(book_request_body: BookRequestBody, ISBN: str | int | float | bool):
    if book_request_body.ISBN != ISBN:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": "Update failed. Different ISBNs in payload and query param."
            },
        )

    if not check_is_valid_price(book_request_body.price):
        return RESPONSE_INVALID_PRICE

    if not check_is_valid_quantity(book_request_body.quantity):
        return RESPONSE_INVALID_QUANTITY

    if not check_does_ISBN_exist(book_request_body.ISBN):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Update failed. This ISBN does not exist."},
        )

    with Session(engine) as session:
        book = session.get(Books, book_request_body.ISBN)
        book.title = book_request_body.title
        book.author = book_request_body.Author
        book.description = book_request_body.description
        book.genre = book_request_body.genre
        book.price = book_request_body.price
        book.quantity = book_request_body.quantity
        session.add(book)
        session.commit()

    book = get_book_by_ISBN(book_request_body.ISBN)
    return {
        "ISBN": str(book.ISBN),
        "title": str(book.title),
        "Author": str(book.author),
        "description": str(book.description),
        "genre": str(book.genre),
        "price": float(book.price),
        "quantity": float(book.quantity),
    }


@app.get("/books/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books(ISBN):
    book = get_book_by_ISBN(ISBN)
    if book is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This ISBN does not exist."},
        )

    book = get_book_by_ISBN(ISBN)
    return {
        "ISBN": str(book.ISBN),
        "title": str(book.title),
        "Author": str(book.author),
        "description": str(book.description),
        "genre": str(book.genre),
        "price": float(book.price),
        "quantity": float(book.quantity),
        "summary": str(book.summary),
    }


@app.get("/books/isbn/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books_duplicate_enpoint(ISBN):
    book = get_book_by_ISBN(ISBN)
    if book is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This ISBN does not exist."},
        )

    book = get_book_by_ISBN(ISBN)
    return {
        "ISBN": str(book.ISBN),
        "title": str(book.title),
        "Author": str(book.author),
        "description": str(book.description),
        "genre": str(book.genre),
        "price": float(book.price),
        "quantity": float(book.quantity),
        "summary": str(book.summary),
    }


# =========
# Customers
# =========
@app.post("/customers", tags=["customers"], status_code=status.HTTP_201_CREATED)
async def post_customers(customer_request_body: CustomerRequestBody):
    if not check_is_valid_email(customer_request_body.userId):
        return RESPONSE_INVALID_EMAIL

    if not check_is_valid_state_abbr(customer_request_body.state):
        return RESPONSE_INVALID_STATE

    if check_does_user_id_exist(customer_request_body.userId):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"message": "This user ID already exists in the system."},
        )

    customer = Customers(
        userId=customer_request_body.userId,
        name=customer_request_body.name,
        phone=customer_request_body.phone,
        address=customer_request_body.address,
        address2=customer_request_body.address2,
        city=customer_request_body.city,
        state=customer_request_body.state,
        zipcode=customer_request_body.zipcode,
    )
    create_customer(customer)
    customer = get_customer_by_userId(customer_request_body.userId)
    return {
        "id": int(customer.customer_id),
        "userId": str(customer.userId),
        "name": str(customer.name),
        "phone": str(customer.phone),
        "address": str(customer.address),
        "address2": str(customer.address2),
        "city": str(customer.city),
        "state": str(customer.state),
        "zipcode": str(customer.zipcode),
    }


@app.get("/customers/{id}", tags=["customers"], status_code=status.HTTP_200_OK)
async def get_customers(id: int):
    customer = get_customer_by_id(id)
    if customer is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This ID does not exist."},
        )

    return {
        "id": int(customer.customer_id),
        "userId": str(customer.userId),
        "name": str(customer.name),
        "phone": str(customer.phone),
        "address": str(customer.address),
        "address2": str(customer.address2),
        "city": str(customer.city),
        "state": str(customer.state),
        "zipcode": str(customer.zipcode),
    }


@app.get("/customers", tags=["customers"], status_code=status.HTTP_200_OK)
async def get_customers_by_userId(userId):
    if not check_is_valid_email(userId):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Retrieval failed. Invalid email."},
        )

    customer = get_customer_by_userId(userId)
    if customer is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This email does not exist."},
        )

    return {
        "id": int(customer.customer_id),
        "userId": str(customer.userId),
        "name": str(customer.name),
        "phone": str(customer.phone),
        "address": str(customer.address),
        "address2": str(customer.address2),
        "city": str(customer.city),
        "state": str(customer.state),
        "zipcode": str(customer.zipcode),
    }


# =============
# Uncategorized
# =============
@app.get(
    "/status",
    tags=["uncategorized"],
    status_code=status.HTTP_200_OK,
)
async def get_status(response: Response):
    return JSONResponse(content="OK", headers={"Content-Type": "text/plain"})
