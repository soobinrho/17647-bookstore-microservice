from fastapi import FastAPI, status, Response
from fastapi.responses import JSONResponse


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
    }
]

app = FastAPI(
    title="Bookstore API Backend",
    description=description,
    contact={
        "name": "Soobin Rho",
        "url": "https://github.com/soobinrho",
        "email": "soobinrho@gmail.com",
    }
)


# =====
# Books
# =====
@app.get("/books", tags=["books"])
async def get_placeholder():
  return [{"name": "value"}]

# =========
# Customers
# =========
@app.get("/customers", tags=["customers"])
async def get_placeholder():
  return [{"name": "value"}]

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


