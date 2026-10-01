---
etiqueta: "P'(x_0)"
respuesta: "dp_val"
unidad: "mV/bar"
---

Con el **mismo polinomio de tu ejercicio**, reporta ahora **solo el valor de
la primera derivada** $P\,'(x_0)$ en ese punto.

Para obtenerla necesitas la **segunda corrida** de la división sintética:
vuelve a aplicar el mismo algoritmo, pero ahora sobre los coeficientes $b_k$
que obtuviste en la primera pasada. El resultado es $P\,'(x_0)=c_1$, es decir
el **penúltimo** valor de esa segunda fila.

Reporta un **número**, con al menos 4 decimales y **sin unidades**. Es el
segundo valor que devuelve tu función `horner(a, x0)`, así que puedes
comprobarlo con ella.
