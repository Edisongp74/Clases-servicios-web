
import json
import logging
import os

import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from pydantic import ValidationError

from app.database.connection import SessionLocal
from app.schemas.medicion import MqttPayload
from app.crud.mediciones import registrar_mediciones


load_dotenv()

BROKER = os.getenv("MQTT_BROKER", "emqx.coriotlab.co")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "")
USERNAME = os.getenv("MQTT_USERNAME") or None
PASSWORD = os.getenv("MQTT_PASSWORD") or None
KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        logger.error("No se pudo conectar a MQTT: %s", reason_code)
        return

    logger.info("Conectado a %s:%s", BROKER, PORT)
    client.subscribe(TOPIC)
    logger.info("Suscrito al tópico: %s", TOPIC)


def on_message(client, userdata, message):
    db = SessionLocal()

    try:
        contenido = message.payload.decode("utf-8")
        datos = json.loads(contenido)
        payload = MqttPayload.model_validate(datos)

        if payload.sensor_id != "GAS-007":
            logger.warning(
                "Mensaje ignorado: sensor recibido %s",
                payload.sensor_id,
            )
            return

        mediciones = registrar_mediciones(db, payload)

        logger.info(
            "Mensaje válido de %s: %s mediciones guardadas",
            payload.sensor_id,
            len(mediciones),
        )

    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, ValueError) as error:
        logger.warning("Mensaje rechazado: %s", error)

    except Exception:
        logger.exception("Error inesperado procesando el mensaje MQTT")

    finally:
        db.close()


def main():
    if not TOPIC.strip():
        raise RuntimeError(
            "MQTT_TOPIC está vacío. Configura el tópico asignado antes de ejecutar."
        )

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    if USERNAME:
        client.username_pw_set(USERNAME, PASSWORD or "")

    client.on_connect = on_connect
    client.on_message = on_message

    logger.info("Conectando a %s:%s...", BROKER, PORT)
    client.connect(BROKER, PORT, KEEPALIVE)
    client.loop_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Consumidor MQTT detenido")
