from fastapi import FastAPI, status, Response, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlmodel import Session, SQLModel, create_engine, select
from google import genai
from dotenv import load_dotenv, find_dotenv
from .db.bookstore_models import Books, Customers
from .input_data_validations import (
    check_is_valid_price,
    check_is_valid_email,
    check_is_valid_state_abbr,
)
import os


# ======================
# Database Configuration
# ======================
load_dotenv(find_dotenv())
DB_USER = os.environ.get("BOOKSTORE_BACKEND_DB_USER", None)
DB_PASS = os.environ.get("BOOKSTORE_BACKEND_DB_PASS", None)
DB_URL = os.environ.get("BOOKSTORE_BACKEND_DB_URL", None)
engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_URL}/bookstore", echo=False
)
SQLModel.metadata.create_all(engine)

# ============================================
# FastAPI Automatic API Documentation Metadata
# ============================================
# Reference: https://fastapi.tiangolo.com/tutorial/metadata/
description = """
## Bookstore API Backend for Books and Customers

Reference: https://github.com/soobinrho/17647-A1-bookstore-microservice

<br>
"""

tags_metadata = [
    {
        "name": "books",
        "description": "RESTful API's for books.",
    },
    {
        "name": "customers",
        "description": "RESTful API's for customers.",
    },
    {
        "name": "uncategorized",
        "description": "Other API endpoints.",
    },
]

app = FastAPI(
    title="Bookstore API Backend",
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
RESPONSE_INVALID_PRICE = JSONResponse(
    status_code=status.HTTP_400_BAD_REQUEST,
    content={
        "message": "Invalid price. It must be a valid number, and it must have between 0 to 2 decimal places."
    },
)

RESPONSE_INVALID_EMAIL = JSONResponse(
    status_code=status.HTTP_400_BAD_REQUEST,
    content={
        "message": 'Invalid email. It must match the regular expression "[^@]+@[^@]+\\.[^@]+".'
    },
)

RESPONSE_INVALID_STATE = JSONResponse(
    status_code=status.HTTP_400_BAD_REQUEST,
    content={
        "message": "Invalid state. It must be a valid 2-letter U.S. state abbreviation."
    },
)


def get_LLM_book_500_words_summary(title: str, author: str, ISBN: str) -> str:
    # Source: https://github.com/googleapis/python-genai?tab=readme-ov-file#client-context-managers
    try:
        return "TODO: DELTE THIS WHEN COMPLETE"
        with genai.Client() as client:
            prompt = (
                "You're Frank Herbert the author of Dune. I am a huge fan of yours. "
                + f"Please write a 500-words summary of the following book: {title} "
                + f"by the author {author} with ISBN {ISBN}. I don't care if the book "
                + "actually exists or not, so please feel free to make up something "
                + "based on the book name and the book author. Please respond with a "
                + "summary of the book in exactly 500 words."
            )
            summary = (
                client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=prompt,
                )
            ).text
    except Exception as e:
        summary = f"Gemini API returned the following error:\n{e}"

    return summary


def create_book(book: Books) -> None:
    with Session(engine) as session:
        session.add(book)
        session.commit()


def create_customer(customer: Customers) -> None:
    with Session(engine) as session:
        session.add(customer)
        session.commit()


def check_does_ISBN_exist(ISBN: str) -> bool:
    with Session(engine) as session:
        book = session.get(Books, ISBN)
        return book is not None


# NOTE: Customer ID is the numeric, autoincrementing ID, while User ID is the email.
def check_does_customer_id_exist(id: str) -> bool:
    with Session(engine) as session:
        customer = session.get(Customers, id)
        return customer is not None


def check_does_user_id_exist(userId: str) -> bool:
    with Session(engine) as session:
        customer = session.exec(
            select(Customers).where(Customers.userId == userId)
        ).first()
        return customer is not None


def get_book_by_ISBN(ISBN: str) -> Books:
    with Session(engine) as session:
        book = session.get(Books, ISBN)
        return book


def get_customer_by_id(id: str) -> Customers:
    with Session(engine) as session:
        customer = session.get(Customers, id)
        return customer


def get_customer_by_userId(userId: str) -> Customers:
    with Session(engine) as session:
        customer = session.exec(
            select(Customers).where(Customers.userId == userId)
        ).first()
        return customer


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
async def post_books(ISBN, title, Author, description, genre, price, quantity):
    if not check_is_valid_price(price):
        return RESPONSE_INVALID_PRICE

    if check_does_ISBN_exist(ISBN):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"message": "This ISBN already exists in the system."},
        )

    book = Books(
        ISBN=ISBN,
        title=title,
        author=Author,
        description=description,
        genre=genre,
        price=price,
        quantity=quantity,
    )
    create_book(book)
    book = get_book_by_ISBN(ISBN)
    return {
        "ISBN": book.ISBN,
        "title": book.title,
        "Author": book.author,
        "description": book.description,
        "genre": book.genre,
        "price": book.price,
        "quantity": book.quantity,
    }


