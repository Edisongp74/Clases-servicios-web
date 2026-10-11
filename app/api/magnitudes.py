
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.sensor_magnitud import SensorMagnitud
from app.schemas.sensor_magnitud import SensorMagnitudResponse

router = APIRouter(prefix="/magnitudes", tags=["Magnitudes"])


@router.get("/", response_model=list[SensorMagnitudResponse])
def listar_magnitudes(db: Session = Depends(get_db)):
    return (
        db.query(SensorMagnitud)
        .order_by(SensorMagnitud.sensor_id, SensorMagnitud.id)
        .all()
    )


@router.get("/{magnitud_id}", response_model=SensorMagnitudResponse)
def obtener_magnitud(magnitud_id: int, db: Session = Depends(get_db)):
    magnitud = (
        db.query(SensorMagnitud)
        .filter(SensorMagnitud.id == magnitud_id)
        .first()
    )

    if magnitud is None:
        raise HTTPException(status_code=404, detail="Magnitud no encontrada")

    return magnitud
