"""
ml/evaluacion.py - Qué tan bueno es el árbol y si sus reglas funcionan en el motor
==================================================================================
Rol C | Base teórica: Capítulo 17

Usa el contrato del Rol B (preparacion.py y arbol.py) y mide:
    1. Accuracy, precisión, recall y F1 por clase + matriz de confusión (30 % de prueba).
    2. Validación cruzada estratificada de 5 particiones: ¿el resultado es estable?
    3. Comparación contra una línea base (DummyClassifier) y un RandomForest.
    4. Integración: las reglas de docs/reglas_aprendidas.txt corriendo en el motor de
       la Actividad 1 dan la misma respuesta que el árbol.

Ejecutar (desde la raíz):
    python src/ml/evaluacion.py
Genera docs/figuras/06_matriz_confusion.png y docs/figuras/07_comparacion_modelos.png
e imprime las tablas en Markdown para docs/pruebas_modelo.md.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, confusion_matrix,
                             precision_recall_fscore_support)
from sklearn.model_selection import StratifiedKFold, cross_val_score

from ml.arbol import PROFUNDIDAD, PROFUNDIDADES, entrenar
from ml.integracion import cargar_reglas_aprendidas, hechos_de_fila, inferir_demora
from ml.preparacion import RAIZ, SEMILLA, cargar_datos, dividir, preparar

CLASES = ["baja", "media", "alta"]
FIGURAS = RAIZ / "docs" / "figuras"
PLIEGUES = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)


def modelos():
    return {
        "Línea base (DummyClassifier)": DummyClassifier(strategy="most_frequent"),
        f"Árbol de decisión (profundidad {PROFUNDIDAD})": None,   # se entrena con arbol.entrenar
        # Por defecto cada división mira sqrt(92) ≈ 9 columnas al azar; como 74 de las 92 son
        # estaciones (casi no influyen), muchas divisiones no ven ninguna columna útil.
        "RandomForest (por defecto)": RandomForestClassifier(n_estimators=200, random_state=SEMILLA),
        "RandomForest (todas las columnas)": RandomForestClassifier(
            n_estimators=200, max_features=None, random_state=SEMILLA),
    }


def tabla(encabezados, filas):
    lineas = ["| " + " | ".join(encabezados) + " |",
              "|" + "|".join("---" for _ in encabezados) + "|"]
    lineas += ["| " + " | ".join(str(c) for c in fila) + " |" for fila in filas]
    return "\n".join(lineas)


def pct(valor):
    return f"{valor * 100:.1f} %".replace(".", ",")


# ---------------------------------------------------------------------------
# 1. Métricas por clase y matriz de confusión
# ---------------------------------------------------------------------------
def metricas(y_real, y_pred):
    precision, recall, f1, soporte = precision_recall_fscore_support(y_real, y_pred, labels=CLASES)
    filas = [(c, pct(p), pct(r), pct(f), s) for c, p, r, f, s in
             zip(CLASES, precision, recall, f1, soporte)]
    p, r, f, _ = precision_recall_fscore_support(y_real, y_pred, labels=CLASES, average="macro")
    filas.append(("**promedio macro**", pct(p), pct(r), pct(f), sum(soporte)))
    return accuracy_score(y_real, y_pred), filas


def graficar_matriz(y_real, y_pred, ruta):
    matriz = confusion_matrix(y_real, y_pred, labels=CLASES)
    ConfusionMatrixDisplay(matriz, display_labels=CLASES).plot(cmap="Blues", colorbar=False)
    plt.title(f"Matriz de confusión - árbol (profundidad {PROFUNDIDAD})")
    plt.xlabel("Predicción del árbol")
    plt.ylabel("Valor real")
    plt.tight_layout()
    plt.savefig(ruta, dpi=120)
    plt.close()
    return matriz


# ---------------------------------------------------------------------------
# 2 y 3. Validación cruzada y comparación de modelos
# ---------------------------------------------------------------------------
def comparar_modelos(X, y, X_entrena, X_prueba, y_entrena, y_prueba):
    filas = []
    for nombre, modelo in modelos().items():
        ajustado = entrenar(X_entrena, y_entrena) if modelo is None else modelo.fit(X_entrena, y_entrena)
        # cross_val_score clona el modelo: cada partición se entrena desde cero.
        cv = cross_val_score(ajustado, X, y, cv=PLIEGUES)
        filas.append({"nombre": nombre, "prueba": ajustado.score(X_prueba, y_prueba),
                      "cv": cv, "entrena": ajustado.score(X_entrena, y_entrena)})
    return filas


def graficar_comparacion(filas, ruta):
    nombres = [f["nombre"].replace(" (", "\n(") for f in filas]
    medias = [f["cv"].mean() for f in filas]
    desv = [f["cv"].std() for f in filas]
    plt.figure(figsize=(9, 4.8))
    barras = plt.bar(nombres, medias, yerr=desv, capsize=6,
                     color=["#9aa5b1", "#2f6db5", "#a9c79a", "#6b9e4f"])
    for barra, media in zip(barras, medias):
        plt.text(barra.get_x() + barra.get_width() / 2, media + 0.03, pct(media), ha="center")
    plt.ylim(0, 1)
    plt.ylabel("Acierto (validación cruzada, 5 particiones)")
    plt.title("Árbol de decisión contra las referencias")
    plt.tight_layout()
    plt.savefig(ruta, dpi=120)
    plt.close()


def profundidad_por_validacion(X, y):
    """Confirma la profundidad del Rol B sin mirar el conjunto de prueba."""
    return [(p, cross_val_score(entrenar(X, y, p), X, y, cv=PLIEGUES).mean())
            for p in PROFUNDIDADES]


# ---------------------------------------------------------------------------
# 4. Reglas aprendidas dentro del motor de la Actividad 1
# ---------------------------------------------------------------------------
def probar_integracion(df_prueba, y_arbol):
    """
    - Con TODAS las reglas: el motor debe dar exactamente la respuesta del árbol.
    - Con las 4 escogidas: cuántos viajes cubren y cuánto aciertan en esos viajes.
    """
    filas = df_prueba.to_dict("records")
    todas = cargar_reglas_aprendidas(todas=True)
    iguales = sum(inferir_demora(hechos_de_fila(f), todas)[0] == pred
                  for f, pred in zip(filas, y_arbol))

    escogidas = cargar_reglas_aprendidas()
    por_regla = []
    for regla in escogidas:
        cubiertos = [f for f in filas if inferir_demora(hechos_de_fila(f), [regla])[0]]
        aciertos = sum(f["nivel_demora"] == regla["entonces"][2] for f in cubiertos)
        por_regla.append((regla, len(cubiertos), aciertos))
    return len(todas), iguales, len(filas), por_regla


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    df = cargar_datos()
    X, y = preparar(df)
    X_entrena, X_prueba, y_entrena, y_prueba = dividir(X, y)
    arbol = entrenar(X_entrena, y_entrena)
    y_pred = arbol.predict(X_prueba)
    FIGURAS.mkdir(parents=True, exist_ok=True)

    print(f"Datos: {len(df)} viajes | entrenamiento {len(X_entrena)} | prueba {len(X_prueba)}"
          f" | {X.shape[1]} columnas después de get_dummies()\n")

    acierto, filas = metricas(y_prueba, y_pred)
    print(f"## 1. Árbol (profundidad {PROFUNDIDAD}) sobre el 30 % de prueba\n")
    print(f"Accuracy: **{pct(acierto)}**\n")
    print(tabla(["Clase", "Precisión", "Recall", "F1", "Viajes"], filas))

    matriz = graficar_matriz(y_prueba, y_pred, FIGURAS / "06_matriz_confusion.png")
    print("\nMatriz de confusión (filas = real, columnas = predicho):\n")
    print(tabla(["Real \\ Predicho"] + CLASES,
                [[f"**{c}**"] + list(fila) for c, fila in zip(CLASES, matriz)]))

    print("\n## 2 y 3. Validación cruzada (5 particiones) y comparación\n")
    comparacion = comparar_modelos(X, y, X_entrena, X_prueba, y_entrena, y_prueba)
    graficar_comparacion(comparacion, FIGURAS / "07_comparacion_modelos.png")
    print(tabla(["Modelo", "Entrenamiento", "Prueba (30 %)", "CV media", "CV desv.", "CV por partición"],
                [(f["nombre"], pct(f["entrena"]), pct(f["prueba"]), pct(f["cv"].mean()),
                  pct(f["cv"].std()), " · ".join(pct(v) for v in f["cv"])) for f in comparacion]))

    print("\nProfundidad según validación cruzada (sin tocar el conjunto de prueba):\n")
    print(tabla(["Profundidad", "CV media"],
                [(p, pct(m)) for p, m in profundidad_por_validacion(X, y)]))

    print("\n## 4. Reglas aprendidas dentro del motor de la Actividad 1\n")
    total, iguales, viajes, por_regla = probar_integracion(df.loc[X_prueba.index], y_pred)
    print(f"Con las {total} reglas del árbol cargadas, el motor coincide con el árbol en "
          f"**{iguales} de {viajes}** viajes de prueba ({pct(iguales / viajes)}).\n")
    print(tabla(["Regla", "Condiciones", "Viajes de prueba que cubre", "Acierto en esos viajes"],
                [(r["id"], r["descripcion"].removeprefix("Aprendida del árbol: "), n,
                  pct(a / n) if n else "-") for r, n, a in por_regla]))


if __name__ == "__main__":
    main()
