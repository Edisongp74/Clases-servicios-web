
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.crud.mediciones import registrar_mediciones
from app.schemas.medicion import MedicionResponse, MqttPayload

router = APIRouter(prefix="/mediciones", tags=["Mediciones"])


@router.post("/", response_model=list[MedicionResponse], status_code=201)
def crear_mediciones(
    payload: MqttPayload,
    db: Session = Depends(get_db),
):
    try:
        return registrar_mediciones(db, payload)
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="No fue posible registrar las mediciones",
        ) from error
