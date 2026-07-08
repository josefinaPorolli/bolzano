def cantidad_iteraciones(a, b, tolerancia):
    # Se termina el proceso cuando (b-a)/2^n < tolrancia
    n = 0
    while (b - a) / (2 ** n) >= tolerancia:
        n += 1
    return n

def iterar(funcion, a, b, n):
    historial = [] # lista de tuplas (a, b, x) para cada iteración
    for i in range(n):
        x = (a + b) / 2
        historial.append((a, b, x))
        if evaluar(funcion, x) == 0:
            return x, historial
        a, b = nuevo_intervalo(funcion, a, b, x)
    return (a + b) / 2, historial

def nuevo_intervalo(funcion, a, b, x): # a es el primer extremo del intervalo, b el segundo extremo y x el punto medio
    """Define el nuevo intervalo [a, b] para la siguiente iteración"""
    if evaluar(funcion, a) * evaluar(funcion, x) < 0:
        return a, x
    else:
        return x, b    

def evaluar(funcion: str, x: float) -> float:
    """Evalúa la función en el punto x."""
    return eval(funcion)