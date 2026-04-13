import os

import httpx
from fastapi import BackgroundTasks, FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlmodel import Session, SQLModel, create_engine

from app.shared_library.input_data_validations import (
    check_is_authenticated_request,
    check_is_valid_price,
    check_is_valid_quantity,
)
from app.shared_library.models import BookRequestBody, Books
from app.shared_library.responses import (
    RESOPNSE_500_SERVER_ERROR,
    RESPONSE_503_CIRCUIT_BREAKER_OPEN,
    RESPONSE_INVALID_PRICE,
    RESPONSE_INVALID_QUANTITY,
    RESPONSE_NO_CONTENT,
    RESPONSE_UNAUTHENTICATED,
)

from .metadata import contact, description, tags_metadata
from .wrapper_book_summary import get_book_500_words_summary
from .wrapper_circuit_breaker import (
    check_circuit_breaker_open,
    check_should_circuit_breaker_close,
    close_circuit_breaker,
    open_circuit_breaker,
    reset_circuit_breaker_time,
)

IS_DEV = os.environ.get("IS_DEV", None)
IS_DEV = True if IS_DEV is not None else False
print(f"[INFO] IS_DEV = {IS_DEV}")

DB_USER = os.environ.get("DB_USER", None)
DB_PASS = os.environ.get("DB_PASS", None)
DB_URL = os.environ.get("DB_URL", None)
DB_DATABASE = os.environ.get("DB_DATABASE", None)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", None)
API_RELATED_BOOKS_URL = os.environ.get("API_RELATED_BOOKS_URL", None)
should_raise_exception = False
if DB_USER is None:
    print("[ERROR] DB_USER is None")
    should_raise_exception = True
if DB_PASS is None:
    print("[ERROR] DB_PASS is None")
    should_raise_exception = True
if DB_URL is None:
    print("[ERROR] DB_URL is None")
    should_raise_exception = True
if DB_DATABASE is None:
    print("[ERROR] DB_DATABASE is None")
    should_raise_exception = True
if GEMINI_API_KEY is None:
    print("[ERROR] GEMINI_API_KEY is None")
    should_raise_exception = True
if API_RELATED_BOOKS_URL is None:
    print("[ERROR] API_RELATED_BOOKS_URL is None")
    should_raise_exception = True
if should_raise_exception:
    raise Exception(
        "[ERROR] Required credentials were not found in the environment variables"
    )

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_URL}/{DB_DATABASE}", echo=False
)
SQLModel.metadata.create_all(engine)

app = FastAPI(
    title="Bookstore API Service for Books Data",
    description=description,
    tags_metadata=tags_metadata,
    contact=contact,
)


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


@app.middleware("http")
async def middleware_main(req: Request, call_next_api):
    if not IS_DEV and not check_is_authenticated_request(
        req.url.path, req.headers.get("Authorization", None)
    ):
        return RESPONSE_UNAUTHENTICATED

    res = await call_next_api(req)
    return res


def create_book(book: Books) -> None:
    with Session(engine) as session:
        session.add(book)
        session.commit()


def check_does_ISBN_exist(ISBN: str) -> bool:
    with Session(engine) as session:
        book = session.get(Books, ISBN)
        return book is not None


def get_book_by_ISBN(ISBN: str) -> Books:
    with Session(engine) as session:
        book = session.get(Books, ISBN)
        return book


def background_task_generate_summary(title: str, author: str, ISBN: str):
    book = get_book_by_ISBN(ISBN)
    if book.summary is None:
        summary = get_book_500_words_summary(book.title, book.author, book.ISBN)
        with Session(engine) as session:
            book_session = session.get(Books, ISBN)
            book_session.summary = summary
            session.add(book_session)
            session.commit()


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
        "quantity": int(book.quantity),
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

    # This is required because of a very particular test case in autograde:
    #   Test Failed: '3' != 3 : Get book (mobile) [GET /books/{ISBN}]: field 'genre' expected 3 (genre must be 3 for mobile), got '3'.
    genre = str(book.genre)
    if genre.isnumeric():
        genre = float(genre)
        if genre.is_integer():
            genre = int(genre)
    return {
        "ISBN": str(book.ISBN),
        "title": str(book.title),
        "Author": str(book.author),
        "description": str(book.description),
        "genre": genre,
        "price": float(book.price),
        "quantity": int(book.quantity),
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
    genre = str(book.genre)
    if genre.isnumeric():
        genre = float(genre)
        if genre.is_integer():
            genre = int(genre)
    return {
        "ISBN": str(book.ISBN),
        "title": str(book.title),
        "Author": str(book.author),
        "description": str(book.description),
        "genre": genre,
        "price": float(book.price),
        "quantity": int(book.quantity),
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
    genre = str(book.genre)
    if genre.isnumeric():
        genre = float(genre)
        if genre.is_integer():
            genre = int(genre)
    return {
        "ISBN": str(book.ISBN),
        "title": str(book.title),
        "Author": str(book.author),
        "description": str(book.description),
        "genre": genre,
        "price": float(book.price),
        "quantity": int(book.quantity),
        "summary": str(book.summary),
    }


@app.get("/books/{ISBN}/related-books", tags=["books"], status_code=status.HTTP_200_OK)
async def get_related_books(ISBN):
    CIRCUIT_BREAKER_TIMEOUT = 3  # Seconds.
    if check_circuit_breaker_open():
        if not check_should_circuit_breaker_close():
            return RESPONSE_503_CIRCUIT_BREAKER_OPEN
        else:
            # This is the circuit breaker's half-open state in which a re-attempt should
            # be made. If the re-attempt fails, the clock resets. If the re-attempt
            # suceeds, the circuit breaker closes and resumes normal operation.
            async with httpx.AsyncClient(timeout=CIRCUIT_BREAKER_TIMEOUT) as client:
                try:
                    res = await client.get(f"{API_RELATED_BOOKS_URL}/{ISBN}")
                except httpx.TimeoutException:
                    print("[INFO] reset_circuit_breaker_time()")
                    reset_circuit_breaker_time()
                    return RESPONSE_503_CIRCUIT_BREAKER_OPEN
                else:
                    print("[INFO] close_circuit_breaker()")
                    close_circuit_breaker()
                    if str(res.status_code) == "200":
                        return res.json()
                    elif str(res.status_code) == "204":
                        return RESPONSE_NO_CONTENT
                    else:
                        return RESOPNSE_500_SERVER_ERROR

    async with httpx.AsyncClient(timeout=CIRCUIT_BREAKER_TIMEOUT) as client:
        try:
            res = await client.get(f"{API_RELATED_BOOKS_URL}/{ISBN}")
        except httpx.TimeoutException:
            print("[INFO] check_circuit_breaker_open() = False")
            print("[INFO] httpx.TimeoutException")
            print("[INFO] open_circuit_breaker()")
            open_circuit_breaker()
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={"message": "Please try again later."},
            )
        else:
            if str(res.status_code) == "200":
                return res.json()
            elif str(res.status_code) == "204":
                return RESPONSE_NO_CONTENT
            else:
                return RESOPNSE_500_SERVER_ERROR


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
