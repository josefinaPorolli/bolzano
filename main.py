"El usuario introduce una fn genérica"
"Se emplean las restricciones para restringir puntos o rangos"
"se conforma un dominio"
"Se le solicita una intervalo de búsqueda de raíces"
"En caso de optar por no introducir uno, se realiza una búsqueda simétrica exponencial"
"Se aplica Bolzano"
"Se aplica la UI"
import	restricciones as r
import BuscadorDeIntervalos as b
def prints():
    """Imprime una tabla de funciones genéricas y sus representaciones matemáticas."""
    print("Las funciones en programación no se dictan igual que en matemáticas, por lo que se emplean representaciones a nivel código de las mismas.")
    print("Se le adjunta a usted una tabla de equivalencias entre dichas funciones y su representación:")
    dict ={
        "x**(1/n)": "ⁿ√x",
        "e**x": "eˣ",
        "log_n(x)": "logₙ(x)",
        "ln(x)": "ln(x)",
        "sin(x)": "sin(x)",
        "cos(x)": "cos(x)",
        "tan(x)": "tan(x)",
        "asin(x)": "asin(x)",
        "acos(x)": "acos(x)",
        "atan(x)": "atan(x)",
        "sec(x)": "sec(x)",
        "csc(x)": "csc(x)",
        "cot(x)": "cot(x)",
        "sinh(x)": "sinh(x)",
        "cosh(x)": "cosh(x)",
        "tanh(x)": "tanh(x)",
        "csch(x)": "csch(x)",
        "sech(x)": "sech(x)",
        "coth(x)": "coth(x)",
        "x / y": "x / y",
        "x * y": "x ⋅ y",
        "x + y": "x + y",
        "x - y": "x - y",
        "x ** n": "xⁿ"
    }
    print(f"{'Comando:':14}{'Fn:'}")
    for each in dict:
        print(f"{each:10} -> {dict[each]}")

prints()
fn="sin(x-1)/(x-1)"
# fn=input("Introduce la función: ")
dominio = r.CalcularDominio(fn)
print(f"El dominio de la función es: {dominio}")
intervalos = b.BuscarIntervalosRaiz(fn, dominio)
for r in intervalos:
    if isinstance(r, tuple):
        print(f"Intervalo: [{round(r[0],6)}, {round(r[1],6)}]")
    else:
        print(f"Raíz exacta: x = {round(r, 6)}")
