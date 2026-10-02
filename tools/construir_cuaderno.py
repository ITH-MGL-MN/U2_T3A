# -*- coding: utf-8 -*-
"""
tools/construir_cuaderno.py — Genera U2_T3A.ipynb.

El cuaderno se escribe aquí como texto (Markdown y Python) y se serializa a
JSON. Así se revisa y se corrige en un archivo legible en lugar de pelear con
el formato .ipynb, y el cuaderno se puede regenerar entero con:

    python tools/construir_cuaderno.py
"""
import io
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, 'U2_T3A.ipynb')

CELDAS = []
MD = 'markdown'
PY = 'python'


def md(texto):
    CELDAS.append((MD, texto))


def py(texto):
    CELDAS.append((PY, texto))


# =====================================================================
#  PORTADA
# =====================================================================
md(r"""
# U2_T3A · Forma anidada de Horner, derivadas y deflación

### Evaluación eficiente de polinomios

## ¿Qué vas a aprender?

Evaluar un polinomio «como está escrito» es un desperdicio: calcular
$x^{4}$, $x^{3}$, $x^{2}$ por separado repite trabajo y **amplifica el error de
redondeo**. La **regla de Horner** reescribe el polinomio de forma anidada y
consigue el mismo resultado con $n$ multiplicaciones en lugar de $O(n^2)$.

De paso, esa misma pasada te regala **tres cosas más**: la derivada $P\,'(x_0)$
(con una segunda corrida) y el **polinomio deflactado** $Q(x)$ de dividir entre
$(x-x_0)$.

| # | Pregunta | Tipo | Puntos |
|---|---|---|---|
| 1 | Cuánto ahorra la forma anidada | opción múltiple | 10 |
| 2 | Programar `horner(a, x0)` | código (casos ocultos) | 25 |
| 3 | Valor $P(x_0)$ de tu ejercicio | numérica | 15 |
| 4 | Derivada $P\,'(x_0)$ de tu ejercicio | numérica | 15 |
| 5 | Deflación: coeficientes de $Q(x)$ | 3 casillas | 25 |
| 6 | Decisión de ingeniería | opción múltiple | 10 |

$$\text{Calificación} = 0.70\,(\text{automático}) + 0.30\,(\text{2 actividades a mano})$$

Se requiere **$\ge 90\%$** de los 100 puntos automáticos para poder enviar.

> **Importante:** la tarea está **sembrada con tu número de control**. Cada
> compañero tiene polinomios, puntos de evaluación y raíces distintos. Copiar
> no sirve: la función se califica con **casos ocultos** que nunca ves.

---

## Cómo usar este cuaderno

1. Escribe tu correo institucional en la celda de identificación.
2. Lee la teoría de las secciones 1 y 2 (son cortas y traen un laboratorio).
3. Haz la **actividad a mano** de la sección 3 **con calculadora** y reporta
   tus valores.
4. Programa `horner` y compruébala con **tu** ejercicio.
5. Repite con la **deflación** en la sección 4.
6. Al final, imprime la **hoja de trabajo manual** y envíala junto con tu
   cuaderno.
""")

