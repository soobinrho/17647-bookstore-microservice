import os

from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse

# from app.shared_library.emails import (
# )
from .metadata import contact, description, tags_metadata

KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", None)
KAFKA_BROKER_0_URL = os.environ.get("KAFKA_BROKER_0_URL", None)
KAFKA_BROKER_1_URL = os.environ.get("KAFKA_BROKER_1_URL", None)
KAFKA_BROKER_2_URL = os.environ.get("KAFKA_BROKER_2_URL", None)
if (
    KAFKA_TOPIC is None
    or KAFKA_BROKER_0_URL is None
    or KAFKA_BROKER_1_URL is None
    or KAFKA_BROKER_2_URL is None
):
    raise Exception(
        "[ERROR] Required credentials were not found in the environment variables"
    )

app = FastAPI(
    title="Bookstore API Service for Customers Data",
    description=description,
    tags_metadata=tags_metadata,
    contact=contact,
)


# =========
# Customers
# =========


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
