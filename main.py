"El usuario introduce una fn genérica"
"Se emplean las restricciones para restringir puntos o rangos"
"se conforma un dominio"
"Se le solicita una intervalo de búsqueda de raíces"
"En caso de optar por no introducir uno, se realiza una búsqueda simétrica exponencial"
"Se aplica Bolzano"
"Se aplica la UI"
import	restricciones as r
import BuscadorDeIntervalos as bu
import funciones_bolzano as f
a,b=0,0

def prints():
    """Imprime una tabla de funciones genéricas y sus representaciones matemáticas."""
    print("Las funciones en programación no se dictan igual que en matemáticas, por lo que se emplean representaciones a nivel código de las mismas.")
    print("Se le adjunta a usted una tabla de equivalencias entre dichas funciones y su representación:")
    dict ={
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
    print(f"{'Comando:':14}{'Fn:'}")
    for each in dict:
        print(f"{each:10} -> {dict[each]}")


while True:
	prints()
	# fn = "log(x+5) + sqrt(x+3) - 1/x + sin(x) - (x-2)"
	# fn = "1"
	while True:
		fn = input("Introduce la función a evaluar: ")
		if r.validar_funciones(fn): break
		print("Función inválida. Utilice la sintaxis indicada.")
	
	dominio = r.CalcularDominio(fn)
	dominio_str = r.formatear_dominio(dominio)

	print(f"El dominio de la función es: {dominio_str}")

	if(input("¿Desea introducir un intervalo de búsqueda de raíces? (s/n): ").lower() == "s"):
		while True:
			try:
				a = float(input("Ingrese el inicio del intervalo: "))
				b = float(input("Ingrese el final del intervalo: "))

				if r.intervalo_en_dominio(dominio, a, b):	break
				else: print("El intervalo no pertenece al dominio.")

			except ValueError:	print("Debe ingresar números válidos.")
	
	else:
		print("Se intentará encontrar automáticamente un intervalo adecuado...")
		intervalos = bu.BuscarIntervalosRaiz(fn, dominio_str)

		print("El método de Bolzano exige una función continua en el intervalo, que además tenga signos opuestos en los extremos del mismo. Por lo tanto, se han detectado los siguientes intervalos que cumplen estas condiciones, evaluando a su función introducida como una conjunción de funciones por tramos, donde a cada tramo se le ha buscado individualmente un único intervalo contenedor de raiz (o la propia raiz si accidentalmente fue hayada durante dicha búsqueda):")
		print(intervalos)

		#	Se extraen los dominios de cada tramo para mostrar al usuario
		dominios = dominio_str[4:-1].split(", ")
		
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

		if isinstance(item, tuple):	a,b = item
		else:
			if item is None:
				print("No había raíces detectables en ese intervalo.")
			else:
				print(f"La raíz de ese intervalo es x = {round(item,6)}")

	try: # validar que el intervalo seleccionado cumple con las condiciones de Bolzano
		if((bu.evaluar(bu.set_funcion(fn), a) * bu.evaluar( bu.set_funcion(fn), b)))<0:
			break
		else:
			print("\nEl intervalo seleccionado no es válido para practicar Bolzano.")
			print("Debe cumplirse f(a)·f(b) < 0.")
			print("Ingrese nuevamente un intervalo o finalice la ejecución si quedó conforme al resultado.\n")
		
	except:		
		print("Mi tomate es gei")
	if input("desea intentar nuevamente? (s/n): ").lower() == "s":
		continue
	else: 
		print("Saliendo del programa.")
		exit()

print("ejecutan a bolzonaro")