# =====================================================================
#  1. CONFIGURACIÓN
# =====================================================================
py(r"""
#@title ⚙️ Configuración general — ejecuta esta celda **PRIMERO** (no modificar)
# ============================================================
# CELDA 1 — CONFIGURACIÓN GENERAL
# Detecta si corre en Google Colab o en tu computadora, monta Drive y
# carga el motor de la tarea:
#     Colab    -> grader_ofuscado.txt  (lo que ve el alumno)
#     PC local -> grader_local.py      (el MISMO motor, legible, para depurar)
# Los dos archivos los genera  python tools/build.py  a partir de las
# mismas fuentes: el código es idéntico, solo cambia la presentación.
# ============================================================
import base64
import importlib
import os
import subprocess
import sys
import zlib

import matplotlib.pyplot as plt
import numpy as np
from IPython.display import Markdown, display

%matplotlib inline
plt.rcParams["figure.figsize"] = (9, 4.5)

# ¿Estamos en Google Colab?
try:
    import google.colab
    ES_COLAB = True
except ImportError:
    ES_COLAB = False

# --- Repositorio de la tarea  <-- EDITAR SOLO SI CAMBIA EL REPO ------
REPO_URL = "https://github.com/ITH-MGL-MN/U2_T3A.git"
REPO_NOMBRE = "U2_T3A"

# --- Solo en tu computadora: qué versión del motor quieres probar ---
#   True  -> grader_local.py     (bundle legible, se puede leer y depurar)
#   False -> grader_ofuscado.txt (exactamente lo que recibe el alumno)
DEBUG_SIN_OFUSCAR = True

if ES_COLAB:
    BASE = "/content/drive/MyDrive/CursoMN"
    REPO = os.path.join(BASE, REPO_NOMBRE)
else:
    # En local: buscar la carpeta de la tarea (la que tiene grader_local.py)
    # subiendo de carpeta en carpeta desde la carpeta actual.
    REPO = os.getcwd()
    for _ in range(4):
        if os.path.exists(os.path.join(REPO, "grader_local.py")):
            break
        _padre = os.path.dirname(REPO)
        if _padre == REPO:
            break
        REPO = _padre
    # Respaldo: ruta local de la tarea en tu Drive (ajústala si la moviste)
    if not os.path.exists(os.path.join(REPO, "grader_local.py")):
        REPO = r"o:\Mi unidad\CursoMN\U2_T3A"

print("Modo          :", "Google Colab" if ES_COLAB else "PC local")
print("Carpeta tarea :", REPO)

# ============================================================
# Montar Drive y traer el repositorio  (solo en Colab)
# En tu computadora no hace nada.
# ============================================================
if ES_COLAB:
    from google.colab import drive

    drive.mount("/content/drive")
    os.makedirs(BASE, exist_ok=True)
    try:
        if not os.path.exists(REPO):
            subprocess.run(["git", "clone", REPO_URL, REPO], check=True)
        else:
            subprocess.run(["git", "-C", REPO, "pull"], check=True)
        print("✅ Repositorio listo en Drive.")
    except Exception as _exc:
        print("⚠️ No se pudo clonar/actualizar el repositorio:", _exc)
        print("   Si la carpeta ya existe en tu Drive puedes continuar.")
else:
    print("Modo local: no se monta Drive, uso la carpeta de arriba.")

# ============================================================
# Librerías necesarias
# ============================================================
for _pkg in ("sympy", "numpy", "scipy", "matplotlib", "requests", "ipywidgets"):
    try:
        importlib.import_module(_pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", _pkg])

# ============================================================
# Motor de la tarea
# ============================================================
USAR_OFUSCADO = ES_COLAB or (not DEBUG_SIN_OFUSCAR)

if USAR_OFUSCADO:
    _ruta = os.path.join(REPO, "grader_ofuscado.txt")
    with open(_ruta, encoding="utf-8") as f:
        _blob = f.read().strip()
    codigo = zlib.decompress(base64.b64decode(_blob)).decode("utf-8")
else:
    _ruta = os.path.join(REPO, "grader_local.py")
    with open(_ruta, encoding="utf-8") as f:
        codigo = f.read()
    print("🔧 Modo debug local: cargando el bundle legible (sin ofuscar)")

try:
    exec(codigo, globals())
except Exception as _exc:
    raise RuntimeError(
        "No pude cargar el motor desde %s.\n"
        "En Colab: revisa que el repositorio se haya clonado.\n"
        "En local: ejecuta  python tools/build.py  para generarlo.\n"
        "Detalle: %r" % (_ruta, _exc)
    )

print("Motor cargado :", "OFUSCADO (grader_ofuscado.txt)" if USAR_OFUSCADO
      else "BUNDLE local (grader_local.py)")
print("\nListo. Ahora ejecuta la celda de identificación.")
""")

md(r"""
---
## Identifícate

Al ejecutar la celda de configuración, Google te pidió permiso para acceder a
tu Drive. Con esa **misma cuenta** te identifico automáticamente: no tienes que
escribir nada.

> # ⚠️ INICIA SESIÓN CON TU CORREO INSTITUCIONAL
> - Debe ser un correo que termine en **@….tecnm.mx** (por ejemplo `@hermosillo.tecnm.mx`).
> - Si inicias con una cuenta personal, verás una alerta y **no podrás continuar**.
> - Es importante para identificarte y validar tu tarea.

Si ya ejecutaste esta celda varias veces, puede seguirte preguntando por otros
permisos: puedes continuar sin seleccionarlos. Solo se necesita el permiso de
**leer tu correo**.
""")

py(r"""
#@title 👤 Identificación automática
# ============================================================
# IDENTIFICACIÓN AUTOMÁTICA
# Usa el correo institucional (…@….tecnm.mx) con el que montaste Drive.
# ============================================================
if ES_COLAB:
    import requests
    from google.colab import auth
    import google.auth
    import google.auth.transport.requests

    # Autenticación explícita para asegurar el acceso a la identidad
    try:
        auth.authenticate_user()
        creds, _ = google.auth.default()
        auth_request = google.auth.transport.requests.Request()
        creds.refresh(auth_request)
        info = requests.get(
            "https://www.googleapis.com/drive/v3/about?fields=user",
            headers={"Authorization": "Bearer " + creds.token},
            timeout=20,
        ).json()
        email = info.get("user", {}).get("emailAddress", "")
    except Exception as e:
        print("⚠️ No se pudo obtener tu correo automáticamente.")
        print("Asegúrate de permitir el acceso en la ventana emergente.")
        print("Detalle:", e)
        email = ""
else:
    # Modo local (pruebas): escribe un correo manualmente
    email = "m16330887@hermosillo.tecnm.mx"
    # email = input("Correo institucional (pruebas): ").strip()

# --- Validación del dominio institucional ----------------------------
if email and ("@" in email) and email.lower().endswith(".tecnm.mx"):
    alumno_id = email
    print("✅ Identificado:", email)
    print("   Número de control:", extraer_nc(email))
elif not email:
    alumno_id = None
    print("⛔ No pude identificar tu correo.")
    print("   Vuelve a ejecutar la celda de configuración y acepta el permiso")
    print("   en la ventana de Google.")
else:
    from IPython.display import HTML

    display(HTML(
        '<p style="color:#b00020;background:#ffe0e0;padding:12px;border-radius:8px;'
        'font-weight:bold">⛔ Este correo no es institucional.<br>'
        'Usa tu cuenta @….tecnm.mx. Si iniciaste con otra cuenta, '
        'cierra sesión o usa una ventana de incógnito.</p>'
    ))
    print("Correo detectado:", email)
    alumno_id = None

if alumno_id is None:
    raise RuntimeError(
        "Detente aquí: necesito tu correo institucional para generar tu tarea.\n"
        "Corrige la identificación y vuelve a ejecutar esta celda."
    )

print("\nListo. Continúa con la sección 1.")
""")

