
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.medicion import Medicion
from app.models.sensor import Sensor
from app.models.sensor_magnitud import SensorMagnitud
from app.schemas.medicion import MqttPayload


def registrar_mediciones(
    db: Session,
    payload: MqttPayload,
) -> list[Medicion]:
    sensor = (
        db.query(Sensor)
        .filter(Sensor.codigo == payload.sensor_id)
        .first()
    )

    if sensor is None:
        raise ValueError("El sensor indicado no existe")

    if not sensor.activo:
        raise ValueError("El sensor está inactivo")

    timestamp = payload.timestamp.astimezone(timezone.utc)
    nuevas_mediciones = []

    try:
        for nombre_magnitud, dato in payload.measurements.items():
            magnitud = (
                db.query(SensorMagnitud)
                .filter(
                    SensorMagnitud.sensor_id == sensor.id,
                    SensorMagnitud.magnitud == nombre_magnitud,
                )
                .first()
            )

            if magnitud is None:
                raise ValueError(
                    f"La magnitud '{nombre_magnitud}' no pertenece al sensor"
                )

            if dato.unit != magnitud.unidad:
                raise ValueError(
                    f"Unidad incorrecta para '{nombre_magnitud}'. "
                    f"Se esperaba '{magnitud.unidad}'"
                )

            valor = Decimal(str(dato.value))

            if not (
                magnitud.valor_minimo
                <= valor
                <= magnitud.valor_maximo
            ):
                raise ValueError(
                    f"El valor de '{nombre_magnitud}' está fuera de rango"
                )

            medicion = Medicion(
                sensor_magnitud_id=magnitud.id,
                valor=valor,
                timestamp_utc=timestamp,
            )

            db.add(medicion)
            nuevas_mediciones.append(medicion)

        db.commit()

        for medicion in nuevas_mediciones:
            db.refresh(medicion)

        return nuevas_mediciones

    except Exception:
        db.rollback()
        raise