@app.put("/books/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def put_books(ISBN, title, Author, description, genre, price, quantity):
    if not check_is_valid_price(price):
        return RESPONSE_INVALID_PRICE

    if not check_does_ISBN_exist(ISBN):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Update failed. This ISBN does not exist."},
        )

    with Session(engine) as session:
        book = session.get(Books, ISBN)
        book.title = title
        book.author = Author
        book.description = description
        book.genre = genre
        book.price = price
        book.quantity = quantity
        session.add(book)
        session.commit()

    book = get_book_by_ISBN(ISBN)
    return {
        "ISBN": book.ISBN,
        "title": book.title,
        "Author": book.author,
        "description": book.description,
        "genre": book.genre,
        "price": book.price,
        "quantity": book.quantity,
    }


@app.get("/books/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books(ISBN):
    book = get_book_by_ISBN(ISBN)
    if book is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This ISBN does not exist."},
        )

    if book.summary is None:
        summary = get_LLM_book_500_words_summary(book.title, book.author, book.ISBN)
        with Session(engine) as session:
            book = session.get(Books, ISBN)
            book.summary = summary
            session.add(book)
            session.commit()

    book = get_book_by_ISBN(ISBN)
    return {
        "ISBN": book.ISBN,
        "title": book.title,
        "Author": book.author,
        "description": book.description,
        "genre": book.genre,
        "price": book.price,
        "quantity": book.quantity,
        "summary": book.summary,
    }


@app.get("/books/isbn/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books_duplicate_enpoint(ISBN):
    book = get_book_by_ISBN(ISBN)
    if book is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This ISBN does not exist."},
        )

    if book.summary is None:
        summary = get_LLM_book_500_words_summary(book.title, book.author, book.ISBN)
        with Session(engine) as session:
            book = session.get(Books, ISBN)
            book.summary = summary
            session.add(book)
            session.commit()

    book = get_book_by_ISBN(ISBN)
    return {
        "ISBN": book.ISBN,
        "title": book.title,
        "Author": book.author,
        "description": book.description,
        "genre": book.genre,
        "price": book.price,
        "quantity": book.quantity,
        "summary": book.summary,
    }


# =========
# Customers
# =========
@app.post("/customers", tags=["customers"], status_code=status.HTTP_201_CREATED)
async def post_customers(
    userId, name, phone, address, city, state, zipcode, address2=None
):
    if not check_is_valid_email(userId):
        return RESPONSE_INVALID_EMAIL

    if not check_is_valid_state_abbr(state):
        return RESPONSE_INVALID_STATE

    if check_does_user_id_exist(userId):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"message": "This user ID already exists in the system."},
        )

    customer = Customers(
        userId=userId,
        name=name,
        phone=phone,
        address=address,
        address2=address2,
        city=city,
        state=state,
        zipcode=zipcode,
    )
    create_customer(customer)
    customer = get_customer_by_userId(userId)
    return {
        "id": customer.customer_id,
        "userId": customer.userId,
        "name": customer.name,
        "phone": customer.phone,
        "address": customer.address,
        "address2": customer.address2,
        "city": customer.city,
        "state": customer.state,
        "zipcode": customer.zipcode,
    }


@app.get("/customers/{id}", tags=["customers"], status_code=status.HTTP_200_OK)
async def get_customers(id):
    customer = get_customer_by_id(id)
    if customer is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This ID does not exist."},
        )

    return {
        "id": customer.customer_id,
        "userId": customer.userId,
        "name": customer.name,
        "phone": customer.phone,
        "address": customer.address,
        "address2": customer.address2,
        "city": customer.city,
        "state": customer.state,
        "zipcode": customer.zipcode,
    }


@app.get("/customers", tags=["customers"], status_code=status.HTTP_200_OK)
async def get_customers_by_userId(userid):
    customer = get_customer_by_userId(userid)
    if customer is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This ID does not exist."},
        )

    return {
        "id": customer.customer_id,
        "userId": customer.userId,
        "name": customer.name,
        "phone": customer.phone,
        "address": customer.address,
        "address2": customer.address2,
        "city": customer.city,
        "state": customer.state,
        "zipcode": customer.zipcode,
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
