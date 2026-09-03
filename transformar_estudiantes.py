import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RUTA_CSV = BASE_DIR / "datos" / "estudiantes.csv"

with open(RUTA_CSV, encoding="utf-8") as archivo:
    lector = csv.DictReader(archivo)
    estudiantes = list(lector)


def transformar_estudiante(estudiante: dict) -> dict:
    return {
        "id": estudiante["codigo"],
        "nombre_completo": f'{estudiante["nombre"]} {estudiante["apellido"]}',
        "semestre": int(estudiante["semestre"]),
        "promedio": float(estudiante["promedio"]),
        "estado": "Activo" if estudiante["activo"] == "true" else "Inactivo"
    }


def serializar_estudiantes(ruta: Path, estudiantes: list[dict]) -> None:
    """Serializa una lista de diccionarios Python a un archivo JSON UTF-8."""
    ruta.parent.mkdir(exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(estudiantes, archivo, indent=2, ensure_ascii=False)

def deserializar_estudiantes(ruta: Path) -> list[dict]:
    """Deserializa un archivo JSON a una lista de diccionarios Python."""
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)

estudiantes_transformados = [
    transformar_estudiante(estudiante)
    for estudiante in estudiantes
]


RUTA_JSON = BASE_DIR / "salida" / "estudiantes_resumen.json"

serializar_estudiantes(RUTA_JSON, estudiantes_transformados)
print(f"Archivo JSON generado: {RUTA_JSON}")

estudiantes_recuperados = deserializar_estudiantes(RUTA_JSON)

print("\nDatos recuperados desde el JSON:")
print(estudiantes_recuperados[0])
print(f"Total recuperado: {len(estudiantes_recuperados)}")