# =====================================================================
#  2. POR QUÉ HORNER
# =====================================================================
md(r"""
---
# 1 · El costo de evaluar un polinomio

Un polinomio de grado $n$ se escribe

$$P(x) = a_n x^n + a_{n-1} x^{n-1} + \dots + a_1 x + a_0$$

y lo natural es evaluarlo **tal como está escrito**: calcular cada potencia
$x^2, x^3, \dots, x^n$ y multiplicarla por su coeficiente. Si se hace así, contar
las multiplicaciones da

$$n + (n-1) + (n-2) + \dots + 1 = \frac{n(n+1)}{2} = O(n^2)$$

Para un polinomio de grado 4 son **10** multiplicaciones; para grado 8, **36**.
En un microcontrolador de 8 bits cada multiplicación es una operación costosa
(decenas de ciclos), así que esto se nota.

## La forma anidada

Sacando factor común $x$ una y otra vez, el mismo polinomio se reescribe

$$P(x) = \bigl(\dots\bigl((a_n x + a_{n-1})x + a_{n-2}\bigr)x + \dots\bigr)x + a_0$$

y ahora **cada paso reutiliza el resultado del anterior**. Eso baja el costo a
exactamente $n$ multiplicaciones y $n$ sumas: $O(n)$.

---

> **Además hay una ganancia numérica.** Al calcular $x^{20}$ y multiplicarlo por
> un coeficiente, el error de redondeo de las potencias intermedias se arrastra
> y se amplifica. En la forma anidada solo se hace una multiplicación y una suma
> por coeficiente, así que el error crece mucho menos. **En el segundo
> laboratorio lo vas a ver con números, no con palabras.**

---

### 🧪 Laboratorio A · ¿Cuántas multiplicaciones ahorra Horner?

El laboratorio de abajo **cuenta las multiplicaciones reales** y compara el tiempo de ejecución entre la implementación directa y la anidada.

**Las dos se miden en igualdad de condiciones:** Python puro, escalar, el mismo
número de repeticiones y sin bibliotecas compiladas. Comparar contra `numpy`
(que está escrita en C y procesa vectores completos) mediría la diferencia de
lenguajes, no la del algoritmo.

#### Glosario

> **Algoritmo «ingenuo» (*Naive algorithm*):** En computación y ciencias de la computación, el término *ingenuo* o del francés *naïve* se refiere al enfoque directo o literal de resolver un problema matemático tal como está definido en papel, sin aplicar optimizaciones algorítmicas ni considerar el consumo de recursos computacionales.

> **Regla de Horner:** Llamado así en honor al matemático británico William George Horner (aunque conocido siglos antes por matemáticos en China e India), es el algoritmo estándar para reducir la evaluación de un polinomio a una secuencia anidada de $n$ multiplicaciones y $n$ sumas.
""")

py(r"""
# @title 🧪 Laboratorio A · Ahorro de operaciones y tiempo (mismas condiciones)
#
# Los dos métodos se comparan EN IGUALDAD DE CONDICIONES:
#   * Python puro y escalar, los dos igual. Comparar contra numpy (C +
#     vectorizado) mediría la diferencia de lenguajes, no la del algoritmo.
#   * `horner_referencia` es la MISMA función del motor que califica la
#     pregunta 2, no una copia escrita aquí.
#   * la evaluación término a término sale del motor (`evaluar_ingenuo`),
#     que además CUENTA las multiplicaciones de verdad, una por una.
import time
from IPython.display import Markdown, display

encabezados = ("| Grado ($n$) | Mult. término a término | Mult. Horner | Ahorro | "
               "Tiempo ingenuo (µs) | Tiempo Horner (µs) | ¿Mismo valor? |\n")
separador = "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n"
filas = ""

for n in (2, 4, 6, 8, 10, 12, 20, 50, 100, 200):
    a = [1.0] * (n + 1)
    x = 1.5

    v_ing, mult_ing = evaluar_ingenuo(a, x)
    v_hor = horner_referencia(a, x)[0]      # forma anidada del motor
    mult_hor = n                            # una multiplicación por coeficiente

    # Las mismas repeticiones para los dos, y suficientes para que el
    # cronómetro mida algo (se divide entre ellas para dar μs por evaluación).
    reps = max(5, 200000 // max(1, mult_ing))
    t0 = time.perf_counter()
    for _ in range(reps):
        evaluar_ingenuo(a, x)
    t1 = time.perf_counter()
    t2 = time.perf_counter()
    for _ in range(reps):
        horner_referencia(a, x)
    t3 = time.perf_counter()

    us_ing = (t1 - t0) / reps * 1e6
    us_hor = (t3 - t2) / reps * 1e6
    iguales = "sí" if abs(v_ing - v_hor) <= 1e-12 * max(1.0, abs(v_ing)) else "⚠️ no"

    filas += ("| $%d$ | $%d$ | $%d$ | **$%d$** | %.1f | %.1f | %s |\n"
              % (n, mult_ing, mult_hor, mult_ing - mult_hor, us_ing, us_hor, iguales))

display(Markdown(
    "### 📊 Costo y tiempo (mismo lenguaje, misma máquina, mismas repeticiones)\n\n"
    + encabezados + separador + filas
    + "\n> **Multiplicaciones:** término a término $\\frac{n(n+1)}{2}$, Horner $n$.\n"
      "> El ahorro es $\\frac{n(n+1)}{2}-n=\\frac{n(n-1)}{2}$, que sigue siendo\n"
      "> $O(n^2)$ **de operaciones que te ahorras**; el costo de Horner es $O(n)$.\n"
      "> Con $n=200$: 20 100 operaciones contra 200.\n"
      "> Si en vez de calcular cada potencia desde cero las guardaras en un\n"
      "> arreglo ($x^2=x\\cdot x$, $x^3=x^2\\cdot x$, ...), el ingenuo bajaría a\n"
      "> $2n$ multiplicaciones, pero necesitaría guardar $n$ valores y seguiría\n"
      "> costando el doble que Horner.\n"
      ">\n"
      "> **Tiempo:** las dos columnas son del MISMO número de repeticiones en\n"
      "> Python puro. El conteo le añade unas sumas al método ingenuo, así que si\n"
      "> acaso lo perjudica: la diferencia real es igual o mayor.\n"
      ">\n"
      "> **¿Y numpy?** Aquí no se compara contra `numpy.polyval` a propósito: esa\n"
      "> función está escrita en C y procesa vectores completos, así que ganaría\n"
      "> por lenguaje, no por algoritmo. Dos implementaciones se comparan\n"
      "> cambiando una sola cosa: la forma de recorrer los coeficientes.\n"
      ">\n"
      "> **¿Mismo valor?** Con coeficientes positivos los dos aciertan. La\n"
      "> diferencia numérica aparece cuando hay **cancelación**, y eso lo mide el\n"
      "> laboratorio B."))
""")

