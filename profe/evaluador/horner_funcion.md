---
funcion: horner
firma: "horner(a, x0)"
salida: tupla
ejemplo: "horner([1, -4, 5, -3, 2], 3.0)"
---

Programa el **algoritmo anidado de Horner** para evaluar un polinomio y su
primera derivada en un punto, usando **una sola pasada** por los coeficientes
para el valor y una **segunda pasada** (sobre los resultados de la primera)
para la derivada.

Tu función recibe:

* `a` — la lista de coeficientes del polinomio, **de mayor a menor grado**:
  $a=[a_n, a_{n-1}, \dots, a_0]$ (el polinomio tiene grado $n$)
* `x0` — el punto donde se evalúa

y devuelve **una tupla con tres elementos**, en este orden:

1. `p_val` — el valor $P(x_0)$
2. `dp_val` — la primera derivada $P\,'(x_0)$
3. `Q` — la **lista** de coeficientes del cociente de dividir $P(x)$ entre
   $(x-x_0)$, también de mayor a menor grado (son los $b$ de la primera
   pasada, sin el último)

Con el ejemplo `horner([1, -4, 5, -3, 2], 3.0)` debe devolver
`(11.0, 27.0, [1.0, -1.0, 2.0, 3.0])`: el polinomio evaluado en 3, su
derivada en 3 y el cúbico que resulta de dividirlo entre $(x-3)$.

**No uses `numpy.polyval` ni símilares**: se califica que tu código haga el
recorrido anidado. Fíjate en la diferencia con evaluar término a término: en
la forma anidada **cada resultado se reutiliza** como el factor de la
siguiente multiplicación.
