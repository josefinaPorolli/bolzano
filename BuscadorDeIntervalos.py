import sympy as sp
from sympy import sympify, S, oo, Interval, Union, Complement, ImageSet, FiniteSet
import math

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

        # cerca de una asíntota sympy no siempre lanza excepción: puede
        # devolver zoo (ComplexInfinity) directamente, o un valor finito
        # pero enorme un paso antes/después del polo. Esto es una red de
        # seguridad extra; la protección real contra falsos "cambios de
        # signo" que en verdad son un salto de asíntota está en
        # `hay_excluido_en_rango` (ver más abajo), que sabe EXACTAMENTE
        # dónde están las asíntotas periódicas y no depende de qué tan
        # grande dio el valor muestreado.
        if not f.is_real or not f.is_finite:
            return None
        if abs(f) > UMBRAL_POLO:
            return None

        return f
    except Exception:
        return None


# ============================================================
# DETECCIÓN DE ASÍNTOTAS ENTRE DOS PUNTOS
# ============================================================
#
# Un cambio de signo f(x0)*f(x1)<0 NO implica que haya una raíz si entre
# x0 y x1 la función tiene un polo (Bolzano exige continuidad en [x0,x1]).
# Esto pasa justo con tan(x), cot(x), etc. Como el dominio ahora modela
# correctamente las exclusiones periódicas (ver restricciones.py), se
# puede chequear ARITMÉTICAMENTE si algún punto excluido cae estrictamente
# dentro de (x0,x1), sin depender de que el valor muestreado haya sido
# "suficientemente grande" (que con un grid grueso puede no serlo).

def _es_imageset_lineal_enteros(s):
    if not isinstance(s, ImageSet):
        return False
    if len(s.args) < 2 or s.args[1] != S.Integers:
        return False
    lam = s.lamda
    if len(lam.variables) != 1:
        return False
    n = lam.variables[0]
    coef = lam.expr.diff(n)
    return not coef.has(n)

def hay_excluido_en_rango(excluido, a, b):
    """¿Hay algún punto de `excluido` estrictamente entre a y b?"""
    if excluido is None or excluido == S.EmptySet:
        return False

    a = float(a)
    b = float(b)
    if a > b:
        a, b = b, a

    if isinstance(excluido, Union):
        return any(hay_excluido_en_rango(p, a, b) for p in excluido.args)

    if isinstance(excluido, FiniteSet):
        return any(a < float(p) < b for p in excluido)

    if _es_imageset_lineal_enteros(excluido):
        lam = excluido.lamda
        n = lam.variables[0]
        expr = lam.expr
        coef = float(expr.diff(n))
        offset = float(expr.subs(n, 0))

        if coef == 0:
            return a < offset < b

        n_lo = (a - offset) / coef
        n_hi = (b - offset) / coef
        if coef < 0:
            n_lo, n_hi = n_hi, n_lo

        for n_val in range(math.floor(n_lo), math.ceil(n_hi) + 1):
            punto = offset + coef * n_val
            if a < punto < b:
                return True
        return False

    # tipo de exclusión no reconocido: no se puede verificar con certeza.
    # Preferimos no bloquear la búsqueda antes que romper con una excepción.
    return False

def _excluido_de(dominio):
    """Extrae el conjunto excluido (el "- {...}") de un dominio Complement.
    Si el dominio no tiene exclusiones, devuelve None."""
    if isinstance(dominio, Complement):
        return dominio.args[1]
    return None

from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

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


# ============================================================
# EXTRACCIÓN DE INTERVALOS BASE A PARTIR DEL DOMINIO (objeto sympy)
# ============================================================
#
# Antes se armaba el dominio como STRING (via formatear_dominio) y se volvía
# a parsear acá con .split(","). Eso es frágil: cualquier cambio en cómo se
# imprime el dominio (p. ej. al agregar soporte para dominios periódicos,
# "D: ℝ - {pi*n + pi/2 : n∈ℤ}") rompe el parser. Ahora se recibe directamente
# el objeto Set de sympy que ya devuelve CalcularDominio, sin pasar por texto.
#
# Las exclusiones puntuales/periódicas (el "- {...}" de un Complement) no se
# usan para particionar el intervalo de búsqueda: son un conjunto de medida
# cero, así que un barrido numérico prácticamente nunca cae justo en uno.
# La protección real contra falsos positivos en esos puntos (asíntotas) está
# en evaluar(), que descarta valores no finitos o desmesuradamente grandes.

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