md(r"""
### 🧪 Laboratorio B · Error de redondeo: los dígitos que no se ven

Todos los valores de abajo salen con **17 cifras** (todas las que guarda un
`float` de doble precisión) y el valor «verdadero» se calcula con **aritmética
racional exacta** (`Fraction`). Así el error que se mide es *solo* el del redondeo
del método: no hay una tercera fuente de error.

Se hace en tres pasos:

1. **Los últimos dígitos a la vista.** El mismo polinomio evaluado de las dos
   formas, con todas sus cifras, contra el valor exacto.
2. **Una evaluación mal condicionada.** Con $(x-1)^n$ desarrollado, en $x=1.0001$,
   los términos valen hasta $10^{17}$ y el resultado es $10^{-4n}$: al restar se
   cancelan y se llevan los dígitos. Se mide $\kappa$, el **número de condición**,
   que *predice* cuántos dígitos se pierden, y se comprueba que la predicción
   acierta. Ahí toca preguntarse de quién es la culpa.
3. **Un polinomio grande «normal»** (coeficientes positivos, sin cancelación):
   los dos aciertan y la única diferencia real vuelve a ser el costo.
""")

py(r"""
# @title 🧪 Laboratorio B · Error de redondeo: los dígitos que no se ven
#
# El valor "verdadero" es EXACTO (aritmética racional), y se evalúa en el MISMO
# float `x` para los dos métodos, así que la diferencia que se ve es
# exclusivamente la del redondeo de cada uno.

x = 1 + 1e-4
print("Polinomio: P(x) = (x - 1)^n  desarrollado (coeficientes que alternan de signo)")
print("Punto:     x = %.20g   <-- el MISMO para los dos métodos\n" % x)
print("%-5s %-25s %-11s %-25s %-11s"
      % ("n", "término a término", "error rel.", "Horner", "error rel."))
print("-" * 84)
for n in (2, 4, 6, 8, 12, 20, 40, 60):
    a = coeficientes_binomio(n)          # (x - 1)^n, de mayor a menor grado
    exacto = evaluar_exacto(a, x)
    v_ing, _ = evaluar_ingenuo(a, x)
    v_hor = horner_referencia(a, x)[0]
    print("%-5d %-25.17g %-11.2e %-25.17g %-11.2e"
          % (n, v_ing, error_relativo(v_ing, exacto),
             v_hor, error_relativo(v_hor, exacto)))
print("-" * 84)

print("\nEl valor exacto vale 1e-4 elevado a n, o sea:")
for n in (2, 6, 12, 20):
    print("   (x - 1)^%-3d = %s" % (n, evaluar_exacto(coeficientes_binomio(n), x)))

print("\nLee las columnas: con n = 8 el resultado verdadero ya es del orden de")
print("1e-32, pero los términos que suma el método ingenuo son del orden de 1e2.")
print("Restar números así de parecidos se come TODOS los dígitos disponibles:")
print("lo que queda es ruido. La forma anidada nunca construye esos términos")
print("grandes: calcula (x - 1) una vez y lo multiplica; por eso conserva los")
print("dígitos incluso cuando el resultado es diminuto.")

# --- ¿Y con un polinomio grande "normal"? -----------------------------
print("\n" + "=" * 84)
print("Polinomio grande con coeficientes POSITIVOS (sin cancelación):")
print("=" * 84)
print("%-6s %-25s %-11s %-25s %-11s"
      % ("grado", "término a término", "error rel.", "Horner", "error rel."))
print("-" * 84)
for n in (50, 100, 200, 400):
    a = [1.0] * (n + 1)
    xg = 1.5
    exacto = evaluar_exacto(a, xg)
    v_ing, mult = evaluar_ingenuo(a, xg)
    v_hor = horner_referencia(a, xg)[0]
    print("%-6d %-25.17g %-11.2e %-25.17g %-11.2e"
          % (n, v_ing, error_relativo(v_ing, exacto), v_hor,
             error_relativo(v_hor, exacto)))
print("-" * 84)
print("Aquí los dos métodos aciertan (el error es del orden del épsilon de la")
print("máquina, ~1e-16) porque todos los términos tienen el MISMO signo y se")
print("suman sin cancelarse. La ventaja de Horner en este caso es solo de costo:")
print("el ingenuo hizo %d multiplicaciones (y el mismo número de sumas) donde"
      % evaluar_ingenuo([1.0] * 201, 1.5)[1])
print("Horner habría hecho 200.")
""")

