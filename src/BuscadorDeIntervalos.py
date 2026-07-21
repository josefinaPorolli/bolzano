import sympy as sp
from sympy import S, oo, Interval, Union, Complement
from restricciones import hay_excluido_en_rango

UMBRAL_POLO = sp.Float(1e6, 64)  # |f(x)| por encima de esto se trata como "probable asíntota", no dato confiable
INF = sp.Float(1e-6, 64)         # infinitésimo para correrse de un borde/punto excluido antes de evaluar

def evaluar(fn: sp.Expr, val: sp.Float):
    try:
        variable = next(iter(fn.free_symbols), None)
        f = sp.N(
            fn.subs(variable, val)
            if variable
            else fn,
            64
        )

        if not f.is_real or not f.is_finite:
            return None
        if abs(f) > UMBRAL_POLO:
            return None

        return f
    except Exception:
        return None

def _excluido_de(dominio):
    """Extrae el conjunto excluido (el "- {...}") de un dominio Complement.
    Si el dominio no tiene exclusiones, devuelve None."""
    if isinstance(dominio, Complement):
        return dominio.args[1]
    return None

def es_raiz_exacta(fn, val):
    f = evaluar(fn, val)
    return f is not None and f == 0

def buscar_en_99(fn, a, b, excluido=None):
    paso = (b - a) / 99
    intervalos = []
    encontrado = False

    for i in range(99):
        x0 = a + i * paso
        x1 = x0 + paso

        if es_raiz_exacta(fn, x0): return [x0]
        if es_raiz_exacta(fn, x1): return [x1]

        f0 = evaluar(fn, x0)
        f1 = evaluar(fn, x1)

        if f0 is not None and f1 is not None and f0 * f1 < 0:
            if hay_excluido_en_rango(excluido, x0, x1):
                continue  # es un salto de asíntota, no una raíz
            intervalos.append((x0, x1))
            encontrado = True

    if not encontrado:
        intervalos.append(None)

    return intervalos

def buscar_exponencial_derecha(fn, a, excluido=None):
    if es_raiz_exacta(fn, a): return [a]

    f_a = evaluar(fn, a)
    if f_a is None: return [None]

    for n in range(32):
        b = a + 2**n

        if es_raiz_exacta(fn, b): return [b]

        f_b = evaluar(fn, b)

        if f_b is not None and f_a * f_b < 0 and not hay_excluido_en_rango(excluido, a, b):
            return [(a, b)]

    return [None]

def buscar_exponencial_izquierda(fn, b, excluido=None):
    if es_raiz_exacta(fn, b): return [b]

    f_b = evaluar(fn, b)
    if f_b is None: return [None]

    for n in range(32):
        a = b - 2**n

        if es_raiz_exacta(fn, a): return [a]

        f_a = evaluar(fn, a)

        if f_a is not None and f_a * f_b < 0 and not hay_excluido_en_rango(excluido, a, b):
            return [(a, b)]

    return [None]

def buscar_simetrico(fn, excluido=None):
    inicio = sp.Float(0, 64)

    if evaluar(fn, inicio) is None:
        # 0 cae justo en un excluido (p. ej. una asíntota periódica que
        # pasa por el origen): lo corremos un infinitésimo hacia el lado
        # donde la función sí esté definida, mismo criterio que ya se usa
        # para los bordes abiertos de un intervalo (INF).
        if evaluar(fn, INF) is not None:
            inicio = INF
        elif evaluar(fn, -INF) is not None:
            inicio = -INF
        else:
            return [None]

    if es_raiz_exacta(fn, inicio):
        return [inicio]

    f_0 = evaluar(fn, inicio)

    if f_0 is None:
        return [None]

    for n in range(32):
        delta = sp.Float(2**n, 64)

        b = inicio + delta

        if es_raiz_exacta(fn, b):
            return [b]

        f_b = evaluar(fn, b)

        if f_b is not None and f_0 * f_b < 0 and not hay_excluido_en_rango(excluido, inicio, b):
            return [(inicio, b)]

        a = inicio - delta

        if es_raiz_exacta(fn, a):
            return [a]

        f_a = evaluar(fn, a)

        if f_a is not None and f_0 * f_a < 0 and not hay_excluido_en_rango(excluido, a, inicio):
            return [(a, inicio)]

    return [None]

def _intervalos_base(dominio):
    if isinstance(dominio, Complement):
        base, _ = dominio.args
        return _intervalos_base(base)

    if dominio == S.Reals:
        return [(-oo, oo, True, True)]

    if isinstance(dominio, Interval):
        return [(dominio.start, dominio.end, dominio.left_open, dominio.right_open)]

    if isinstance(dominio, Union):
        out = []
        for parte in dominio.args:
            out += _intervalos_base(parte)
        return out

    # tipo no reconocido (dominio vacío, condición rara, etc.): buscar en
    # toda la recta como último recurso en vez de romper
    return [(-oo, oo, True, True)]


def BuscarIntervalosRaiz(fn, dominio):

    intervalos_base = _intervalos_base(dominio)
    excluido = _excluido_de(dominio)

    todos = []

    for a, b, left_open, right_open in intervalos_base:

        a_es_inf = (a == -oo)
        b_es_inf = (b == oo)

        a_f = None if a_es_inf else sp.Float(a, 64)
        b_f = None if b_es_inf else sp.Float(b, 64)

        if a_es_inf and b_es_inf:
            intervalos = buscar_simetrico(fn, excluido)

        elif b_es_inf:
            inicio = a_f + INF if left_open else a_f
            intervalos = buscar_exponencial_derecha(fn, inicio, excluido)

        elif a_es_inf:
            fin = b_f - INF if right_open else b_f
            intervalos = buscar_exponencial_izquierda(fn, fin, excluido)

        else:
            a_real = a_f + INF if left_open else a_f
            b_real = b_f - INF if right_open else b_f
            intervalos = buscar_en_99(fn, a_real, b_real, excluido)

        todos += intervalos

    return todos


def intervalo_en_dominio(dominio, a, b):
    return Interval(a, b).is_subset(dominio)