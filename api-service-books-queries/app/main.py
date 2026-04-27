import httpx
import pymongo
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo import AsyncMongoClient

from app.shared_library.constants import (
    COLNAME_AUTHOR,
    COLNAME_DESCRIPTION,
    COLNAME_GENRE,
    COLNAME_ISBN,
    COLNAME_PRICE,
    COLNAME_QUANTITY,
    COLNAME_SUMMARY,
    COLNAME_TITLE,
)
from app.shared_library.models import Books
from app.shared_library.responses import (
    RESOPNSE_500_SERVER_ERROR,
    RESPONSE_503_CIRCUIT_BREAKER_OPEN,
    RESPONSE_NO_CONTENT,
)
from app.shared_library.utils import (
    get_autograder_safe_genre,
    get_env_vars_for_api_service_books_queries,
    get_is_valid_keyword,
)

from .metadata import contact, description, tags_metadata
from .wrapper_circuit_breaker import (
    check_circuit_breaker_open,
    check_should_circuit_breaker_close,
    close_circuit_breaker,
    open_circuit_breaker,
    reset_circuit_breaker_time,
)

CONFIGS = get_env_vars_for_api_service_books_queries()

str_db_connection = None
if not CONFIGS["IS_DEV"]:
    str_db_connection = (
        f"mongodb+srv://{CONFIGS['DB_USER']}:{CONFIGS['DB_PASS']}@{CONFIGS['DB_URL']}"
    )
else:
    str_db_connection = f"mongodb://{CONFIGS['DB_USER']}:{CONFIGS['DB_PASS']}@{CONFIGS['DB_URL']}:{CONFIGS['DB_PORT']}"
db_client = AsyncMongoClient(
    str_db_connection, server_api=pymongo.server_api.ServerApi(version="1")
)
db = db_client.get_database(CONFIGS["DB_DATABASE"])
db_collection = db.get_collection(CONFIGS["DB_COLLECTION"])


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
    book = await db_collection.find_one({COLNAME_ISBN: ISBN})
    return book


def get_async_cursor_books_by_keyword_from_db(keyword: str):
    keyword = str(keyword)
    # Reference: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/find/
    async_cursor = db_collection.find({
        "$or": [
            {COLNAME_TITLE: {"$regex": keyword, "$options": "i"}},
            {COLNAME_AUTHOR: {"$regex": keyword, "$options": "i"}},
            {COLNAME_DESCRIPTION: {"$regex": keyword, "$options": "i"}},
            {COLNAME_GENRE: {"$regex": keyword, "$options": "i"}},
            {COLNAME_SUMMARY: {"$regex": keyword, "$options": "i"}},
        ]
    })
    return async_cursor


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
    async_cursor = get_async_cursor_books_by_keyword_from_db(keyword)
    cleaned_books = []
    async for book in async_cursor:
        cleaned_books.append({
            "ISBN": str(book[COLNAME_ISBN]),
            "title": str(book[COLNAME_TITLE]),
            "Author": str(book[COLNAME_AUTHOR]),
            "description": str(book[COLNAME_DESCRIPTION]),
            "genre": get_autograder_safe_genre(book[COLNAME_GENRE]),
            "price": float(book[COLNAME_PRICE]),
            "quantity": int(book[COLNAME_QUANTITY]),
            "summary": str(book[COLNAME_SUMMARY]),
        })
    if len(cleaned_books) == 0:
        return RESPONSE_NO_CONTENT
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
        "ISBN": str(book[COLNAME_ISBN]),
        "title": str(book[COLNAME_TITLE]),
        "Author": str(book[COLNAME_AUTHOR]),
        "description": str(book[COLNAME_DESCRIPTION]),
        "genre": get_autograder_safe_genre(book[COLNAME_GENRE]),
        "price": float(book[COLNAME_PRICE]),
        "quantity": int(book[COLNAME_QUANTITY]),
        "summary": str(book[COLNAME_SUMMARY]),
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
        "ISBN": str(book[COLNAME_ISBN]),
        "title": str(book[COLNAME_TITLE]),
        "Author": str(book[COLNAME_AUTHOR]),
        "description": str(book[COLNAME_DESCRIPTION]),
        "genre": get_autograder_safe_genre(book[COLNAME_GENRE]),
        "price": float(book[COLNAME_PRICE]),
        "quantity": int(book[COLNAME_QUANTITY]),
        "summary": str(book[COLNAME_SUMMARY]),
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
                    res = await client.get(f"{CONFIGS['API_RELATED_BOOKS_URL']}/{ISBN}")
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
            res = await client.get(f"{CONFIGS['API_RELATED_BOOKS_URL']}/{ISBN}")
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