# =====================================================================
#  3. EL ALGORITMO
# =====================================================================
md(r"""
---
# 2 · El algoritmo anidado y lo que te regala

## La recurrencia

Con los coeficientes $a=[a_n, a_{n-1}, \dots, a_0]$ y el punto $x_0$, la
primera corrida es

$$b_n = a_n, \qquad b_k = a_k + b_{k+1}\,x_0 \quad (k = n-1, n-2, \dots, 0)$$

y al terminar:

* **el valor**: $P(x_0) = b_0$;
* **los demás $b$**: los coeficientes del cociente $Q(x)$ de dividir $P(x)$
  entre $(x - x_0)$, es decir

$$P(x) = (x - x_0)\,Q(x) + b_0$$

Ojo con el orden: si tus coeficientes van de mayor a menor grado, al recorrerlos
en ese mismo orden vas obteniendo $b_n, b_{n-1}, \dots, b_0$. El **último** es el
valor del polinomio y **los anteriores** forman $Q$ (sin ese último).

## La derivada, con una segunda corrida

Para la derivada no hace falta derivar el polinomio a mano: se **repite la misma
división sintética**, ahora sobre los $b_k$:

$$c_n = b_n, \qquad c_k = b_k + c_{k+1}\,x_0 \quad (k = n-1, \dots, 1)$$

y el resultado es

$$\boxed{\ P\,'(x_0) = c_1\ }$$

es decir el **penúltimo** valor de esa segunda fila.

## La deflación

Si además $x_0$ resulta ser una **raíz exacta** ($P(x_0)=0$), entonces
$b_0 = 0$ y el cociente cumple

$$P(x) = (x - r)\,Q(x)$$

Eso es **deflactar**: bajar el grado en 1 sin volver a resolver el problema
completo. Es la forma estándar de encontrar *todas* las raíces de un polinomio
(paso a paso, quitando la que ya conoces).

> **Cuidado con dos detalles:** el cociente **conserva el coeficiente líder**
> (si $P$ empieza con $4x^3$, $Q$ empieza con $4x^2$), y si el residuo $b_0$
> **no** es cero, es que $r$ no era raíz exacta: ese residuo vale $P(r)$.

### Las dos filas de la tabla, de un vistazo

El laboratorio de abajo imprime la tabla completa de una división sintética
(la misma que vas a llenar a mano) para que veas de dónde sale cada número.
""")

py(r"""
#@title 🔬 Laboratorio · la división sintética paso a paso
# Un polinomio de ejemplo cualquiera (NO es el tuyo).
a_demo = [2, -6, 2, -1]
x_demo = 3.0


def division_sintetica_detallada(a, x0):
    '''Imprime cada paso de la primera corrida.'''
    print("Coeficientes a = %s   y   x0 = %g\n" % (a, x0))
    print("Primera corrida (b):")
    b = [float(a[0])]
    print("   b_%d = a_%d = %g" % (len(a) - 1, len(a) - 1, b[0]))
    for k in range(1, len(a)):
        b.append(a[k] + b[k - 1] * x0)
        print("   b_%d = a_%d + b_%d*x0 = %g + %g*%g = %g"
              % (len(a) - 1 - k, len(a) - 1 - k, len(a) - k, a[k], b[k - 1], x0, b[k]))
    print("\n   P(x0) = b_0 = %g" % b[-1])
    print("   Q(x)  = %s" % b[:-1])

    print("\nSegunda corrida (c), sobre los b:")
    c = [b[0]]
    for k in range(1, len(b) - 1):
        c.append(b[k] + c[k - 1] * x0)
        print("   c_%d = b_%d + c_%d*x0 = %g + %g*%g = %g"
              % (len(b) - 1 - k, len(b) - 1 - k, len(b) - k, b[k], c[k - 1], x0, c[k]))
    print("\n   P'(x0) = c_1 = %g" % c[-1])

    # Comprobación: P(x) = (x - x0) Q(x) + P(x0)
    def evaluar(coefs, x):
        n = len(coefs) - 1
        return sum(c * x ** (n - i) for i, c in enumerate(coefs))

    xt = x0 + 1.0
    izq = evaluar(a, xt)
    der = (xt - x0) * evaluar(b[:-1], xt) + b[-1]
    print("\nComprobación en x = %g:  P(x) = %.6f   (x-x0)*Q(x)+b_0 = %.6f"
          % (xt, izq, der))
    return b, c


division_sintetica_detallada(a_demo, x_demo)
print("\nFíjate en que NO aparece ninguna potencia de x elevada: la gracia es")
print("que cada b se calcula con el b anterior.")
""")

