import os
import asyncio

import httpx
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import pymongo
from pymongo import AsyncMongoClient, ReturnDocument

from app.shared_library.input_data_validations import (
    sanitize_env_var,
)
from app.shared_library.models import Books, Misc
from app.shared_library.responses import (
    RESOPNSE_500_SERVER_ERROR,
    RESPONSE_503_CIRCUIT_BREAKER_OPEN,
    RESPONSE_NO_CONTENT,
)
from app.shared_library.utils import get_autograder_safe_genre, get_is_valid_keyword

from .metadata import contact, description, tags_metadata
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
DB_PORT = os.environ.get("DB_PORT", None)
DB_DATABASE = os.environ.get("DB_DATABASE", None)
DB_COLLECTION = os.environ.get("DB_COLLECTION", None)
API_RELATED_BOOKS_URL = os.environ.get("API_RELATED_BOOKS_URL", None)
should_raise_exception = False
if DB_USER is None:
    print("[ERROR] DB_USER = None")
    should_raise_exception = True
if DB_PASS is None:
    print("[ERROR] DB_PASS = None")
    should_raise_exception = True
if DB_URL is None:
    print("[ERROR] DB_URL = None")
    should_raise_exception = True
# In prod, a MongoDB cluster is used instead of a local instance of MongoDB.
# MongoDB clusters don't accept port numbers.
if DB_PORT is None and IS_DEV:
    print("[ERROR] DB_PORT = None")
    should_raise_exception = True
if DB_DATABASE is None:
    print("[ERROR] DB_DATABASE = None")
    should_raise_exception = True
if DB_COLLECTION is None:
    print("[ERROR] DB_COLLECTION = None")
    should_raise_exception = True
if API_RELATED_BOOKS_URL is None:
    print("[ERROR] API_RELATED_BOOKS_URL = None")
    should_raise_exception = True
if should_raise_exception:
    raise Exception(
        "[ERROR] Required credentials were not found in the environment variables"
    )

# K8s includes something like DB_USER='...' to include the quotes themselves too.
# Thus, sanitize it so that the env vars do not start with or end with quotes.
DB_USER = sanitize_env_var(DB_USER)
DB_PASS = sanitize_env_var(DB_PASS)
DB_URL = sanitize_env_var(DB_URL)
DB_PORT = int(float(sanitize_env_var(DB_PORT))) if IS_DEV else None
DB_DATABASE = sanitize_env_var(DB_DATABASE)
DB_COLLECTION = sanitize_env_var(DB_COLLECTION)
API_RELATED_BOOKS_URL = sanitize_env_var(API_RELATED_BOOKS_URL)

str_db_connection = None
if not IS_DEV:
    str_db_connection = f"mongodb+srv://{DB_USER}:{DB_PASS}@{DB_URL}"
else:
    str_db_connection = f"mongodb://{DB_USER}:{DB_PASS}@{DB_URL}:{DB_PORT}"
db_client = AsyncMongoClient(str_db_connection, server_api=pymongo.server_api.ServerApi(version="1"))
db = db_client.get_database(DB_DATABASE)
db_collection = db.get_collection(DB_COLLECTION)
db_collection.create_index([("ISBN", pymongo.ASCENDING)], unique=True)


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


async def get_book_by_ISBN(ISBN: str) -> Books:
    ISBN = str(ISBN)
    book = await db_collection.find_one({"ISBN": ISBN})
    return book


async def get_books_by_keyword_from_db(keyword: str) -> Books | None:
    keyword = str(keyword)
    # Reference: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/find/
    async_cursor = db_collection.find({
        "$or": [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"author": {"$regex": keyword, "$options": "i"}},
            {"description": {"$regex": keyword, "$options": "i"}},
            {"genre": {"$regex": keyword, "$options": "i"}},
            {"summary": {"$regex": keyword, "$options": "i"}},
        ]
    })
    books = []
    async for book in async_cursor:
        books.append(book)
    if len(books) == 0:
        return None
    else:
        return books


# =====
# Books
# =====
@app.get("/books", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books_by_keyword(keyword: str):
    if not get_is_valid_keyword(keyword):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": "Retrieval failed. The keyword query parameter must be a-z or A-Z."
            },
        )
    books = await get_books_by_keyword_from_db(keyword)
    if books is None:
        return RESPONSE_NO_CONTENT
    cleaned_books = []
    for book in books:
        cleaned_books.append({
            "ISBN": str(book["ISBN"]),
            "title": str(book["title"]),
            "Author": str(book["author"]),
            "description": str(book["description"]),
            "genre": get_autograder_safe_genre(book["genre"]),
            "price": float(book["price"]),
            "quantity": int(book["quantity"]),
            "summary": str(book["summary"]),
        })
    return cleaned_books


@app.get("/books/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books(ISBN):
    book = await get_book_by_ISBN(ISBN)
    if book is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This ISBN does not exist."},
        )
    return {
        "ISBN": str(book["ISBN"]),
        "title": str(book["title"]),
        "Author": str(book["author"]),
        "description": str(book["description"]),
        "genre": get_autograder_safe_genre(book["genre"]),
        "price": float(book["price"]),
        "quantity": int(book["quantity"]),
        "summary": str(book["summary"]),
    }


@app.get("/books/isbn/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books_duplicate_enpoint(ISBN):
    book = await get_book_by_ISBN(ISBN)
    if book is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This ISBN does not exist."},
        )
    return {
        "ISBN": str(book["ISBN"]),
        "title": str(book["title"]),
        "Author": str(book["author"]),
        "description": str(book["description"]),
        "genre": get_autograder_safe_genre(book["genre"]),
        "price": float(book["price"]),
        "quantity": int(book["quantity"]),
        "summary": str(book["summary"]),
    }


@app.get("/books/{ISBN}/related-books", tags=["books"], status_code=status.HTTP_200_OK)
async def get_related_books(ISBN):
    CIRCUIT_BREAKER_TIMEOUT = 3  # Seconds.
    with Session(engine) as db_session:
        if check_circuit_breaker_open(db_session):
            if not check_should_circuit_breaker_close(db_session):
                return RESPONSE_503_CIRCUIT_BREAKER_OPEN
            else:
                # This is the circuit breaker's half-open state in which a re-attempt should
                # be made. If the re-attempt fails, the clock resets. If the re-attempt
                # suceeds, the circuit breaker closes and resumes normal operation.
                async with httpx.AsyncClient(timeout=CIRCUIT_BREAKER_TIMEOUT) as client:
                    try:
                        res = await client.get(f"{API_RELATED_BOOKS_URL}/{ISBN}")
                    except httpx.TimeoutException:
                        print("[INFO] reset_circuit_breaker_time(db_session)")
                        reset_circuit_breaker_time(db_session)
                        return RESPONSE_503_CIRCUIT_BREAKER_OPEN
                    else:
                        print("[INFO] close_circuit_breaker(db_session)")
                        close_circuit_breaker(db_session)
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
                print("[INFO] check_circuit_breaker_open(db_session) = False")
                print("[INFO] httpx.TimeoutException")
                print("[INFO] open_circuit_breaker(db_session)")
                open_circuit_breaker(db_session)
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
