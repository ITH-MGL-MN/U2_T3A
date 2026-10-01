---
id: deflacion_leva
titulo: "Perfil de leva: deflación con una raíz exacta"
incognita: "Q"
unidad: "-"
mano: true
rangos:
  r1: [2, 4, 0]
  b: [1, 3, 0]
  c: [1, 6, 0]
---

El perfil de una **leva mecánica** se modela con el polinomio cúbico

$$P(x) = {polinomio}$$

donde $x$ es el ángulo del árbol de levas.

Al graficarlo observas que la curva cruza el eje en $x = {r1}$, o sea que
$P({r1}) = 0$: es una **raíz exacta** y la conoces de antemano. No tiene
sentido volver a resolver el problema completo desde el principio.

Aplica **una división sintética** (deflación) dividiendo $P(x)$ entre
$(x - {r1})$ y reporta los coeficientes del polinomio reducido de segundo
grado

$$Q(x) = A\,x^{2} + B\,x + C$$

**de mayor a menor grado**, es decir reporta $A$, luego $B$ y luego $C$.

La tabla de la división está en blanco abajo. Fíjate en que el último valor
que obtengas (el residuo) también es información: si $x = {r1}$ fuera raíz
solo *aproximada*, ese residuo sería el error que cometes al suponerla.