md(r"""
---

### ✏️ Pregunta 1
""")

py(r"""
#@title 🧪 Pregunta 1 · cuánto ahorra la forma anidada
MI_TAREA = generar_tarea(alumno_id)   # tu tarea queda guardada en MI_TAREA
pregunta(1)
""")

# =====================================================================
#  4. ACTIVIDAD A MANO · HORNER
# =====================================================================
md(r"""
---
# 3 · Actividad a mano · Horner: $P(x_0)$ y $P\,'(x_0)$

Aquí abajo está **tu** polinomio (el tuyo, no el de tu compañero) y el punto de
evaluación. Vas a llenar la tabla **a mano, con calculadora**, en este orden:

1. **Fila $b_k$** (primera corrida): empieza con $b = a_n$ y aplica
   $b \leftarrow b \cdot x_0 + a_k$ recorriendo los coeficientes de mayor a menor
   grado. El **último** valor que obtengas es $P(x_0)$.
2. **Fila $c_k$** (segunda corrida): repite lo mismo **pero sobre los $b$** (no
   sobre los $a$). El **penúltimo** valor de esta fila es $P\,'(x_0)$.

Después reporta tus dos resultados en la celda que sigue. **No redondees los
pasos intermedios**: el error se acumula y la comprobación te lo va a decir.
""")

py(r"""
#@title ✏️✅ Horner · actividad a mano, práctica y preguntas
EJ_HR = mano_enunciado('HORNER')
""")

py(r"""
# ---------------------------------------------------------------------
#  TU ECUACION, escrita por ti como funciones lambda.
#  P  -> el polinomio del enunciado
#  dP -> su derivada analitica (la que obtendrias derivando a mano)
#
#  Por ejemplo:  P  = lambda x: x**3 - 4*x**2 + 7*x + 1
#                dP = lambda x: 3*x**2 - 8*x + 7
# ---------------------------------------------------------------------
P = None          # <-- escribe TU polinomio   (P = lambda x: ...)
dP = None         # <-- escribe TU derivada    (dP = lambda x: ...)

mano_ecuacion('HORNER', f=P, df=dP)
""")

py(r"""
# ---------------------------------------------------------------------
#  Escribe aqui tus DOS valores calculados a mano y vuelve a ejecutar
#  esta celda para recibir la realimentacion.
# ---------------------------------------------------------------------
MIS_HR = [0.0, 0.0]          # <-- [P(x_0), P'(x_0)]

mano_comprueba('HORNER', MIS_HR)
""")

md(r"""
---
### 💻 Pregunta 2 · programa el algoritmo

Ahora vas a programar exactamente lo que acabas de hacer a mano, pero para
cualquier polinomio. La pregunta pide una función con esta firma:

```python
horner(a, x0)  ->  (p_val, dp_val, Q)
```

* `a` es la lista de coeficientes **de mayor a menor grado**;
* devuelve el valor, la derivada y la **lista** del cociente.

Se califica con **casos ocultos** (polinomios que nunca ves), así que no sirve
devolver un número fijo ni llamar a `numpy.polyval`: hay que recorrer los
coeficientes con la recurrencia.
""")

py(r"""
#@title Pregunta 2 · programar horner con casos ocultos
pregunta(2)
""")

py(r"""
# --- Práctica: programa el método ------------------------------------
def horner(a, x0):
    '''
    Forma anidada de Horner.

    Parametros
    ----------
    a  : lista de coeficientes de MAYOR a menor grado, [a_n, ..., a_0]
    x0 : punto de evaluacion

    Devuelve
    --------
    (p_val, dp_val, Q)
        p_val  : P(x0)
        dp_val : P'(x0)
        Q      : lista de los coeficientes del cociente P(x)/(x - x0),
                 tambien de mayor a menor grado
    '''
    # =================================================================
    #  ESCRIBE TU CODIGO AQUI
    #  Primera corrida:  b = a[0]; para cada coeficiente siguiente
    #      b = b*x0 + a_k        (ve guardando cada b)
    #  Segunda corrida:  igual, pero sobre los b_k ya guardados
    #      (el resultado P'(x0) es el PENULTIMO de esa fila)
    #  Y ojo: Q son los b SIN el ultimo.
    # =================================================================
    # return (p_val, dp_val, Q)
    raise NotImplementedError("Completa la funcion horner") # Borra esta línea


# --- Prueba con TU ejercicio -----------------------------------------
try:
    _p, _d, _q = horner(EJ_HR['a'], EJ_HR['x0'])
    comparar_practica('HORNER', EJ_HR, (_p, _d, _q))
except NotImplementedError as exc:
    print("Todavia no terminas la funcion:", exc)
except TypeError as exc:
    print("Tu funcion devolvio algo que no se puede leer:", exc)

# --- Solución de referencia (revisa DESPUES de intentarlo) -----------
tabla('HORNER', EJ_HR)
""")

