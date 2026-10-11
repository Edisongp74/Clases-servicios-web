
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.sensor import Sensor
from app.models.sensor_magnitud import SensorMagnitud
from app.models.medicion import Medicion
from app.schemas.sensor import SensorResponse
from app.schemas.sensor_magnitud import SensorMagnitudResponse
from app.schemas.medicion import MedicionResponse

router = APIRouter(prefix="/sensores", tags=["Sensores"])


@router.get("/", response_model=list[SensorResponse])
def listar_sensores(db: Session = Depends(get_db)):
    return db.query(Sensor).order_by(Sensor.id).all()


@router.get("/por-codigo/{codigo}", response_model=SensorResponse)
def obtener_sensor_por_codigo(codigo: str, db: Session = Depends(get_db)):
    sensor = db.query(Sensor).filter(Sensor.codigo == codigo).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return sensor


@router.get("/{sensor_id}", response_model=SensorResponse)
def obtener_sensor(sensor_id: int, db: Session = Depends(get_db)):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return sensor


@router.get("/{sensor_id}/magnitudes", response_model=list[SensorMagnitudResponse])
def listar_magnitudes_sensor(sensor_id: int, db: Session = Depends(get_db)):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    return (
        db.query(SensorMagnitud)
        .filter(SensorMagnitud.sensor_id == sensor_id)
        .order_by(SensorMagnitud.id)
        .all()
    )


@router.get("/{sensor_id}/mediciones", response_model=list[MedicionResponse])
def listar_mediciones_sensor(
    sensor_id: int,
    magnitud: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    consulta = (
        db.query(Medicion)
        .join(SensorMagnitud, Medicion.sensor_magnitud_id == SensorMagnitud.id)
        .filter(SensorMagnitud.sensor_id == sensor_id)
    )

    if magnitud:
        consulta = consulta.filter(SensorMagnitud.magnitud == magnitud)
    if desde:
        consulta = consulta.filter(Medicion.timestamp_utc >= desde)
    if hasta:
        consulta = consulta.filter(Medicion.timestamp_utc <= hasta)

    return (
        consulta.order_by(Medicion.timestamp_utc.desc())
        .limit(limit)
        .all()
    )


@router.get("/{sensor_id}/ultima-medicion", response_model=MedicionResponse)
def obtener_ultima_medicion(sensor_id: int, db: Session = Depends(get_db)):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    medicion = (
        db.query(Medicion)
        .join(SensorMagnitud, Medicion.sensor_magnitud_id == SensorMagnitud.id)
        .filter(SensorMagnitud.sensor_id == sensor_id)
        .order_by(Medicion.timestamp_utc.desc(), Medicion.id.desc())
        .first()
    )

    if medicion is None:
        raise HTTPException(status_code=404, detail="El sensor no tiene mediciones")

    return medicion
