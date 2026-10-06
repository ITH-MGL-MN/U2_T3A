---
id: horner_calibracion
titulo: "Calibración de un sensor piezoeléctrico (grado 4)"
incognita: "P"
unidad: "mV"
mano: true
rangos:
  x_eval: [1.5, 3.0, 1]
  a4: [1, 3, 0]
  a3: [-5, -2, 0]
  a2: [4, 9, 0]
  a1: [-4, -1, 0]
  a0: [2, 9, 0]
---

El voltaje de salida de un **sensor piezoeléctrico** montado en un banco de
pruebas se modela con el polinomio de calibración de **cuarto grado**

$$P(x) = {polinomio}$$

donde $x$ es la presión aplicada, en **bar**, y $P(x)$ el voltaje que entrega
el acondicionador, en **mV**.

En el punto de operación $x_0 = {x_eval}$ necesitas dos cosas: el voltaje
$P(x_0)$ y la **sensibilidad** del sensor, que es su primera derivada
$P'(x_0)$.

Ya tienes la tabla de la división sintética en blanco. Llénala **en el orden
del algoritmo**: primero toda la fila $b_k$ (la división), y solo después la
fila $c_k$ (la segunda ejecución, que va sobre los $b_k$ que acabas de obtener).
No redondees los pasos intermedios.
