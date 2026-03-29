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
async def add_test(req: Request, call_next_api):
    req_path = req.url.path
    if not req_path.startswith("/docs") and not req_path.startswith("/openapi.json"):
        authorization = req.headers.get("Authorization", None)
        if authorization is None or not check_is_valid_JWT(authorization):
            # DEBUG
            print("[INFO] NO VALID JWT DETECTED.")
            # DEBUG
            # return RESPONSE_UNAUTHORIZED

    # DEBUG
    print(f"[INFO] {API_SERVICES_LOAD_BALANCER_URL}")
    res = await call_next_api(req)
    return res


# =====
# Books
# =====
@app.post("/books", tags=["books"], status_code=status.HTTP_201_CREATED)
async def post_books(book_request_body: BookRequestBody):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{API_SERVICES_LOAD_BALANCER_URL}/books",
            json=json.loads(book_request_body.model_dump_json()),
        )
    return res.json()


@app.put("/books/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def put_books(book_request_body: BookRequestBody, ISBN: str | int | float | bool):
    async with httpx.AsyncClient() as client:
        res = await client.put(
            f"{API_SERVICES_LOAD_BALANCER_URL}/books/{ISBN}",
            json=json.loads(book_request_body.model_dump_json()),
        )
    return res.json()


@app.get("/books/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books(ISBN):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_SERVICES_LOAD_BALANCER_URL}/books/{ISBN}")
    return res.json()


@app.get("/books/isbn/{ISBN}", tags=["books"], status_code=status.HTTP_200_OK)
async def get_books_duplicate_enpoint(ISBN):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_SERVICES_LOAD_BALANCER_URL}/books/isbn/{ISBN}")
    return res.json()


# =========
# Customers
# =========
@app.post("/customers", tags=["customers"], status_code=status.HTTP_201_CREATED)
async def post_customers(customer_request_body: CustomerRequestBody):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{API_SERVICES_LOAD_BALANCER_URL}/customers",
            json=json.loads(customer_request_body.model_dump_json()),
        )
    return res.json()


@app.get("/customers/{id}", tags=["customers"], status_code=status.HTTP_200_OK)
async def get_customers(id: int):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_SERVICES_LOAD_BALANCER_URL}/customers/{id}")
    return res.json()


@app.get("/customers", tags=["customers"], status_code=status.HTTP_200_OK)
async def get_customers_by_userId(userId):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{API_SERVICES_LOAD_BALANCER_URL}/customers", params={"userId": userId}
        )
    return res.json()


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
