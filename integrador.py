import csv
import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATOS_DIR = BASE_DIR / "datos"
SALIDA_DIR = BASE_DIR / "salida"

PROVEEDOR_A = DATOS_DIR / "proveedor_a.json"
PROVEEDOR_B = DATOS_DIR / "proveedor_b.csv"

SALIDA_DIR.mkdir(exist_ok=True)


def leer_proveedor_a():
    with open(PROVEEDOR_A, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    return datos["records"]


def leer_proveedor_b():
    with open(PROVEEDOR_B, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo, delimiter=";")
        return list(lector)


def convertir_fahrenheit_a_celsius(valor):
    return (float(valor) - 32) * 5 / 9


def convertir_ms_a_kmh(valor):
    return float(valor) * 3.6


def normalizar_fecha_a(fecha):
    return datetime.fromisoformat(fecha).isoformat()


def normalizar_fecha_b(fecha):
    return datetime.strptime(fecha, "%d/%m/%Y %H:%M").isoformat()


def normalizar_proveedor_a(registro):
    try:
        return {
            "ciudad": registro["station"]["city_name"],
            "pais": registro["station"]["country_code"],
            "latitud": float(registro["location"]["lat"]),
            "longitud": float(registro["location"]["lon"]),
            "temperatura_c": convertir_fahrenheit_a_celsius(
                registro["measurements"]["temperature_f"]
            ),
            "humedad": float(registro["measurements"]["relative_humidity"]),
            "viento_kmh": convertir_ms_a_kmh(
                registro["measurements"]["wind_speed_ms"]
            ),
            "fecha_hora": normalizar_fecha_a(registro["observed_at"]),
            "origen": "proveedor_a",
        }

    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"No se pudo normalizar el registro: {error}")


def normalizar_proveedor_b(registro):
    try:
        return {
            "ciudad": registro["municipality"],
            "pais": registro["country"],
            "latitud": float(registro["latitude_deg"]),
            "longitud": float(registro["longitude_deg"]),
            "temperatura_c": float(registro["temp_celsius"]),
            "humedad": float(registro["humidity_pct"]),
            "viento_kmh": float(registro["wind_kmh"]),
            "fecha_hora": normalizar_fecha_b(registro["measurement_time"]),
            "origen": "proveedor_b",
        }

    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"No se pudo normalizar el registro: {error}")


def normalizar_registros(registros_a, registros_b):
    normalizadas = []
    errores_normalizacion = []

    for registro in registros_a:
        trazabilidad = registro.get("provider_record_id", "sin_id")

        try:
            normalizado = normalizar_proveedor_a(registro)
            normalizadas.append(normalizado)
        except ValueError as error:
            errores_normalizacion.append(
                {
                    "trazabilidad": trazabilidad,
                    "origen": "proveedor_a",
                    "tipo": "error_normalizacion",
                    "detalle": str(error),
                }
            )

    for registro in registros_b:
        trazabilidad = registro.get("record_code", "sin_id")

        try:
            normalizado = normalizar_proveedor_b(registro)
            normalizadas.append(normalizado)
        except ValueError as error:
            errores_normalizacion.append(
                {
                    "trazabilidad": trazabilidad,
                    "origen": "proveedor_b",
                    "tipo": "error_normalizacion",
                    "detalle": str(error),
                }
            )

    return normalizadas, errores_normalizacion


def guardar_normalizadas(registros):
    archivo_salida = SALIDA_DIR / "normalizadas.json"

    with open(archivo_salida, "w", encoding="utf-8") as archivo:
        json.dump(registros, archivo, ensure_ascii=False, indent=2)


def main():
    registros_a = leer_proveedor_a()
    registros_b = leer_proveedor_b()

    total_procesados = len(registros_a) + len(registros_b)

    normalizadas, errores_normalizacion = normalizar_registros(
        registros_a, registros_b
    )

    guardar_normalizadas(normalizadas)

    print(f"Proveedor A: {len(registros_a)} registros")
    print(f"Proveedor B: {len(registros_b)} registros")
    print(f"Total procesados: {total_procesados}")
    print(f"Registros normalizados: {len(normalizadas)}")
    print(f"Errores de normalización: {len(errores_normalizacion)}")
    print()
    print("Errores encontrados:")

    for error in errores_normalizacion:
        print(
            f"- {error['trazabilidad']} "
            f"({error['origen']}): {error['detalle']}"
        )

    print()
    print("Archivo generado:")
    print(SALIDA_DIR / "normalizadas.json")


if __name__ == "__main__":
    main()