import sympy as sp

def cantidad_iteraciones(a: sp.Float, b: sp.Float, tolerancia: sp.Float) -> int:
    # Se termina el proceso cuando (b-a)/2^n < tolrancia
    n = 0
    while (b - a) / (2 ** n) >= tolerancia:
        n += 1
    return n

def iterar(funcion: sp.Expr, a: sp.Float, b: sp.Float, n: int) -> tuple:

    a = sp.Float(a,64)
    b = sp.Float(b,64)

    historial = [] # lista de tuplas (a, b, x) para cada iteración
    for i in range(n):
        x = sp.Float((a + b) / 2,64)
        historial.append((a, b, x))
        if evaluar(funcion, x) == 0:
            return x, historial
        a, b = nuevo_intervalo(funcion, a, b, x)

    return sp.Float((a+b)/2,64), historial

def nuevo_intervalo(funcion: sp.Expr, a: sp.Float, b: sp.Float, x: sp.Float) -> tuple: # a es el primer extremo del intervalo, b el segundo extremo y x el punto medio
    """Define el nuevo intervalo [a, b] para la siguiente iteración"""    
    if evaluar(funcion, a) * evaluar(funcion, x) < 0:
        return sp.Float(a,64), sp.Float(x,64)
    else:
        return sp.Float(x,64), sp.Float(b,64)

def evaluar(funcion: sp.Expr, valor: sp.Float) -> sp.Float:
    return sp.N(
        funcion.subs(next(iter(funcion.free_symbols), None), valor)
        if funcion.free_symbols
        else funcion,
        64
    )

"""
·funcion.free_symbols → obtiene el conjunto de variables presentes en la expresión.
·iter(funcion.free_symbols) → crea un iterador sobre esas variables.
·next(..., None) → obtiene la primera variable del iterador, o None si no existe.
·funcion.subs(variable, valor) → sustituye esa variable por el valor indicado.
·if funcion.free_symbols else funcion → decide si hace la sustitución o devuelve la constante directamente.
"""