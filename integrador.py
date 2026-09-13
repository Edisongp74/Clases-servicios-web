import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATOS_DIR = BASE_DIR / "datos"

PROVEEDOR_A = DATOS_DIR / "proveedor_a.json"
PROVEEDOR_B = DATOS_DIR / "proveedor_b.csv"


def leer_proveedor_a():
    with open(PROVEEDOR_A, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    return datos["records"]


def leer_proveedor_b():
    with open(PROVEEDOR_B, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo, delimiter=";")
        return list(lector)


def main():
    registros_a = leer_proveedor_a()
    registros_b = leer_proveedor_b()

    total = len(registros_a) + len(registros_b)

    print(f"Proveedor A: {len(registros_a)} registros")
    print(f"Proveedor B: {len(registros_b)} registros")
    print(f"Total procesados: {total}")


if __name__ == "__main__":
    main() 