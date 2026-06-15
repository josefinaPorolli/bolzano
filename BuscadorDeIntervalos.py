from sympy import symbols, sympify
import math

x_sym = symbols("x")

def evaluar(fn, val):
    try:
        return float(fn.subs(x_sym, val))
    except:
        return None

def set_funcion(fn_str):
    return sympify(fn_str)

def es_raiz_exacta(fn, val):
    f = evaluar(fn, val)
    return f is not None and f == 0

def buscar_en_9(fn, a, b):
    paso = (b - a) / 9
    intervalos = []
    for i in range(9):
        x0 = a + i * paso
        x1 = x0 + paso
        if es_raiz_exacta(fn, x0): return [x0]
        if es_raiz_exacta(fn, x1): return [x1]
        f0 = evaluar(fn, x0)
        f1 = evaluar(fn, x1)
        if f0 is not None and f1 is not None and f0 * f1 < 0:
            intervalos.append((x0, x1))
    return intervalos

def buscar_exponencial_derecha(fn, a):
    if es_raiz_exacta(fn, a): return [a]
    f_a = evaluar(fn, a)
    if f_a is None: return []
    for n in range(12):
        b = a + 2**n
        if es_raiz_exacta(fn, b): return [b]
        f_b = evaluar(fn, b)
        if f_b is not None and f_a * f_b < 0:
            return [(a, b)]
    return []

def buscar_exponencial_izquierda(fn, b):
    if es_raiz_exacta(fn, b): return [b]
    f_b = evaluar(fn, b)
    if f_b is None: return []
    for n in range(12):
        a = b - 2**n
        if es_raiz_exacta(fn, a): return [a]
        f_a = evaluar(fn, a)
        if f_a is not None and f_a * f_b < 0:
            return [(a, b)]
    return []

def buscar_simetrico(fn):
    if es_raiz_exacta(fn, 0): return [0]
    f_0 = evaluar(fn, 0)
    if f_0 is None: return []
    intervalos = []
    found_right = False
    found_left = False
    for n in range(12):
        delta = 2**n
        if not found_right:
            b = delta
            if es_raiz_exacta(fn, b):
                intervalos.append(b)
                found_right = True
            else:
                f_b = evaluar(fn, b)
                if f_b is not None and f_0 * f_b < 0:
                    intervalos.append((0, b))
                    found_right = True
        if not found_left:
            a = -delta
            if es_raiz_exacta(fn, a):
                intervalos.append(a)
                found_left = True
            else:
                f_a = evaluar(fn, a)
                if f_a is not None and f_0 * f_a < 0:
                    intervalos.append((a, 0))
                    found_left = True
        if found_right and found_left:
            break
    return intervalos

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

        INF = 0.001

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
            intervalos = buscar_en_9(fn, a_real, b_real)

        todos += intervalos

    return todos