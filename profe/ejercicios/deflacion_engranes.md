---
id: deflacion_engranes
titulo: "Tren de engranes: deflación con coeficiente líder"
incognita: "Q"
unidad: "-"
mano: true
rangos:
  r: [2, 4, 0]
  p: [-3, 2, 0]
  q: [1, 8, 0]
  A: [1, 3, 0]
---

La función de transferencia de un **tren de engranes** de un reductor tiene
como denominador el polinomio cúbico

$$P(x) = {polinomio}$$

Se sabe que $x = {r}$ es una de sus raíces exactas (un polo del sistema).

Divide $P(x)$ entre $(x - {r})$ por **división sintética** y reporta el
polinomio reducido de segundo grado $Q(x) = A\,x^{2} + B\,x + C$, de mayor a
menor grado ($A$, luego $B$, luego $C$).

> **Cuidado:** este polinomio **no** es mónico. Al deflactar a mano el error
> más común es dividir como si el coeficiente líder fuera 1; el cociente
> conserva el coeficiente líder del polinomio original.
