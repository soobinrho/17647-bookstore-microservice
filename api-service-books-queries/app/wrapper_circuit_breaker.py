import datetime
import time

from sqlalchemy import URL
from sqlmodel import Session, SQLModel, create_engine

from app.shared_library.models import Misc
from app.shared_library.utils import get_env_vars_for_circuit_breaker

CONFIGS = get_env_vars_for_circuit_breaker()
CIRCUIT_BREAKER_WAIT_HOW_LONG = 60  # Seconds.
MISC_KEY_WHEN_OPEN = "when_circuit_breaker_open"

url_db_connection = URL.create(
    "mysql+pymysql",
    username=CONFIGS["DB_BOOKS_COMMANDS_USER"],
    password=CONFIGS["DB_BOOKS_COMMANDS_PASS"],
    host=CONFIGS["DB_BOOKS_COMMANDS_URL"],
    port=CONFIGS["DB_BOOKS_COMMANDS_PORT"],
    database=CONFIGS["DB_BOOKS_COMMANDS_DATABASE"],
)
engine = create_engine(url_db_connection, echo=False)
SQLModel.metadata.create_all(engine, tables=[Misc.__table__])


# Professor Merson's instruction hinted that we could use K8s Volume
# functionality. I opted to use the already-available AWS Aurora cluster
# for the circuit breaker's data storage requirement. Tradeoffs is that
# relying on a database increases outbound coupling. However, what I gain
# by doing so is that I can use an existing data storage and I therefore
# don't have to implement a new mechanism just for the circuit breaker.
def check_circuit_breaker_open() -> bool:
    with Session(engine) as session:
        # Circuit breaker closed = Service functioning as expected.
        # Circuit breaker open = Service malfunctioning.
        when_circuit_breaker_open = session.get(Misc, MISC_KEY_WHEN_OPEN)
        if when_circuit_breaker_open is None:
            return False
        else:
            return True


def check_should_circuit_breaker_close() -> bool:
    with Session(engine) as session:
        when_circuit_breaker_open = session.get(Misc, MISC_KEY_WHEN_OPEN)
        when_open = int(when_circuit_breaker_open.misc_value)
        when_open = datetime.datetime.fromtimestamp(when_open)
        when_recheck = when_open + datetime.timedelta(
            seconds=CIRCUIT_BREAKER_WAIT_HOW_LONG
        )
        datetime_now = datetime.datetime.now()
        if when_recheck < datetime_now:
            return True
        else:
            return False


def get_unix_epoch_now() -> int:
    return int(time.time())


def reset_circuit_breaker_time() -> None:
    with Session(engine) as session:
        when_circuit_breaker_open = session.get(Misc, MISC_KEY_WHEN_OPEN)
        when_circuit_breaker_open.misc_value = f"{get_unix_epoch_now()}"
        session.add(when_circuit_breaker_open)
        session.commit()


def close_circuit_breaker() -> None:
    with Session(engine) as session:
        when_circuit_breaker_open = session.get(Misc, MISC_KEY_WHEN_OPEN)
        session.delete(when_circuit_breaker_open)
        session.commit()


def open_circuit_breaker() -> None:
    with Session(engine) as session:
        when_circuit_breaker_open = Misc(
            misc_key=MISC_KEY_WHEN_OPEN,
            misc_value=f"{get_unix_epoch_now()}",
        )
        session.add(when_circuit_breaker_open)
        session.commit()
