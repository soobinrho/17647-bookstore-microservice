import json
import os
import signal

from confluent_kafka import Consumer
from wrapper_email import send_email

from app.shared_library.input_data_validations import sanitize_env_var

KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", None)
KAFKA_BROKER_0_URL = os.environ.get("KAFKA_BROKER_0_URL", None)
KAFKA_BROKER_1_URL = os.environ.get("KAFKA_BROKER_1_URL", None)
KAFKA_BROKER_2_URL = os.environ.get("KAFKA_BROKER_2_URL", None)

list_env_vars = [
    KAFKA_TOPIC,
    KAFKA_BROKER_0_URL,
    KAFKA_BROKER_1_URL,
    KAFKA_BROKER_2_URL,
]
should_raise_exception = False
for env_var in list_env_vars:
    if env_var is None:
        print(f"[ERROR] {env_var} = None")
        should_raise_exception = True
if should_raise_exception:
    raise Exception(
        "[ERROR] Required credentials were not found in the environment variables"
    )

# K8s includes something like DB_USER='...' to include the quotes themselves too.
# Thus, sanitize it so that the env vars do not start with or end with quotes.
KAFKA_TOPIC = sanitize_env_var(KAFKA_TOPIC)
KAFKA_BROKER_0_URL = sanitize_env_var(KAFKA_BROKER_0_URL)
KAFKA_BROKER_1_URL = sanitize_env_var(KAFKA_BROKER_1_URL)
KAFKA_BROKER_2_URL = sanitize_env_var(KAFKA_BROKER_2_URL)


# Source: https://stackoverflow.com/a/31464349
class class_sig_term_handler:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


def main():
    print(f"[INFO] Starting to listen for the Kafka topic {KAFKA_TOPIC}")
    consumer = Consumer({
        "bootstrap.servers": ",".join([
            KAFKA_BROKER_0_URL,
            KAFKA_BROKER_1_URL,
            KAFKA_BROKER_2_URL,
        ]),
        "group.id": "customers",
    })
    consumer.subscribe([KAFKA_TOPIC])
    sig_term_handler = class_sig_term_handler()
    while not sig_term_handler.kill_now:
        msg = consumer.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            print(f"[ERROR] {msg.error()}")
            continue

        message = msg.value().decode("utf-8")
        print(f"[INFO] Received message: {message}")
        message_parsed = json.loads(message)
        customer_email = message_parsed["userId"]
        print(f"[INFO] Customer Email: {customer_email}")
        customer_name = message_parsed["name"]
        print(f"[INFO] Customer Name: {customer_name}")
        email_body = f"Dear {customer_name},\nWelcome to the Book store created by soobinr.\nExceptionally this time we won’t ask you to click a link to activate your account.\n"
        print(f"[INFO] Email Body: {email_body}")
        send_email(
            email_body=email_body,
            email_to=customer_email,
            email_subject="Activate your book store account",
        )
    consumer.close()


if __name__ == "__main__":
    main()
