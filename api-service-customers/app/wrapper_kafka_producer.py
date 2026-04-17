import os

from confluent_kafka import Producer

from app.shared_library.input_data_validations import sanitize_env_var

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


# K8s includes something like DB_USER='...' to include the quotes themselves too.
# Thus, sanitize it so that the env vars do not start with or end with quotes.
KAFKA_TOPIC = sanitize_env_var(KAFKA_TOPIC)
KAFKA_BROKER_0_URL = sanitize_env_var(KAFKA_BROKER_0_URL)
KAFKA_BROKER_1_URL = sanitize_env_var(KAFKA_BROKER_1_URL)
KAFKA_BROKER_2_URL = sanitize_env_var(KAFKA_BROKER_2_URL)


def callback_kafka(err, msg):
    if err:
        print(f"[ERROR] {err}")
    else:
        try:
            print(
                f"[INFO] Kafka message successfully produced and consumed: {msg.value().decode('UTF-8')}"
            )
        except Exception as e:
            print(f"[ERROR] {e}")


def produce_kafka_message(json_message: str):
    # Source: https://developer.confluent.io/get-started/python/?utm_medium=sem&utm_source=google&utm_campaign=ch.sem_br.nonbrand_tp.prs_tgt.dsa_mt.dsa_rgn.namer_sbrgn.unitedstates_lng.eng_dv.all_con.confluent-developer&utm_term=&creative=&device=c&placement=&gad_source=1&gad_campaignid=19560855036&gbraid=0AAAAADRv2c2_QRTDnd_1dqGksH_Qbrbri&gclid=CjwKCAjwhe3OBhABEiwA6392zCiEHG8BZfriWhuPlmVjPWZKNr8zCdr_CRqZ5kxNP5wZxj_JGi04ZhoCaGQQAvD_BwE#build-producer
    config = {
        "bootstrap.servers": ",".join([
            KAFKA_BROKER_0_URL,
            KAFKA_BROKER_1_URL,
            KAFKA_BROKER_2_URL,
        ])
    }
    producer = Producer(config)
    producer.produce(KAFKA_TOPIC, json_message, callback=callback_kafka)
    producer.flush()
