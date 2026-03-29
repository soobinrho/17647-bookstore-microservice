from contextlib import asynccontextmanager
from fastapi import FastAPI, status, Response, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from starlette.background import BackgroundTask
from app.shared_library.models import (
    Books,
    Customers,
    BookRequestBody,
    CustomerRequestBody,
)
from app.shared_library.input_data_validations import (
    check_is_valid_JWT,
    check_is_valid_price,
    check_is_valid_email,
    check_is_valid_quantity,
    check_is_valid_state_abbr,
)
import os
import httpx


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
## Bookstore BFF (Backend For Frontend) for Desktop

Reference: https://github.com/soobinrho/17647-bookstore-microservice

<br>
"""

tags_metadata = [
    {
        "name": "books",
        "description": "Desktop BFF for the API service for books data.",
    },
    {
        "name": "customers",
        "description": "Desktop BFF for the API service for customers data.",
    },
    {
        "name": "uncategorized",
        "description": "Other API endpoints.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Source: https://stackoverflow.com/a/74556972
    async with httpx.AsyncClient(base_url=API_SERVICES_LOAD_BALANCER_URL) as client:
        yield {"client": client}


app = FastAPI(
    title="Bookstore BFF (Backend For Frontend) for Desktop",
    description=description,
    contact={
        "name": "Soobin Rho",
        "url": "https://github.com/soobinrho",
        "email": "soobinrho@gmail.com",
    },
    lifespan=lifespan,
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


# ==========
# Middleware
# ==========
@app.middleware("http")
async def add_test(req: Request, call_next_api):
    if "Authorization" not in req.headers:
        print("Return the error")

    if not check_is_valid_JWT(req.headers["Authorization"]):
        print("Return the error")

    res = await call_next_api(req)
    return res


async def _reverse_proxy(request: Request):
    # Source: https://stackoverflow.com/a/74556972
    client = request.state.client
    url = httpx.URL(path=request.url.path, query=request.url.query.encode("utf-8"))
    headers = [(k, v) for k, v in request.headers.raw if k != b"host"]
    req = client.build_request(
        request.method, url, headers=headers, content=request.stream()
    )
    r = await client.send(req, stream=True)
    return StreamingResponse(
        r.aiter_raw(),
        status_code=r.status_code,
        headers=r.headers,
        background=BackgroundTask(r.aclose),
    )


# =====
# Books
# =====
app.add_route("/books", _reverse_proxy, ["POST"])
app.add_route("/books/{ISBN}", _reverse_proxy, ["GET", "PUT"])
app.add_route("/books/isbn/{ISBN}", _reverse_proxy, ["GET"])

# =========
# Customers
# =========
app.add_route("/customers", _reverse_proxy, ["GET", "POST"])
app.add_route("/customers/{id}", _reverse_proxy, ["GET"])

# =============
# Uncategorized
# =============
app.add_route("/status", _reverse_proxy, ["GET"])


@app.get(
    "/status",
    tags=["uncategorized"],
    status_code=status.HTTP_200_OK,
)
async def get_status(response: Response):
    return JSONResponse(content="OK", headers={"Content-Type": "text/plain"})
