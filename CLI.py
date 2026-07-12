"El usuario introduce una fn genérica"
"Se emplean las restricciones para restringir puntos o rangos"
"se conforma un dominio"
"Se le solicita una intervalo de búsqueda de raíces"
"En caso de optar por no introducir uno, se realiza una búsqueda simétrica exponencial"
"Se aplica Bolzano"
"Se aplica la UI"
import restricciones as r
import BuscadorDeIntervalos as bu
import funciones_bolzano as f
import interfaz 
import sympy as sp

a:sp.Float = 0
b:sp.Float = 0

def prints():
    """Imprime una tabla de funciones genéricas y sus representaciones matemáticas."""
    print("Las funciones en programación no se escriben igual que en matemáticas.")
    print("A continuación se muestra una tabla de equivalencias:\n")

    funciones = {
        "x**(1/n)": "ⁿ√x",
        "e**x": "eˣ",
        "log(x, n)": "logₙ(x)",
        "sqrt(x)": "√x",
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

    print(f"{'Comando':<10} | {'Función'}")
    print("-" * 23)

    for comando, funcion in funciones.items():
        print(f"{comando:<10} | {funcion}")
    print()

while True:
	prints()
	while True:
		try:
			fn:str = input("Introduce la función a evaluar: ")
			fn = r.preparar_funcion(fn)
			break
		except Exception:
			print("Función inválida. Utilice la sintaxis indicada.")
	
	dominio = r.CalcularDominio(fn)
	dominio_str = r.formatear_dominio(dominio)

	print(f"El dominio de la función es: {dominio_str}")

	if(input("¿Desea introducir un intervalo de búsqueda de raíces? (s/n): ").lower() == "s"):
		while True:
			try:
				a = sp.Float(input("Ingrese el inicio del intervalo: "),64)
				b = sp.Float(input("Ingrese el final del intervalo: "),64)

				if r.intervalo_en_dominio(dominio, a, b):	break
				else: print("El intervalo no pertenece al dominio.")

			except ValueError:	print("Debe ingresar números válidos.")
	
	else:
		print("Se intentará encontrar automáticamente un intervalo adecuado...")
		intervalos = bu.BuscarIntervalosRaiz(fn, dominio)

		print("El método de Bolzano exige una función continua en el intervalo, que además tenga signos opuestos en los extremos del mismo. Por lo tanto, se han detectado los siguientes intervalos que cumplen estas condiciones, evaluando a su función introducida como una conjunción de funciones por tramos, donde a cada tramo se le ha buscado individualmente un único intervalo contenedor de raiz (o la propia raiz si accidentalmente fue hayada durante dicha búsqueda):")

		#	Se extraen los dominios de cada tramo para mostrar al usuario
		excluido = bu._excluido_de(dominio)
		dominios = [
			r._fmt_conjunto(
				sp.Complement(sp.Interval(a, b, izq, der), excluido)
				if excluido is not None
				else sp.Interval(a, b, izq, der)
			)
			for a, b, izq, der in bu._intervalos_base(dominio)
		]
				
		for i, item in enumerate(intervalos):
			print(f"\n{i+1}) Para el dominio {dominios[i]}:")
			if item is None:
				print("   No se halló posible raíz.")
							
			elif isinstance(item, tuple):
				print(
					f"   Subintervalo contenedor de raíz:"
					f" [{round(item[0],6)}, {round(item[1],6)}]"
				)

			else:
				print(
					f"   Se halló raíz exacta:"
					f" x = {round(item,6)}"
				)

		print("\nSeleccione el subintervalo sobre el que desea trabajar:")

		while True:
			try:
				eleccion = int(input("> ")) - 1

				if 0 <= eleccion < len(intervalos):	break
				else:	print("Seleccione una opción válida.")

			except ValueError:	print("Debe ingresar un número.")

		item = intervalos[eleccion]

		if isinstance(item, tuple): a,b = map(lambda x: sp.Float(x,64), item)
		else:
			if item is None:
				print("No había raíces detectables en ese intervalo.")
			else:
				print(f"La raíz de ese intervalo es x = {round(item,6)}")

	try: # validar que el intervalo seleccionado cumple con las condiciones de Bolzano
		if((bu.evaluar(fn, a) * bu.evaluar(fn, b)))<0:
			break
		else:
			print("\nEl intervalo seleccionado no es válido para practicar Bolzano.")
			print("Debe cumplirse f(a)·f(b) < 0.")
			print("Inténtelo nuevamente o finalice la ejecución si quedó conforme al resultado.\n")
		
	except:		
		pass
	if input("desea intentar nuevamente? (s/n): ").lower() == "s":
		continue
	else: 
		print("Saliendo del programa.")
		exit()

# Cuando se llega acá, se ejecuta el algoritmo de Bolzano
print("="*40)
print("DESARROLLO DEL ALGORITMO DE BOLZANO")
print("="*40)

# Para saber la cantidad de iteraciones, se solicita una tolerancia o la propia cantidad de iteraciones
selec: str = ""
n = 0
while selec not in ["1", "2"]:
	selec = input("""¿Desea ingresar una tolerancia o una cantidad de iteraciones?
	1) Tolerancia
	2) Cantidad de iteraciones\n""")
	if selec == "1":
		while True:
			try:
				tol = sp.Float(input("Ingrese la tolerancia deseada: "),64)
				if tol > 0:
					n = f.cantidad_iteraciones(a, b, tol)
					print(f"Se realizarán {n} iteraciones para alcanzar la tolerancia deseada si no se encuentra una raíz exacta.")
					break
				else:	print("La tolerancia debe ser un número positivo.")
			except ValueError:	print("Debe ingresar un número válido.")
	elif selec == "2":
		while True:
			try:
				n = int(input("Ingrese la cantidad de iteraciones deseada: "))
				if n > 0:
					print(f"Se realizarán {n} iteraciones.")
					break
				else:	print("La cantidad de iteraciones debe ser un número entero positivo.")
			except ValueError:	print("Debe ingresar un número válido.")
	else:
		print("Seleccione una opción válida.")

resultado, historial = f.iterar(fn, a, b, n)

for i, (a_i, b_i, x_i) in enumerate(historial, start=1):
    print(f"Iteración {i}")
    print(f"Intervalo: [{interfaz.formato_numero(a_i)}, {interfaz.formato_numero(b_i)}]")
    print(f"x = {interfaz.formato_numero(x_i)}")
    print(f"f(x) = {interfaz.formato_numero(f.evaluar(fn, x_i))}")
    print()

if f.evaluar(fn, resultado) == 0:
    print(f"Resultado final: raíz exacta x = {interfaz.formato_numero(resultado)}")
else:
    print(f"Resultado final (raíz aproximada): x = {interfaz.formato_numero(resultado)}")

interfaz.mostrar_bolzano(fn, historial, resultado)