"""Punto de entrada minimo para demostrar el modulo de validaciones."""

from restricciones import analizar_restricciones


def main():
	errores = analizar_restricciones(radicando=4, divisor=2, argumento_log=10)
	if errores:
		print("Validaciones con errores:")
		for error in errores:
			print(f"- {error}")
	else:
		print("Validaciones matematicas correctas")


if __name__ == "__main__":
	main()
"validamos los puntos de divergencia"