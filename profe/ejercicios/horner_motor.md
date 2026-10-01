---
id: horner_motor
titulo: "Curva de un motor de CD (grado 3)"
incognita: "P"
unidad: "N·m"
mano: true
rangos:
  x_eval: [1.5, 3.0, 1]
  a3: [1, 2, 0]
  a2: [-7, -3, 0]
  a1: [3, 9, 0]
  a0: [1, 6, 0]
---

El **par de un motor de CD** controlado por un variador sigue una curva de
tercer grado respecto a la corriente de armadura:

$$P(x) = {polinomio}$$

con $x$ en **amperes** y $P(x)$ en **N·m**.

El fabricante te pide el par y la pendiente de la curva (su derivada, que es
la constante de torque local) en $x_0 = {x_eval}$ A. Evalúa las dos con la
**forma anidada de Horner** y anota los pasos en la tabla: primero todos los
$b_k$, después todos los $c_k$.
