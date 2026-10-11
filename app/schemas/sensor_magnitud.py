
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SensorMagnitudResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_id: int
    magnitud: str
    unidad: str
    valor_minimo: Decimal
    valor_maximo: Decimal
