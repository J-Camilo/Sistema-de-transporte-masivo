
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd

from sklearn.model_selection import (
    train_test_split,
    cross_val_score
)
from sklearn.tree import (
    DecisionTreeClassifier,
    plot_tree
)

from preparacion import preparar_datos


# Carpeta principal del proyecto
RAIZ = Path(__file__).resolve().parents[2]

# Carpeta donde se guardarán los resultados
CARPETA_RESULTADOS = RAIZ / "resultados"


def comparar_profundidades(X_entrenamiento, y_entrenamiento):
    """
    Entrena árboles con profundidades de 3 a 12
    y selecciona la mejor mediante validación cruzada.
    """

    profundidades = []
    precisiones_entrenamiento = []
    precisiones_validacion = []

    print("\n--- COMPARACIÓN DE PROFUNDIDADES ---")

    for profundidad in range(3, 13):

        modelo = DecisionTreeClassifier(
            criterion="entropy",
            max_depth=profundidad,
            random_state=42
        )

        modelo.fit(X_entrenamiento, y_entrenamiento)

        precision_entrenamiento = modelo.score(
            X_entrenamiento,
            y_entrenamiento
        )

        resultados_cv = cross_val_score(
            modelo,
            X_entrenamiento,
            y_entrenamiento,
            cv=5,
            scoring="accuracy"
        )

        precision_validacion = resultados_cv.mean()

        profundidades.append(profundidad)
        precisiones_entrenamiento.append(
            precision_entrenamiento
        )
        precisiones_validacion.append(
            precision_validacion
        )

        print(
            f"Profundidad {profundidad}: "
            f"Entrenamiento = {precision_entrenamiento:.4f} | "
            f"Validación = {precision_validacion:.4f}"
        )

    resultados = pd.DataFrame({
        "profundidad": profundidades,
        "precision_entrenamiento": precisiones_entrenamiento,
        "precision_validacion": precisiones_validacion
    })

    resultados.to_csv(
        CARPETA_RESULTADOS / "comparacion_profundidades.csv",
        index=False
    )

    plt.figure(figsize=(10, 6))

    plt.plot(
        profundidades,
        precisiones_entrenamiento,
        marker="o",
        label="Entrenamiento"
    )

    plt.plot(
        profundidades,
        precisiones_validacion,
        marker="s",
        label="Validación cruzada"
    )

    plt.xlabel("Profundidad del árbol")
    plt.ylabel("Exactitud (accuracy)")
    plt.title("Comparación de profundidades")
    plt.xticks(profundidades)
    plt.legend()
    plt.grid(True)

    plt.savefig(
        CARPETA_RESULTADOS / "comparacion_profundidades.png",
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    mejor_indice = resultados[
        "precision_validacion"
    ].idxmax()

    mejor_profundidad = int(
        resultados.loc[mejor_indice, "profundidad"]
    )

    print(
        f"\nMejor profundidad: {mejor_profundidad}"
    )

    return mejor_profundidad


def entrenar_arbol(
    X_entrenamiento,
    y_entrenamiento,
    profundidad
):
    """
    Entrena el modelo definitivo.
    """

    modelo = DecisionTreeClassifier(
        criterion="entropy",
        max_depth=profundidad,
        random_state=42
    )

    modelo.fit(X_entrenamiento, y_entrenamiento)

    return modelo


def guardar_modelo(modelo, columnas):
    """
    Guarda el modelo y las columnas utilizadas.
    """

    ruta_modelo = CARPETA_RESULTADOS / "modelo_arbol.joblib"

    joblib.dump(
        {
            "modelo": modelo,
            "columnas": list(columnas)
        },
        ruta_modelo
    )

    print(f"Modelo guardado en: {ruta_modelo}")


def generar_imagen_arbol(modelo, columnas):
    """
    Genera una imagen del árbol entrenado.
    """

    plt.figure(figsize=(24, 12))

    plot_tree(
        modelo,
        feature_names=list(columnas),
        class_names=list(modelo.classes_),
        filled=True,
        rounded=True,
        fontsize=8,
        max_depth=3
    )

    ruta_imagen = CARPETA_RESULTADOS / "arbol_decision.png"

    plt.savefig(
        ruta_imagen,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Imagen guardada en: {ruta_imagen}")


def main():

    CARPETA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True
    )

    (
        X_entrenamiento,
        X_prueba,
        y_entrenamiento,
        y_prueba
    ) = preparar_datos()

    mejor_profundidad = comparar_profundidades(
        X_entrenamiento,
        y_entrenamiento
    )

    modelo = entrenar_arbol(
        X_entrenamiento,
        y_entrenamiento,
        mejor_profundidad
    )

    precision_entrenamiento = modelo.score(
        X_entrenamiento,
        y_entrenamiento
    )

    precision_prueba = modelo.score(
        X_prueba,
        y_prueba
    )

    print("\n--- RESULTADOS DEL MODELO ---")
    print(f"Profundidad seleccionada: {mejor_profundidad}")
    print(f"Exactitud entrenamiento: {precision_entrenamiento:.4f}")
    print(f"Exactitud prueba: {precision_prueba:.4f}")

    guardar_modelo(
        modelo,
        X_entrenamiento.columns
    )

    generar_imagen_arbol(
        modelo,
        X_entrenamiento.columns
    )

    print("\nEntrenamiento finalizado correctamente.")


if __name__ == "__main__":
    main()
