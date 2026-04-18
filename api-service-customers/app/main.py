import os

from fastapi import BackgroundTasks, FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import URL
from sqlmodel import Session, SQLModel, create_engine, select

from app.shared_library.input_data_validations import (
    check_is_valid_email,
    check_is_valid_state_abbr,
    sanitize_env_var,
)
from app.shared_library.models import (
    CustomerRequestBody,
    Customers,
)
from app.shared_library.responses import (
    RESPONSE_INVALID_EMAIL,
    RESPONSE_INVALID_STATE,
)
from app.wrapper_kafka_producer import produce_kafka_message

from .metadata import contact, description, tags_metadata

DB_USER = os.environ.get("DB_USER", None)
DB_PASS = os.environ.get("DB_PASS", None)
DB_URL = os.environ.get("DB_URL", None)
DB_PORT = os.environ.get("DB_PORT", None)
DB_DATABASE = os.environ.get("DB_DATABASE", None)
list_env_vars = [DB_USER, DB_PASS, DB_URL, DB_PORT, DB_DATABASE]
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
if DB_PORT is None:
    print("[ERROR] DB_PORT = None")
    should_raise_exception = True
if DB_DATABASE is None:
    print("[ERROR] DB_DATABASE = None")
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
DB_PORT = int(float(sanitize_env_var(DB_PORT)))
DB_DATABASE = sanitize_env_var(DB_DATABASE)

# Reference: https://docs.sqlalchemy.org/en/21/core/engines.html#creating-urls-programmatically
url_db_connection = URL.create(
    "mysql+pymysql",
    username=DB_USER,
    password=DB_PASS,
    host=DB_URL,
    port=DB_PORT,
    database=DB_DATABASE,
)
print(f'[INFO] Connecting to "{url_db_connection}"...')
engine = create_engine(url_db_connection, echo=False)
print(f'[INFO] DB connection successfully established: "{url_db_connection}"')
SQLModel.metadata.create_all(engine, tables=[Customers.__table__])

app = FastAPI(
    title="Bookstore API Service for Customers Data",
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


def create_customer(customer: Customers) -> None:
    with Session(engine) as session:
        session.add(customer)
        session.commit()


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


def background_task_produce_kafka_message(json_message: str):
    produce_kafka_message(json_message)


# =========
# Customers
# =========
@app.post("/customers", tags=["customers"], status_code=status.HTTP_201_CREATED)
async def post_customers(
    customer_request_body: CustomerRequestBody, background_tasks: BackgroundTasks
):
    if not check_is_valid_email(customer_request_body.userId):
        return RESPONSE_INVALID_EMAIL

    if not check_is_valid_state_abbr(customer_request_body.state):
        return RESPONSE_INVALID_STATE

    if check_does_user_id_exist(customer_request_body.userId):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"message": "This user ID already exists in the system."},
        )

    customer = Customers(
        userId=customer_request_body.userId,
        name=customer_request_body.name,
        phone=customer_request_body.phone,
        address=customer_request_body.address,
        address2=customer_request_body.address2,
        city=customer_request_body.city,
        state=customer_request_body.state,
        zipcode=customer_request_body.zipcode,
    )
    create_customer(customer)
    customer = get_customer_by_userId(customer_request_body.userId)
    kafka_message = customer.model_dump_json()
    print(f"[INFO] Producing a kafka message: {kafka_message}")
    background_tasks.add_task(background_task_produce_kafka_message, kafka_message)
    return {
        "id": int(customer.customer_id),
        "userId": str(customer.userId),
        "name": str(customer.name),
        "phone": str(customer.phone),
        "address": str(customer.address),
        "address2": str(customer.address2),
        "city": str(customer.city),
        "state": str(customer.state),
        "zipcode": str(customer.zipcode),
    }


@app.get("/customers/{id}", tags=["customers"], status_code=status.HTTP_200_OK)
async def get_customers(id: int):
    customer = get_customer_by_id(id)
    if customer is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This ID does not exist."},
        )

    return {
        "id": int(customer.customer_id),
        "userId": str(customer.userId),
        "name": str(customer.name),
        "phone": str(customer.phone),
        "address": str(customer.address),
        "address2": str(customer.address2),
        "city": str(customer.city),
        "state": str(customer.state),
        "zipcode": str(customer.zipcode),
    }


@app.get("/customers", tags=["customers"], status_code=status.HTTP_200_OK)
async def get_customers_by_userId(userId):
    if not check_is_valid_email(userId):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Retrieval failed. Invalid email."},
        )

    customer = get_customer_by_userId(userId)
    if customer is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Retrieval failed. This email does not exist."},
        )

    return {
        "id": int(customer.customer_id),
        "userId": str(customer.userId),
        "name": str(customer.name),
        "phone": str(customer.phone),
        "address": str(customer.address),
        "address2": str(customer.address2),
        "city": str(customer.city),
        "state": str(customer.state),
        "zipcode": str(customer.zipcode),
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
