from sympy import symbols, sympify
import math
x_sym = symbols("x")

def evaluar(fn, val):
    try:
        return fn.subs(x_sym, val).evalf(64)
    except:
        return None

def set_funcion(fn_str):
    from sympy import E, pi, sin, cos, tan, asin, acos, atan, sqrt, log, exp, sinh, cosh, tanh
    namespace = {
        "x": x_sym, "e": E, "E": E, "pi": pi,
        "sin": sin, "cos": cos, "tan": tan,
        "asin": asin, "acos": acos, "atan": atan,
        "sqrt": sqrt, "log": log, "ln": log, "exp": exp,
        "sinh": sinh, "cosh": cosh, "tanh": tanh
    }
    return sympify(fn_str, locals=namespace)

def es_raiz_exacta(fn, val):
    f = evaluar(fn, val)
    return f is not None and f == 0

def buscar_en_99(fn, a, b):
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
            intervalos.append((x0, x1))
            encontrado = True
    if not encontrado:
        intervalos.append(None)
    return intervalos

def buscar_exponencial_derecha(fn, a):
    if es_raiz_exacta(fn, a): return [a]
    f_a = evaluar(fn, a)
    if f_a is None: return [None]
    for n in range(32):
        b = a + 2**n
        if es_raiz_exacta(fn, b): return [b]
        f_b = evaluar(fn, b)
        if f_b is not None and f_a * f_b < 0:
            return [(a, b)]
    return [None]

def buscar_exponencial_izquierda(fn, b):
    if es_raiz_exacta(fn, b): return [b]
    f_b = evaluar(fn, b)
    if f_b is None: return [None]
    for n in range(32):
        a = b - 2**n
        if es_raiz_exacta(fn, a): return [a]
        f_a = evaluar(fn, a)
        if f_a is not None and f_a * f_b < 0:
            return [(a, b)]
    return [None]

def buscar_simetrico(fn):
    if es_raiz_exacta(fn, 0):
        return [0]

    f_0 = evaluar(fn, 0)
    if f_0 is None:
        return [None]

    for n in range(32):
        delta = 2**n

        # derecha
        b = delta
        if es_raiz_exacta(fn, b):
            return [b]

        f_b = evaluar(fn, b)
        if f_b is not None and f_0 * f_b < 0:
            return [(0, b)]

        # izquierda
        a = -delta
        if es_raiz_exacta(fn, a):
            return [a]

        f_a = evaluar(fn, a)
        if f_a is not None and f_0 * f_a < 0:
            return [(a, 0)]

    return [None]

def BuscarIntervalosRaiz(fn_str, dominio_str):
    fn = set_funcion(fn_str)
    dominio_str = dominio_str.replace("D: ", "").strip("{} ")
    partes = dominio_str.split(", ")

    todos = []
    for parte in partes:
        parte = parte.strip()
        left_open  = parte[0] == "("
        right_open = parte[-1] == ")"
        interior = parte[1:-1]
        a_str, b_str = interior.split(",")
        a = -math.inf if "∞" in a_str.strip() else float(a_str.strip())
        b =  math.inf if "∞" in b_str.strip() else float(b_str.strip())

        INF = 1e-6

        if a == -math.inf and b == math.inf:
            intervalos = buscar_simetrico(fn)
        elif b == math.inf:
            inicio = a + INF if left_open else a
            intervalos = buscar_exponencial_derecha(fn, inicio)
        elif a == -math.inf:
            fin = b - INF if right_open else b
            intervalos = buscar_exponencial_izquierda(fn, fin)
        else:
            a_real = a + INF if left_open else a
            b_real = b - INF if right_open else b
            intervalos = buscar_en_99(fn, a_real, b_real)

        todos += intervalos

    return todos