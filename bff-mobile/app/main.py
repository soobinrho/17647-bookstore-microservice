from fastapi import FastAPI, status, Response, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.shared_library.models import (
    BookRequestBody,
    CustomerRequestBody,
)
from app.shared_library.input_data_validations import (
    check_is_valid_JWT,
)
import os
import httpx
import json


# =========================================
# API Services Load Balancer Configurations
# =========================================
API_SERVICES_LOAD_BALANCER_URL = os.environ.get("API_SERVICES_LOAD_BALANCER_URL", None)
if API_SERVICES_LOAD_BALANCER_URL is None:
    raise Exception(
        "[ERROR] Required credentials were not found in the environment variables"
    )


# ============================================
# FastAPI Automatic API Documentation Metadata
# ============================================
# Reference: https://fastapi.tiangolo.com/tutorial/metadata/
description = """
## Bookstore BFF (Backend For Frontend) for Mobile

Reference: https://github.com/soobinrho/17647-bookstore-microservice

<br>
"""

tags_metadata = [
    {
        "name": "books",
        "description": "Mobile BFF for the API service for books data.",
    },
    {
        "name": "customers",
        "description": "Mobile BFF for the API service for customers data.",
    },
    {
        "name": "uncategorized",
        "description": "Other API endpoints.",
    },
]


app = FastAPI(
    title="Bookstore BFF (Backend For Frontend) for Mobile",
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
RESPONSE_UNAUTHORIZED = JSONResponse(
    status_code=status.HTTP_401_UNAUTHORIZED,
    content={"message": "Please provide a valid JWT."},
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


# ==========
# Middleware
# ==========
@app.middleware("http")
async def middleware_main(req: Request, call_next_api):
    req_path = req.url.path
    if not req_path.startswith("/docs") and not req_path.startswith("/openapi.json"):
        authorization = req.headers.get("Authorization", None)
        if authorization is None or not check_is_valid_JWT(authorization):
            return RESPONSE_UNAUTHORIZED

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
    return res.json()


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
    return res.json()


@app.get("/books/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books(ISBN, response: Response):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_SERVICES_LOAD_BALANCER_URL}/books/{ISBN}")
    res = str(res.json()).replace("non-fiction", "3")
    return res


@app.get("/books/isbn/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books_duplicate_enpoint(ISBN, response: Response):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_SERVICES_LOAD_BALANCER_URL}/books/isbn/{ISBN}")
    response.status_code = res.status_code
    res = str(res.json()).replace("non-fiction", "3")
    return res


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
    return res.json()


@app.get("/customers/{id}", tags=["customers"], status_code=status.HTTP_200_OK)
async def get_customers(id: int, response: Response):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_SERVICES_LOAD_BALANCER_URL}/customers/{id}")
    response.status_code = res.status_code
    res = res.json()
    LIST_DELETE_ATTRIBUTES = ["address", "address2", "city", "state", "zipcode"]
    for del_attribute in LIST_DELETE_ATTRIBUTES:
        if del_attribute in res:
            del res[del_attribute]
    return res


@app.get("/customers", tags=["customers"], status_code=status.HTTP_200_OK)
async def get_customers_by_userId(userId, response: Response):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{API_SERVICES_LOAD_BALANCER_URL}/customers", params={"userId": userId}
        )
    response.status_code = res.status_code
    res = res.json()
    LIST_DELETE_ATTRIBUTES = ["address", "address2", "city", "state", "zipcode"]
    for del_attribute in LIST_DELETE_ATTRIBUTES:
        if del_attribute in res:
            del res[del_attribute]
    return res


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