md(r"""
---
### ✏️ Preguntas 3 y 4 · los dos valores de tu ejercicio

Ya tienes la tabla llena a mano y la función programada. Contesta con los
números de **tu** ejercicio (los mismos que reportaste en `MIS_HR`). Si quieres
comprobar antes, ejecuta `mano_solucion('HORNER')`.
""")

py(r"""
pregunta(3)      # el valor P(x_0)
""")

py(r"""
pregunta(4)      # la derivada P'(x_0)
""")

# =====================================================================
#  5. DEFLACIÓN
# =====================================================================
md(r"""
---
# 4 · Deflación: quitar una raíz que ya conoces

Cuando ya sabes que $r$ es raíz de $P$, dividir entre $(x-r)$ te deja un
polinomio de un grado menos **con las mismas raíces restantes**:

$$P(x) = (x - r)\,Q(x) + \underbrace{P(r)}_{b_0}$$

Esa división es **exactamente la primera corrida de Horner evaluada en $r$**, así
que no hay que programar nada nuevo: los coeficientes de $Q$ son los $b_k$ que
obtuviste, sin el último.

## ¿Para qué sirve?

Encontrar todas las raíces de un polinomio de grado alto es un problema difícil.
La estrategia estándar es:

1. encuentra **una** raíz (con Newton, Bairstow, Müller… o «por inspección»);
2. **deflacta** para bajar el grado;
3. repite con el polinomio reducido.

Y si el residuo no sale cero, es que la raíz era solo **aproximada**: ese residuo
es $P(r)$, el error que cometerías al dar por buena esa raíz.

> ⚠️ **El error clásico al deflactar a mano:** dividir como si el polinomio fuera
> mónico. Si $P$ empieza con $4x^3$, entonces $Q$ empieza con $4x^2$: el
> coeficiente líder **se conserva**.
""")

py(r"""
#@title ✏️✅ Deflación · actividad a mano y pregunta
EJ_DF = mano_enunciado('DEFLACION')
""")

py(r"""
# ---------------------------------------------------------------------
#  TU ECUACION, escrita por ti como funcion lambda.
#  Es el MISMO polinomio del enunciado (el de arriba).
#
#  Por ejemplo:  P = lambda x: x**3 - 6*x**2 + 7*x + 6
# ---------------------------------------------------------------------
P = None          # <-- escribe TU polinomio   (P = lambda x: ...)

mano_ecuacion('DEFLACION', f=P)
""")

py(r"""
# ---------------------------------------------------------------------
#  Escribe aqui los TRES coeficientes del polinomio reducido Q(x),
#  de MAYOR a menor grado, y vuelve a ejecutar esta celda.
# ---------------------------------------------------------------------
MIS_DF = [0.0, 0.0, 0.0]          # <-- [A, B, C]

mano_comprueba('DEFLACION', MIS_DF)
""")

py(r"""
pregunta(5)      # los coeficientes de Q(x)
""")

md(r"""
---
### 🧪 Laboratorio · deflación progresiva hasta agotar las raíces

Tu ejercicio tiene una raíz exacta conocida, así que se puede deflactar **en
serie**: encuentra las raíces del polinomio reducido y ya tienes todas.

Aquí se comparan dos caminos y se comprueba el residuo. Fíjate en la última
parte: cuando la raíz **no** es exacta, el residuo es justo el error.
""")

py(r"""
#@title 🧪 Laboratorio · deflación progresiva y comparación con numpy.roots
a = [float(c) for c in EJ_DF['a']]
r = float(EJ_DF['x0'])

print("Polinomio a = %s   con la raíz conocida r = %g\n" % (a, r))

# --- 1) Deflactar con la raíz conocida -------------------------------
Q, residuo = deflactar(a, r)
print("Deflación entre (x - %g):" % r)
print("   Q(x)    = %s" % Q)
print("   residuo = %g   %s" % (residuo, "(exacta ✅)" if abs(residuo) < 1e-12
                                 else "(NO era raíz exacta ❌)"))

# --- 2) Todas las raíces, por los dos caminos ------------------------
print("\nRaíces del polinomio reducido Q (con numpy.roots):")
raices_q = raices_de(Q)
for z in sorted(raices_q, key=lambda z: (round(z.real, 6), round(z.imag, 6))):
    print("   %s" % ("%.8f" % z.real if abs(z.imag) < 1e-12 else "%.8f %+.8fj"
                     % (z.real, z.imag)))

print("\nTodas las raíces del polinomio original (numpy.roots directo):")
for z in sorted(raices_de(a), key=lambda z: (round(z.real, 6), round(z.imag, 6))):
    print("   %s" % ("%.8f" % z.real if abs(z.imag) < 1e-12 else "%.8f %+.8fj"
                     % (z.real, z.imag)))
print("\n   (deben coincidir: r más las de Q)")

# --- 3) Comprobacion: P(x) == (x - r)*Q(x) ---------------------------
def evaluar(coefs, x):
    n = len(coefs) - 1
    return sum(c * x ** (n - i) for i, c in enumerate(coefs))

peor = 0.0
for xt in (-2.0, -0.5, 0.0, 1.7, 4.3):
    izq = evaluar(a, xt)
    der = (xt - r) * evaluar(Q, xt) + residuo
    peor = max(peor, abs(izq - der) / max(1.0, abs(izq)))
print("\nComprobación P(x) = (x-r)Q(x) + residuo en 5 puntos: peor diferencia %.2e" % peor)

# --- 4) ¿Y si la raíz NO fuera exacta? -------------------------------
r_mal = r + 0.05
Q_mal, res_mal = deflactar(a, r_mal)
print("\nSi en lugar de r = %g usas r = %g (0.05 de error):" % (r, r_mal))
print("   residuo = %+.6f   <- esto vale P(%.2f), el error de suponerla raíz"
      % (res_mal, r_mal))
print("   P(%.2f) = %+.6f   (comprueba que coincide)" % (r_mal, evaluar(a, r_mal)))
""")

