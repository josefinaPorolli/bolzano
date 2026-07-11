import sympy as sp

def evaluar(funcion, valor):

    funcion = sp.sympify(funcion)
    return funcion.subs(next(iter(funcion.free_symbols), None), valor) if funcion.free_symbols else funcion

print(evaluar("asin(y)+10*y", 0.5))

"""
·funcion.free_symbols → obtiene el conjunto de variables presentes en la expresión.
·iter(funcion.free_symbols) → crea un iterador sobre esas variables.
·next(..., None) → obtiene la primera variable del iterador, o None si no existe.
·funcion.subs(variable, valor) → sustituye esa variable por el valor indicado.
·if funcion.free_symbols else funcion → decide si hace la sustitución o devuelve la constante directamente.
"""