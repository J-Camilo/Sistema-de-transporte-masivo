
from pathlib import Path

import joblib
import pandas as pd


RAIZ = Path(__file__).resolve().parents[2]

RUTA_MODELO = RAIZ / "resultados" / "modelo_arbol.joblib"


def cargar_modelo():
    if not RUTA_MODELO.exists():
        raise FileNotFoundError(
            f"No se encontró el modelo: {RUTA_MODELO}"
        )

    datos = joblib.load(RUTA_MODELO)

    return datos["modelo"], datos["columnas"]


def predecir_viaje(modelo, columnas, viaje):

    # Convertir el viaje a DataFrame
    datos = pd.DataFrame([viaje])

    # Codificar las variables categóricas
    datos = pd.get_dummies(datos, dtype=int)

    # Utilizar exactamente las columnas del entrenamiento
    datos = datos.reindex(
        columns=columnas,
        fill_value=0
    )

    # Obtener la predicción
    prediccion = modelo.predict(datos)[0]

    # Obtener las probabilidades de cada clase
    probabilidades = modelo.predict_proba(datos)[0]

    return prediccion, dict(
        zip(modelo.classes_, probabilidades)
    )


def main():

    print("\n--- PRUEBA DE PREDICCIÓN ---")

    modelo, columnas = cargar_modelo()

    viaje = {
        "estacion_origen": "Cuba",
        "estacion_destino": "Centro",
        "ruta": "Ruta 1",
        "num_transbordos": 0,
        "distancia_km": 4.5,
        "hora": 7,
        "dia_semana": "lunes",
        "es_festivo": 0,
        "clima": "lluvia",
        "tiempo_base_min": 12.5
    }

    prediccion, probabilidades = predecir_viaje(
        modelo,
        columnas,
        viaje
    )

    print("\nDatos del viaje:")

    for campo, valor in viaje.items():
        print(f"{campo}: {valor}")

    print("\n--- RESULTADO ---")
    print(f"Nivel de demora estimado: {prediccion}")

    print("\nProbabilidades por clase:")

    for clase, probabilidad in probabilidades.items():
        print(f"{clase}: {probabilidad * 100:.2f}%")

    print("\nPrueba finalizada correctamente.")


if __name__ == "__main__":
    main()
