
from pathlib import Path

import joblib
from sklearn.tree import export_text


RAIZ = Path(__file__).resolve().parents[2]

RUTA_MODELO = RAIZ / "resultados" / "modelo_arbol.joblib"

RUTA_REGLAS = RAIZ / "docs" / "reglas_aprendidas.txt"


def cargar_modelo():
    """
    Carga el árbol entrenado y sus características.
    """

    if not RUTA_MODELO.exists():
        raise FileNotFoundError(
            f"No se encontró el modelo: {RUTA_MODELO}"
        )

    datos = joblib.load(RUTA_MODELO)

    modelo = datos["modelo"]
    columnas = datos["columnas"]

    print("Modelo cargado correctamente.")

    return modelo, columnas


def extraer_reglas(modelo, columnas):
    """
    Extrae las reglas aprendidas por el árbol.
    """

    reglas = export_text(
        modelo,
        feature_names=list(columnas),
        decimals=3
    )

    return reglas


def guardar_reglas(reglas):
    """
    Guarda las reglas en un archivo de texto.
    """

    RUTA_REGLAS.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        RUTA_REGLAS,
        "w",
        encoding="utf-8"
    ) as archivo:
        archivo.write(reglas)

    print(f"Reglas guardadas en: {RUTA_REGLAS}")


def main():

    print("\n--- EXTRACCIÓN DE REGLAS ---")

    modelo, columnas = cargar_modelo()

    reglas = extraer_reglas(
        modelo,
        columnas
    )

    guardar_reglas(reglas)

    print("\n--- PRIMERAS REGLAS APRENDIDAS ---")

    lineas = reglas.splitlines()

    for linea in lineas[:25]:
        print(linea)

    print("\nExtracción finalizada correctamente.")


if __name__ == "__main__":
    main()
