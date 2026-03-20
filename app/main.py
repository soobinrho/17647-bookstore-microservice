from fastapi import FastAPI, status, Response, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from google import genai
from dotenv import load_dotenv
from .input_data_validations import (
    check_is_valid_price,
    check_is_valid_email,
    check_is_valid_state_abbr,
)
import os

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
load_dotenv()
DB_USER = os.environ.get("BOOKSTORE_BACKEND_DB_USER", None)
DB_PASS = os.environ.get("BOOKSTORE_BACKEND_DB_PASS", None)

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
    # try:
    #     with genai.Client() as client:
    #         prompt = (
    #             "You're Frank Herbert the author of Dune. I am a huge fan of yours. "
    #             + f"Please write a 500-word summary of the following book: {title} "
    #             + f"by the author {author} with ISBN {ISBN}. I don't care if the book "
    #             + "actually exists or not, so please feel free to make up something "
    #             + "based on the book name and the book author. Please respond with a "
    #             + "summary of the book in exactly 500 words."
    #         )
    #         summary = (
    #             client.models.generate_content(
    #                 # TODO: Check if possible to run without specifying a model.
    #                 # model="gemini-3-flash-preview", contents=prompt
    #                 contents=prompt
    #             )
    #         ).text
    # except Exception as e:
    #     summary = f"Gemini API returned the following error:\n{e}"

    summary = "Here's a placeholder for the 500-words summary."
    return summary


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

    # TODO: MariaDB integration.
    does_record_already_exist = False
    if does_record_already_exist:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"message": "This ISBN already exists in the system."},
        )

    # TODO: Return the DB object.
    return {
        "ISBN": ISBN,
        "title": title,
        "Author": Author,
        "description": description,
        "genre": genre,
        "price": price,
        "quantity": quantity,
    }


@app.put("/books/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def put_books(ISBN, title, Author, description, genre, price, quantity):
    if not check_is_valid_price(price):
        return RESPONSE_INVALID_PRICE

    is_ISBN_not_found = False
    if is_ISBN_not_found:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Update failed. This ISBN does not exist."},
        )

    # TODO: Return the DB object.
    return {
        "ISBN": ISBN,
        "title": title,
        "Author": Author,
        "description": description,
        "genre": genre,
        "price": price,
        "quantity": quantity,
    }


@app.get("/books/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books(ISBN):
    is_ISBN_not_found = False
    if is_ISBN_not_found:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This ISBN does not exist."},
        )

    is_summary_generated = False
    if not is_summary_generated:
        pass
        # summary = get_LLM_book_500_words_summary(title, Author, ISBN)
        # TODO: update the DB with the summary.

    # TODO: Return the DB object.
    return {
        "ISBN": "placeholder",
        "title": "placeholder",
        "Author": "placeholder",
        "description": "placeholder",
        "genre": "placeholder",
        "price": "placeholder",
        "quantity": "placeholder",
        "summary": "placeholder",
    }


@app.get("/books/isbn/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books_duplicate_enpoint(ISBN):
    is_ISBN_not_found = False
    if is_ISBN_not_found:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This ISBN does not exist."},
        )

    is_summary_generated = False
    if not is_summary_generated:
        pass
        # summary = get_LLM_book_500_words_summary(title, Author, ISBN)
        # TODO: update the DB with the summary.

    # TODO: Return the DB object.
    return {
        "ISBN": "placeholder",
        "title": "placeholder",
        "Author": "placeholder",
        "description": "placeholder",
        "genre": "placeholder",
        "price": "placeholder",
        "quantity": "placeholder",
        "summary": "placeholder",
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

    does_record_already_exist = False
    if does_record_already_exist:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"message": "This user ID already exists in the system."},
        )

    # TODO: Return the DB object.
    return {
        "id": "placeholder",
        "userId": "placeholder",
        "name": "placeholder",
        "phone": "placeholder",
        "address": "placeholder",
        "address2": "placeholder",
        "city": "placeholder",
        "state": "placeholder",
        "zipcode": "placeholder",
    }


@app.get("/customers/{id}", tags=["customers"], status_code=status.HTTP_200_OK)
async def get_customers(id):
    is_id_not_found = False
    if is_id_not_found:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This ID does not exist."},
        )

    # TODO: Return the DB object.
    return {
        "id": "placeholder",
        "userId": "placeholder",
        "name": "placeholder",
        "phone": "placeholder",
        "address": "placeholder",
        "address2": "placeholder",
        "city": "placeholder",
        "state": "placeholder",
        "zipcode": "placeholder",
    }


@app.get("/customers", tags=["customers"], status_code=status.HTTP_200_OK)
async def get_customers_query_param_userid(userid):
    is_id_not_found = False
    if is_id_not_found:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This ID does not exist."},
        )

    # TODO: Return the DB object.
    return {
        "id": "placeholder",
        "userId": "placeholder",
        "name": "placeholder",
        "phone": "placeholder",
        "address": "placeholder",
        "address2": "placeholder",
        "city": "placeholder",
        "state": "placeholder",
        "zipcode": "placeholder",
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
