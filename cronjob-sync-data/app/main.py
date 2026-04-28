import asyncio
import signal
import time

import pymongo
from pymongo import AsyncMongoClient
from shared_library.constants import (
    COLNAME_AUTHOR,
    COLNAME_DESCRIPTION,
    COLNAME_GENRE,
    COLNAME_ISBN,
    COLNAME_LAST_UPDATED_DATETIME_UNIX_EPOCH,
    COLNAME_PRICE,
    COLNAME_QUANTITY,
    COLNAME_SUMMARY,
    COLNAME_TITLE,
)
from shared_library.models import Books
from shared_library.utils import get_env_vars_for_cronjob_sync_data
from sqlalchemy import URL
from sqlmodel import Session, SQLModel, create_engine, select

CONFIGS = get_env_vars_for_cronjob_sync_data()

# Reference: https://docs.sqlalchemy.org/en/21/core/engines.html#creating-urls-programmatically
url_db_connection = URL.create(
    "mysql+pymysql",
    username=CONFIGS["DB_BOOKS_COMMANDS_USER"],
    password=CONFIGS["DB_BOOKS_COMMANDS_PASS"],
    host=CONFIGS["DB_BOOKS_COMMANDS_URL"],
    port=CONFIGS["DB_BOOKS_COMMANDS_PORT"],
    database=CONFIGS["DB_BOOKS_COMMANDS_DATABASE"],
)
engine = create_engine(url_db_connection, echo=False)
SQLModel.metadata.create_all(engine, tables=[Books.__table__])

str_db_connection = None
if not CONFIGS["IS_DEV"]:
    str_db_connection = f"mongodb+srv://{CONFIGS['DB_BOOKS_QUERIES_USER']}:{CONFIGS['DB_BOOKS_QUERIES_PASS']}@{CONFIGS['DB_BOOKS_QUERIES_URL']}"
else:
    str_db_connection = f"mongodb://{CONFIGS['DB_BOOKS_QUERIES_USER']}:{CONFIGS['DB_BOOKS_QUERIES_PASS']}@{CONFIGS['DB_BOOKS_QUERIES_URL']}:{CONFIGS['DB_BOOKS_QUERIES_PORT']}"
db_client = AsyncMongoClient(
    str_db_connection, server_api=pymongo.server_api.ServerApi(version="1")
)
db = db_client.get_database(CONFIGS["DB_BOOKS_QUERIES_DATABASE"])
db_collection = db.get_collection(CONFIGS["DB_BOOKS_QUERIES_COLLECTION"])


def get_all_books_from_primary_data_store() -> list | None:
    with Session(engine) as session:
        # `Scalars` instead of `execute` because `execute` returns row objects instead.
        rows = session.scalars(select(Books))
        books = []
        for book in rows:
            books.append(book)
        return books


def get_async_cursor_books():
    async_cursor = db_collection.find(
        {}, {COLNAME_ISBN: 1, COLNAME_LAST_UPDATED_DATETIME_UNIX_EPOCH: 1}
    )
    return async_cursor


async def get_dict_all_books_and_their_last_updated_datetime_from_query_view() -> dict:
    async_cursor = get_async_cursor_books()
    dict_books_and_last_updated_datetime = {}
    async for book in async_cursor:
        dict_books_and_last_updated_datetime[book[COLNAME_ISBN]] = book[
            COLNAME_LAST_UPDATED_DATETIME_UNIX_EPOCH
        ]
    return dict_books_and_last_updated_datetime


async def add_or_update_book_from_query_view(book: Books):
    await db_collection.update_one(
        {COLNAME_ISBN: book.ISBN},
        {
            "$set": {
                COLNAME_TITLE: book.title,
                COLNAME_AUTHOR: book.Author,
                COLNAME_DESCRIPTION: book.description,
                COLNAME_GENRE: book.genre,
                COLNAME_PRICE: book.price,
                COLNAME_QUANTITY: book.quantity,
                COLNAME_SUMMARY: book.summary,
                COLNAME_LAST_UPDATED_DATETIME_UNIX_EPOCH: book.last_updated_datetime_unix_epoch,
            }
        },
        upsert=True,
    )


async def delete_book_from_query_view(ISBN: str):
    ISBN = str(ISBN)
    await db_collection.delete_one({COLNAME_ISBN: ISBN})


# Source: https://stackoverflow.com/a/31464349
class class_sig_term_handler:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


async def main():
    await db_collection.create_index([(COLNAME_ISBN, pymongo.ASCENDING)], unique=True)
    period = CONFIGS["SYNC_DATA_PERIOD_SECONDS"]
    try:
        period = int(period)
    except Exception:
        period = 60
    sig_term_handler = class_sig_term_handler()
    while not sig_term_handler.kill_now:
        books_primary = get_all_books_from_primary_data_store()
        dict_books_view = (
            await get_dict_all_books_and_their_last_updated_datetime_from_query_view()
        )
        set_should_this_book_be_deleted = set()
        for ISBN in dict_books_view:
            set_should_this_book_be_deleted.add(ISBN)

        # 1. Add or update the books depending on last_updated_datetime.
        for book in books_primary:
            ISBN = book.ISBN
            should_add_or_update = False
            if ISBN not in dict_books_view:
                should_add_or_update = True
            else:
                last_updated_primary = int(book.last_updated_datetime_unix_epoch)
                last_updated_view = int(dict_books_view[ISBN])
                if last_updated_view < last_updated_primary:
                    should_add_or_update = True
            if should_add_or_update:
                await add_or_update_book_from_query_view(book)
                print(f"[INFO] Successfully added or updated a book: ISBN = {ISBN}")
            else:
                print(
                    f"[INFO] Successfully checked a book is up-to-date: ISBN = {ISBN}"
                )
            set_should_this_book_be_deleted.discard(ISBN)

        # 2. Delete if the book doesn't exist on the primary data store anymore.
        for ISBN in list(set_should_this_book_be_deleted):
            await delete_book_from_query_view(ISBN)
            print(f"[INFO] Successfully deleted a deprecated book: ISBN = {ISBN}")

        print(f"[INFO] Sleeping for {period} seconds...")
        for _ in range(period):
            time.sleep(1)
            if sig_term_handler.kill_now:
                break


if __name__ == "__main__":
    asyncio.run(main())
