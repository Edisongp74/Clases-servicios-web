from app.api.magnitudes import router as magnitudes_router
import app.models
from app.api.mediciones import router as mediciones_router
from fastapi import FastAPI

from app.api.sensores import router as sensores_router

app = FastAPI(
    title="API de Monitoreo de Sensores",
    description="API para consultar sensores y registrar mediciones.",
    version="1.0.0",
)


@app.get("/")
def inicio():
    return {
        "mensaje": "API de monitoreo de sensores funcionando",
        "estado": "correcto",
    }


@app.get("/health")
def health():
    return {"estado": "activo"}

app.include_router(mediciones_router)
app.include_router(sensores_router)
app.include_router(magnitudes_router)