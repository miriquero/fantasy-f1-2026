# -*- coding: utf-8 -*-
"""
fantasy_f1.py
-------------
Punto de entrada del pipeline. Es solo un wrapper: toda la logica vive en el
paquete f1/. Se mantiene este archivo en la raiz para que el workflow de
GitHub Actions siga llamando a `python fantasy_f1.py` sin cambios.
"""

from f1.consola import configurar_salida_utf8
from f1.main import main

if __name__ == "__main__":
    configurar_salida_utf8()
    main()
