import os

from fastapi import BackgroundTasks, FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from google import genai
from sqlmodel import Session, SQLModel, create_engine

from app.shared_library.input_data_validations import (
    check_is_authenticated_request,
    check_is_valid_price,
    check_is_valid_quantity,
)
from app.shared_library.models import (
    BookRequestBody,
    Books,
)
from app.shared_library.responses import (
    RESPONSE_INVALID_PRICE,
    RESPONSE_INVALID_QUANTITY,
    RESPONSE_UNAUTHENTICATED,
)

from .metadata import contact, description, tags_metadata

DB_USER = os.environ.get("DB_USER", None)
DB_PASS = os.environ.get("DB_PASS", None)
DB_URL = os.environ.get("DB_URL", None)
DB_DATABASE = os.environ.get("DB_DATABASE", None)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", None)
if (
    DB_USER is None
    or DB_PASS is None
    or DB_URL is None
    or DB_DATABASE is None
    or GEMINI_API_KEY is None
):
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
    if not check_is_authenticated_request(
        req.url.path, req.headers.get("Authorization", None)
    ):
        return RESPONSE_UNAUTHENTICATED

    res = await call_next_api(req)
    return res


def get_LLM_book_500_words_summary(title: str, author: str, ISBN: str) -> str:
    # Source: https://github.com/googleapis/python-genai?tab=readme-ov-file#client-context-managers
    try:
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


def background_task_generate_summary(title: str, author: str, ISBN: str):
    book = get_book_by_ISBN(ISBN)
    if book.summary is None:
        summary = get_LLM_book_500_words_summary(book.title, book.author, book.ISBN)
        with Session(engine) as session:
            book_session = session.get(Books, ISBN)
            book_session.summary = summary
            session.add(book_session)
            session.commit()


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