# =====================================================================
#  6. CIERRE
# =====================================================================
md(r"""
---
# 5 · Conclusiones

## Lo que hay que llevarse

1. **La forma anidada baja el costo de $O(n^2)$ a $O(n)$** porque cada paso
   reutiliza el resultado del anterior.
2. **Una sola corrida da tres cosas**: el valor, el polinomio deflactado y —con
   una segunda corrida— la derivada. Es el «dos por uno» que hace que Newton y
   Bairstow evalúen derivadas gratis.
3. **Deflactar es dividir entre $(x-r)$**: baja el grado y conserva las raíces
   que faltan. Si el residuo no es cero, $r$ no era raíz exacta y ese residuo
   mide el error.
4. **El coeficiente líder se conserva** al deflactar. Es el error más común a
   mano.
5. **Todo esto se paga con menos operaciones y menos error de redondeo**, que es
   exactamente lo que necesita un microcontrolador evaluando una calibración.

## Autoevaluación rápida

* ¿Por qué $n$ multiplicaciones y no $\frac{n(n+1)}{2}$?
* ¿De dónde sale el $Q(x)$ de la primera corrida, si nunca dividiste nada?
* ¿Por qué $P\,'(x_0)$ es el **penúltimo** valor de la segunda corrida y no el
  último?
* Si al deflactar el residuo te da $-0.37$, ¿qué significa ese número?
* ¿Por qué no basta con evaluar el polinomio término a término si el resultado
  «sale bien»?

---

### ✏️ Pregunta 6
""")

py(r"""
#@title 🧪 Pregunta 6 · decisión de ingeniería
pregunta(6)
""")

md(r"""
---
# 6 · Entrega

## Antes de enviar

1. **Revisa tus 6 preguntas.** Si alguna está en blanco el sistema la cuenta
   como error.
2. **Completa la función `horner`.** Se prueba con polinomios que nunca ves.
3. **Imprime la hoja de trabajo manual** (celda de abajo). Va junto con tu
   cuaderno: ahí aparecen tus dos tablas a mano con los valores que reportaste y
   los de referencia, para que tu profesor califique rápido las 2 rúbricas (30 %
   de la calificación).
4. Necesitas **$\ge 90\%$** de los 100 puntos automáticos para poder enviar. Si
   no llegas, corrige y vuelve a ejecutar.

| Sección | Actividad a mano | ¿La reportaste? |
|---|---|---|
| 3 | Horner: $P(x_0)$ y $P\,'(x_0)$ | `MIS_HR` |
| 4 | Deflación: coeficientes de $Q(x)$ | `MIS_DF` |

> Si te quedó alguna pregunta mal, **no** borres tu trabajo: primero entiende
> **por qué** falló. Los errores de esta tarea son exactamente los que aparecen
> en el examen final (y en la siguiente entrega, donde Müller y Bairstow usan
> estas mismas divisiones sintéticas).
""")

py(r"""
#@title 📋 Hoja de trabajo manual (entrégala con tu cuaderno)
hoja_manual()
""")

py(r"""
#@title 📤 Calificar y enviar
enviar(alumno_id)
""")


# =====================================================================
#  Serialización
# =====================================================================
def lineas(texto):
    """El formato .ipynb guarda la fuente como lista de líneas CON \\n."""
    lineas = texto.strip('\n').split('\n')
    return [l + '\n' for l in lineas[:-1]] + [lineas[-1]]


def construir():
    celdas = []
    for tipo, texto in CELDAS:
        if tipo == MD:
            celdas.append({'cell_type': 'markdown', 'metadata': {},
                           'source': lineas(texto)})
        else:
            celdas.append({'cell_type': 'code', 'metadata': {},
                           'execution_count': None, 'outputs': [],
                           'source': lineas(texto)})
    nb = {
        'cells': celdas,
        'metadata': {
            'colab': {'provenance': []},
            'kernelspec': {'display_name': 'Python 3', 'name': 'python3'},
            'language_info': {'name': 'python'},
        },
        'nbformat': 4,
        'nbformat_minor': 5,
    }
    with io.open(DESTINO, 'w', encoding='utf-8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
        f.write('\n')
    n_md = sum(1 for t, _ in CELDAS if t == MD)
    print('Cuaderno : %s' % DESTINO)
    print('Celdas   : %d  (%d markdown, %d de código)'
          % (len(CELDAS), n_md, len(CELDAS) - n_md))
    print('Preguntas: %d' % sum(1 for _t, x in CELDAS if 'pregunta(' in x))


if __name__ == '__main__':
    construir()
