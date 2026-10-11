
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.sensor import Sensor
from app.schemas.sensor import SensorResponse

router = APIRouter(prefix="/sensores", tags=["Sensores"])


@router.get("/", response_model=list[SensorResponse])
def listar_sensores(db: Session = Depends(get_db)):
    return db.query(Sensor).order_by(Sensor.id).all()
