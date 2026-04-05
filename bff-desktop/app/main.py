import json
import os

import httpx
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.shared_library.input_data_validations import check_is_authenticated_request
from app.shared_library.models import (
    BookRequestBody,
    CustomerRequestBody,
)
from app.shared_library.responses import RESPONSE_UNAUTHENTICATED

from .metadata import contact, description, tags_metadata

IS_DEV = os.environ.get("IS_DEV", None)
IS_DEV = True if IS_DEV is not None else False
print(f"[INFO] IS_DEV = {IS_DEV}")

API_SERVICES_LOAD_BALANCER_URL = os.environ.get("API_SERVICES_LOAD_BALANCER_URL", None)
if API_SERVICES_LOAD_BALANCER_URL is None:
    raise Exception(
        "[ERROR] Required credentials were not found in the environment variables"
    )

app = FastAPI(
    title="Bookstore BFF (Backend For Frontend) for Desktop",
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


# =====
# Books
# =====
@app.post("/books", tags=["books"], status_code=status.HTTP_201_CREATED)
async def post_books(book_request_body: BookRequestBody, response: Response):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{API_SERVICES_LOAD_BALANCER_URL}/books",
            json=json.loads(book_request_body.model_dump_json()),
        )
    response.status_code = res.status_code
    response.body = res.content


@app.put("/books/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def put_books(
    book_request_body: BookRequestBody,
    ISBN: str | int | float | bool,
    response: Response,
):
    async with httpx.AsyncClient() as client:
        res = await client.put(
            f"{API_SERVICES_LOAD_BALANCER_URL}/books/{ISBN}",
            json=json.loads(book_request_body.model_dump_json()),
        )
    response.status_code = res.status_code
    response.body = res.content


@app.get("/books/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books(ISBN, response: Response):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_SERVICES_LOAD_BALANCER_URL}/books/{ISBN}")
    response.status_code = res.status_code
    response.body = res.content


@app.get("/books/isbn/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books_duplicate_enpoint(ISBN, response: Response):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_SERVICES_LOAD_BALANCER_URL}/books/isbn/{ISBN}")
    response.status_code = res.status_code
    response.body = res.content


@app.get("/books/{ISBN}/related-books", tags=["books"], status_code=status.HTTP_200_OK)
async def get_related_books(ISBN, response: Response):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{API_SERVICES_LOAD_BALANCER_URL}/books/{ISBN}/related-books"
        )
    response.status_code = res.status_code
    response.body = res.content


# =========
# Customers
# =========
@app.post("/customers", tags=["customers"], status_code=status.HTTP_201_CREATED)
async def post_customers(
    customer_request_body: CustomerRequestBody, response: Response
):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{API_SERVICES_LOAD_BALANCER_URL}/customers",
            json=json.loads(customer_request_body.model_dump_json()),
        )
    response.status_code = res.status_code
    response.body = res.content


@app.get("/customers/{id}", tags=["customers"], status_code=status.HTTP_200_OK)
async def get_customers(id: int, response: Response):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_SERVICES_LOAD_BALANCER_URL}/customers/{id}")
    response.status_code = res.status_code
    response.body = res.content


@app.get("/customers", tags=["customers"], status_code=status.HTTP_200_OK)
async def get_customers_by_userId(userId, response: Response):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{API_SERVICES_LOAD_BALANCER_URL}/customers", params={"userId": userId}
        )
    response.status_code = res.status_code
    response.body = res.content


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
