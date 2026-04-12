import json
import os

from confluent_kafka import Consumer
from wrapper_email import send_email

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

# =============
# Kafka Configs
# =============
c = Consumer({
    "bootstrap.servers": [KAFKA_BROKER_0_URL, KAFKA_BROKER_1_URL, KAFKA_BROKER_2_URL],
})


def main():
    c.subscribe([KAFKA_TOPIC])
    listen_for_kafka_messages()
    c.close()


def listen_for_kafka_messages():
    while True:
        msg = c.poll(1.0)

        if msg is None:
            print("hi")
            continue
        if msg.error():
            print(f"[ERROR] {msg.error()}")
            continue

        message = msg.value().decode("utf-8")
        print("[INFO] Received message: {message}")
        message_parsed = json.loads(message)
        print("[INFO] Parsed message: {message_parsed}")
        customer_email = message_parsed["userId"]
        print("[INFO] Customer Email: {customer_email}")
        customer_name = message_parsed["name"]
        print("[INFO] Customer Email: {customer_name}")

        email_body = f"Dear {customer_name},\nWelcome to the Book store created by soobinr.\nExceptionally this time we won’t ask you to click a link to activate your account.\n"
        send_email(
            email_body=email_body,
            email_to=customer_email,
            email_subject="Activate your book store account",
        )


if __name__ == "__main__":
    main()
