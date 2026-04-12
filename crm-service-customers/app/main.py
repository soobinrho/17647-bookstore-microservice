import os

from confluent_kafka import Consumer

from .wrapper_email import send_email

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

c.subscribe([KAFKA_TOPIC])

while True:
    msg = c.poll(1.0)

    if msg is None:
        continue
    if msg.error():
        print("Consumer error: {}".format(msg.error()))
        continue

    print("Received message: {}".format(msg.value().decode("utf-8")))

    if False:
        customer_email = "soobinrho@gmail.com"
        customer_name = "Soobin Rho"
        email_body = f"Dear {customer_name},\nWelcome to the Book store created by soobinr.\nExceptionally this time we won’t ask you to click a link to activate your account.\n"
        send_email(
            email_body=email_body,
            email_to=customer_email,
            email_subject="Activate your book store account",
        )

c.close()
