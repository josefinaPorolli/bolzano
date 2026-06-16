from sympy import *

x = symbols("x")

FUNCIONES_PERMITIDAS = {
    "sqrt",
    "log",
    "ln",
    "exp",

    "sin",
    "cos",
    "tan",

    "asin",
    "acos",
    "atan",

    "sinh",
    "cosh",
    "tanh",

    "sec",
    "csc",
    "cot",

    "csch",
    "sech",
    "coth"
}

RESTRICCIONES = [
    ("sqrt", lambda a: sympify(a) >= 0),
    ("log",  lambda a: sympify(a) > 0),
    ("asin", lambda a: And(sympify(a) >= -1, sympify(a) <= 1)),
    ("acos", lambda a: And(sympify(a) >= -1, sympify(a) <= 1)),
]

def quitar_parentesis(expr):
    expr = expr.strip()
    while expr.startswith("(") and expr.endswith(")"):
        nivel = 0
        es_exterior = True
        for i, c in enumerate(expr):
            if c == "(": nivel += 1
            if c == ")": nivel -= 1
            if nivel == 0 and i < len(expr) - 1:
                es_exterior = False
                break
        if es_exterior:
            expr = expr[1:-1]
        else:
            break
    return expr

def separar(expr, ops):
    partes, ops_lista, actual, nivel, i = [], [], "", 0, 0
    while i < len(expr):
        c = expr[i]
        if c == "(": nivel += 1
        if c == ")": nivel -= 1
        if c in ops and nivel == 0 and actual:
            if c == "*" and i+1 < len(expr) and expr[i+1] == "*": actual += c
            elif c == "*" and i > 0 and expr[i-1] == "*": actual += c
            else:
                partes.append(actual)
                ops_lista.append(c)
                actual = "" if c in "+*/" else c
        else:
            actual += c
        i += 1
    partes.append(actual)
    return partes, ops_lista

def argumento(factor):
    if "(" in factor:
        return factor[factor.index("(")+1 : factor.rindex(")")]
    return None

def es_atomico(expr):
    expr_limpia = expr.replace("**", "")
    if not any(c in expr_limpia for c in "+-*/"):
        return True
    return False

def obtener_condiciones(expr):
    expr = quitar_parentesis(expr)
    if es_atomico(expr):
        return []
    condiciones = []
    terminos, _ = separar(expr, "+-")
    for t in terminos:
        partes, ops_lista = separar(t, "*/")
        for idx, f in enumerate(partes):
            f_limpio = quitar_parentesis(f)
            if idx > 0 and ops_lista[idx-1] == "/":
                condiciones.append(Ne(sympify(f_limpio), 0))
                condiciones += obtener_condiciones(f_limpio)
            for nombre, regla in RESTRICCIONES:
                if f_limpio.startswith(nombre):
                    arg = argumento(f_limpio)
                    if arg:
                        condiciones.append(regla(arg))
                        condiciones += obtener_condiciones(arg)
            if f_limpio.startswith("("):
                condiciones += obtener_condiciones(f_limpio)
    return condiciones

def formatear_dominio(dominio):
    def formatear_intervalo(iv):
        if isinstance(iv, Interval):
            izq = "-∞" if iv.start == -oo else str(iv.start)
            der = "∞" if iv.end == oo else str(iv.end)
            a = "(" if iv.left_open else "["
            b = ")" if iv.right_open else "]"
            return f"{a}{izq},{der}{b}"
        return str(iv)
    if isinstance(dominio, Union):
        partes = [formatear_intervalo(i) for i in dominio.args]
    else:
        partes = [formatear_intervalo(dominio)]
    return "D: {" + ", ".join(partes) + "}"

# def CalcularDominio(fn):
#     condiciones = obtener_condiciones(fn)
#     dominio = S.Reals
#     for c in condiciones:
#         dominio = Intersection(dominio, solve_univariate_inequality(c, x, relational=False))
#     return formatear_dominio(dominio)

def CalcularDominio(fn):
    condiciones = obtener_condiciones(fn)
    dominio = S.Reals

    for c in condiciones:
        valor = simplify(c)

        if valor == True:
            continue

        dominio = Intersection(
            dominio,
            solve_univariate_inequality(c, x, relational=False)
        )

    return dominio

def intervalo_en_dominio(dominio, a, b):
    intervalo = Interval(a, b)
    return intervalo.is_subset(dominio)

def validar_funciones(expr):
    try:
        expresion = sympify(expr)

        for funcion in expresion.atoms(Function):
            if funcion.func.__name__ not in FUNCIONES_PERMITIDAS:
                return False

        return True

    except:
        return False