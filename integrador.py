import csv
import json
from datetime import datetime
from pathlib import Path

import requests


BASE_DIR = Path(__file__).resolve().parent
DATOS_DIR = BASE_DIR / "datos"
SALIDA_DIR = BASE_DIR / "salida"

PROVEEDOR_A = DATOS_DIR / "proveedor_a.json"
PROVEEDOR_B = DATOS_DIR / "proveedor_b.csv"

URL_BASE = "https://appsweb.quantaiot.co"
EQUIPO = "EQUIPO-10-APPSWEB"
URL_MEDICIONES = f"{URL_BASE}/api/v1/mediciones"
TIMEOUT = 10

SALIDA_DIR.mkdir(exist_ok=True)


def enviar_medicion(medicion):
    headers = {
        "Content-Type": "application/json",
        "X-Equipo": EQUIPO,
    }

    try:
        respuesta = requests.post(
            URL_MEDICIONES,
            headers=headers,
            json=medicion,
            timeout=TIMEOUT,
        )

        try:
            contenido = respuesta.json()
        except ValueError:
            contenido = respuesta.text

        return respuesta.status_code, contenido

    except requests.exceptions.Timeout:
        return None, "Timeout"

    except requests.exceptions.RequestException as error:
        return None, f"Error de comunicación: {error}"


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

            normalizadas.append(
                {
                    "trazabilidad": trazabilidad,
                    "medicion": normalizado,
                }
            )

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

            normalizadas.append(
                {
                    "trazabilidad": trazabilidad,
                    "medicion": normalizado,
                }
            )

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


def validar_medicion(medicion):
    errores = []

    if not medicion["ciudad"].strip():
        errores.append("ciudad vacía")

    if not medicion["pais"].strip():
        errores.append("pais vacío")

    if not -90 <= medicion["latitud"] <= 90:
        errores.append("latitud fuera de rango")

    if not -180 <= medicion["longitud"] <= 180:
        errores.append("longitud fuera de rango")

    if not 0 <= medicion["humedad"] <= 100:
        errores.append("humedad fuera de rango")

    if medicion["viento_kmh"] < 0:
        errores.append("viento negativo")

    try:
        datetime.fromisoformat(medicion["fecha_hora"])
    except (TypeError, ValueError):
        errores.append("fecha_hora inválida")

    if medicion["origen"] not in {"proveedor_a", "proveedor_b"}:
        errores.append("origen no permitido")

    return errores


def validar_registros(normalizadas):
    validos = []
    rechazados_localmente = []

    for registro in normalizadas:
        errores = validar_medicion(registro["medicion"])

        if errores:
            rechazados_localmente.append(
                {
                    "trazabilidad": registro["trazabilidad"],
                    "origen": registro["medicion"]["origen"],
                    "tipo": "rechazado_localmente",
                    "detalle": errores,
                }
            )
        else:
            validos.append(registro)

    return validos, rechazados_localmente


def guardar_normalizadas(registros):
    archivo_salida = SALIDA_DIR / "normalizadas.json"

    datos = []

    for registro in registros:
        datos.append(
            {
                "trazabilidad": registro["trazabilidad"],
                **registro["medicion"],
            }
        )

    with open(archivo_salida, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)


def main():
    registros_a = leer_proveedor_a()
    registros_b = leer_proveedor_b()

    total_procesados = len(registros_a) + len(registros_b)

    normalizadas, errores_normalizacion = normalizar_registros(
        registros_a, registros_b
    )

    validos, rechazados_localmente = validar_registros(normalizadas)

    if validos:
        registro_prueba = validos[0]

        codigo, respuesta = enviar_medicion(registro_prueba["medicion"])

        print()
        print("Prueba de envío HTTP:")
        print(f"Registro: {registro_prueba['trazabilidad']}")
        print(f"Código HTTP: {codigo}")
        print(f"Respuesta: {respuesta}")

    guardar_normalizadas(normalizadas)

    print()
    print(f"Proveedor A: {len(registros_a)} registros")
    print(f"Proveedor B: {len(registros_b)} registros")
    print(f"Total procesados: {total_procesados}")
    print(f"Registros normalizados: {len(normalizadas)}")
    print(f"Errores de normalización: {len(errores_normalizacion)}")
    print(f"Válidos localmente: {len(validos)}")
    print(f"Rechazados localmente: {len(rechazados_localmente)}")

    print()
    print("Rechazados localmente:")

    for registro in rechazados_localmente:
        print(
            f"- {registro['trazabilidad']} "
            f"({registro['origen']}): "
            f"{', '.join(registro['detalle'])}"
        )

    print()
    print("Archivo generado:")
    print(SALIDA_DIR / "normalizadas.json")


if __name__ == "__main__":
    main()
    