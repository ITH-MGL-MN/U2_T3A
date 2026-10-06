"""Comprueba el CONTENIDO (no el formato) de la celda del laboratorio de deflación.

Sustituye IPython.display por un impostor que escribe en consola, para poder leer
lo que vería el alumno. Es de un solo uso: borrar después.
"""
import json
import sys
import types

fake = types.ModuleType("IPython.display")


class _Bloc:
    def __init__(self, s):
        self.s = s

    @property
    def data(self):
        return self.s


def _show(obj):
    sys.stdout.write("%s\n\n" % getattr(obj, "data", obj))


fake.display = _show
fake.Markdown = _Bloc
fake.Math = _Bloc
fake.HTML = _Bloc
sys.modules["IPython.display"] = fake

sys.path.insert(0, ".")
sys.path.insert(0, "tools")
import numpy as np  # noqa: E402

from profe.ui import cuaderno as _c  # noqa: E402
from profe.ui.cuaderno import *  # noqa: E402,F401,F403
from visualizar import latex_cientifico, tabla_experimento  # noqa: E402

_c._EXAMEN = None
EJ_DF = _c.mano_enunciado("DEFLACION", nc="16330887")

nb = json.load(open("U2_T3A.ipynb", encoding="utf-8"))
for celda in nb["cells"]:
    fuente = "".join(celda["source"])
    if fuente.startswith("#@title") and "numpy.roots" in fuente:
        exec(compile(fuente, "<lab>", "exec"), globals())
        break
else:
    raise SystemExit("no encontré la celda")
