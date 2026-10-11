
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer


class MeasurementInput(BaseModel):
    value: Annotated[float, Field(allow_inf_nan=False)]
    unit: str = Field(min_length=1, max_length=20)


class MqttPayload(BaseModel):
    sensor_id: str = Field(min_length=1, max_length=20)
    timestamp: datetime
    measurements: dict[str, MeasurementInput] = Field(min_length=1)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("El timestamp debe incluir zona horaria")
        return value


class MedicionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_magnitud_id: int
    valor: Decimal
    timestamp_utc: datetime
    fecha_recepcion: datetime

    @field_serializer("timestamp_utc", "fecha_recepcion")
    def convertir_a_hora_colombia(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(ZoneInfo("America/Bogota"))
