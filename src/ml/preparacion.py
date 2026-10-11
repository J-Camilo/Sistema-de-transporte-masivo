
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


# Ruta del archivo CSV, tomando como referencia
# la carpeta principal del proyecto.
RUTA_CSV = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "viajes_megabus.csv"
)


def cargar_datos(ruta_archivo=RUTA_CSV):
    """
    Lee el archivo CSV que contiene los viajes del Megabús.
    """

    datos = pd.read_csv(ruta_archivo)

    if datos.empty:
        raise ValueError("El archivo CSV no contiene registros.")

    if datos.isnull().any().any():
        raise ValueError("El dataset contiene valores nulos.")

    print("Dataset cargado correctamente.")
    print(f"Total de registros: {len(datos)}")
    print(f"Total de columnas: {len(datos.columns)}")

    return datos


def preparar_datos(ruta_archivo=RUTA_CSV):
    """
    Prepara las características y divide los datos
    en entrenamiento (70 %) y prueba (30 %).
    """

    datos = cargar_datos(ruta_archivo)

    y = datos["nivel_demora"]

    X = datos.drop(
        columns=[
            "id_viaje",
            "tiempo_real_min",
            "nivel_demora"
        ]
    )

    X = pd.get_dummies(X, dtype=int)

    X_entrenamiento, X_prueba, y_entrenamiento, y_prueba = (
        train_test_split(
            X,
            y,
            test_size=0.30,
            random_state=42,
            stratify=y
        )
    )

    return (
        X_entrenamiento,
        X_prueba,
        y_entrenamiento,
        y_prueba
    )


def main():
    """
    Ejecuta la preparación y muestra sus resultados.
    """

    (
        X_entrenamiento,
        X_prueba,
        y_entrenamiento,
        y_prueba
    ) = preparar_datos()

    print("\n--- RESULTADOS DE LA PREPARACIÓN ---")

    print(f"Registros de entrenamiento: {len(X_entrenamiento)}")
    print(f"Registros de prueba: {len(X_prueba)}")

    print(f"Características utilizadas: {X_entrenamiento.shape[1]}")

    print("\nDistribución de clases en entrenamiento:")
    print(y_entrenamiento.value_counts())

    print("\nDistribución de clases en prueba:")
    print(y_prueba.value_counts())

    print("\nPrimeras características:")
    print(X_entrenamiento.head())


if __name__ == "__main__":
    main()
