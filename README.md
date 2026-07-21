# Ilustre del método de Bolzano

**Análisis Numérico - Universidad de Mendoza**
**Ciclo lectivo 2026**
**Integrantes:** Tomás Joaquín Aguinaga Oggero, Josefina Porolli Serpa

Herramienta en Python que, a partir de una función matemática escrita como texto (por ej. `"(e**x+sqrt(x+1)*x*3)/x"`), calcula su **dominio real**, encuentra automáticamente **intervalos donde aplicar el teorema de Bolzano** y ejecuta el **método de bisección** paso a paso — mostrando cada iteración en tabla y en una animación gráfica. Incluye una versión por **consola (CLI)** y una **interfaz gráfica (GUI)** en Tkinter, además de un instalador que empaqueta la GUI como ejecutable de Windows (`Bolzano.exe`).

**Problemática resuleta:**

En Análisis Numérico es habitual toparse con ecuaciones que no tienen solución algebraica exacta —o que directamente involucran funciones trascendentes (exponenciales, logarítmicas, trigonométricas)— donde despejar la incógnita a mano es inviable. Antes de siquiera intentar aproximar una raíz, hay dos problemas previos que suelen resolverse "a ojo" y a mano en la cursada:

Determinar el dominio real de la función. Cualquier función con raíces, logaritmos, divisiones o funciones trigonométricas inversas tiene restricciones que hay que identificar y combinar correctamente (intersección de condiciones, exclusión de puntos, periodicidad). Hacerlo manualmente es tedioso y propenso a errores, sobre todo con funciones compuestas.
Encontrar manualmente, por prueba y error, un intervalo [a, b] donde f(a) y f(b) tengan signos opuestos, condición necesaria para aplicar el teorema de Bolzano y garantizar que exista una raíz. Elegir mal ese intervalo (por ejemplo, por no darse cuenta de una asíntota o de que el intervalo cae fuera del dominio) lleva a resultados inválidos o directamente a que el método de bisección no converja.

Este proyecto automatiza esas dos etapas previas —cálculo del dominio y búsqueda de un intervalo válido— y luego ejecuta el método de bisección paso a paso, permitiendo verificar visualmente (con la animación) cómo converge el algoritmo. De esta forma, un estudiante o docente puede ingresar cualquier función arbitraria y obtener de punta a punta el dominio, el intervalo de aplicación de Bolzano y la raíz aproximada, sin tener que resolver cada etapa a mano.

---

## Estructura del repositorio

```
bolzano/
├── README.md
├── installer.bat          # script que arma el .exe con PyInstaller
├── Bolzano.exe          # ejecutable ya generado
├── micon.ico
└── src/
    ├── restricciones.py         # cálculo del dominio real de la función
    ├── BuscadorDeIntervalos.py  # búsqueda de intervalos/raíces (Bolzano)aíces (Bolzano)
    ├── funciones_bolzano.py     # método de bisección
    ├── interfaz.py              # animación matplotlib del proceso (paleta Rosé Pine)
    ├── CLI.py                   # programa por consola
    ├── GUI.py                   # interfaz gráfica (la que empaqueta el instalador)
    └── requirements.txt
```

## Flujo general

```
fn = "(e**x + sqrt(x+1)*x*3) / x"
        │
        ▼
restricciones.py → CalcularDominio(fn)
        │
        ▼
dominio = D: (-∞,0) ∪ [-1,0) ...  (objeto sympy.Set)
        │
        ▼
BuscadorDeIntervalos.py → BuscarIntervalosRaiz(fn, dominio)
        │
        ▼
[(-1, 0), (0, 1), None, ...]   ← un intervalo/raíz/None por cada tramo del dominio
        │
        ▼
funciones_bolzano.py → iterar(fn, a, b, n)  (bisección)
        │
        ▼
resultado + historial de iteraciones → mostrado en CLI o animado en GUI (interfaz.py)
```

---

## Módulo 1: `restricciones.py` — Dominio de la función

Calcula el **dominio real** de la función. Usa como base `sympy.calculus.util.continuous_domain` y, si esa vía falla, recurre a un análisis propio recursivo de la expresión (revisa cada `sqrt`, `log`, `asin`/`acos`, división, etc. y arma las condiciones correspondientes).

**Restricciones que reconoce:**

| Función | Restricción |
|---|---|
| `sqrt(a)` | `a ≥ 0` |
| `log(a)` / `log(a, base)` | `a > 0` (y `base > 0`, `base ≠ 1` si la base depende de x) |
| `asin(a)`, `acos(a)` | `-1 ≤ a ≤ 1` |
| `a / b` | `b ≠ 0` |
| `tan(a)`, `sec(a)` | `cos(a) ≠ 0` |
| `cot(a)`, `csc(a)` | `sin(a) ≠ 0` |

Las funciones trigonométricas dan lugar a **exclusiones periódicas** (por ej. `tan(x)` excluye infinitos puntos). El módulo detecta cuando dos series periódicas de sympy corresponden en realidad a un único período menor y las fusiona (`fusionar_periodicos`), para que el dominio se muestre de forma compacta.

**Salida:** el dominio es un objeto `sympy.Set` (`Interval`, `Union`, `Complement`, etc.), formateado a texto legible con `formatear_dominio`, por ejemplo:

```
D: ℝ - {π/2 + nπ : n∈ℤ}
D: [-1,0) ∪ (0,∞)
```

**Funciones públicas principales:**

- `preparar_funcion(fn: str) -> sp.Expr` — parsea el string a expresión sympy.
- `CalcularDominio(fn) -> sp.Set` — dominio real de la función.
- `formatear_dominio(dominio) -> str` — texto legible del dominio.
- `intervalo_en_dominio(dominio, a, b) -> bool` — valida que `[a,b]` esté contenido en el dominio.

---

## Módulo 2: `BuscadorDeIntervalos.py` — Búsqueda de subintervalos contenedores de raíces

Recibe el dominio ya calculado y busca, **en cada tramo continuo por separado**, un intervalo donde `f(a)·f(b) < 0` (condición del teorema de Bolzano) o directamente una raíz exacta.

Estrategia según el tipo de tramo:

| Tramo | Estrategia |
|---|---|
| `[a, b]` acotado | lo divide en **99 secciones** iguales y evalúa signo en cada extremo |
| con algún borde abierto | igual, pero se corre `1e-6` hacia adentro del borde abierto antes de evaluar |
| `[a, ∞)` / `(-∞, b]` | **búsqueda exponencial** (`a+2ⁿ`, hasta 32 pasos) hacia el infinito correspondiente |
| `(-∞, ∞)` | búsqueda exponencial **simétrica** desde `x=0`, a derecha e izquierda a la vez |

Puntos adicionales:

- Si `|f(x)|` supera un umbral (`1e6`) se descarta como posible asíntota, no como dato válido.
- Si un cambio de signo detectado coincide con un punto excluido del dominio (por ej. una asíntota), se descarta: no es una raíz, es un salto de discontinuidad.
- `BuscarIntervalosRaiz(fn, dominio)` devuelve una **lista**, un elemento por cada tramo del dominio: un número (raíz exacta), una tupla `(a, b)` (intervalo con cambio de signo) o `None` (no se encontró nada en ese tramo).

---

## Módulo 3: `funciones_bolzano.py` — Método de bisección

Implementa la bisección clásica sobre el intervalo `[a, b]` elegido:

- `cantidad_iteraciones(a, b, tolerancia)` — calcula cuántas iteraciones `n` hacen falta para que `(b-a)/2ⁿ < tolerancia`.
- `iterar(funcion, a, b, n)` — ejecuta hasta `n` iteraciones (o corta antes si encuentra una raíz exacta), devolviendo el resultado final y el **historial** completo `(a, b, x)` de cada paso.
- Todo el cálculo usa `sympy.Float` con 64 dígitos de precisión.

---

## Módulo 4: `interfaz.py` — Animación del proceso

Contiene la lógica de graficado con `matplotlib` (paleta oscura "Rosé Pine") reutilizada tanto por la CLI como por las GUI:

- Dibuja la función, marca cada iteración de la bisección (intervalo, punto medio) y anima la convergencia con `FuncAnimation`.
- Maneja también el caso de raíz exacta encontrada sin iterar (`mostrar_raiz_exacta`).

---

## `CLI.py` — Versión por consola

Flujo interactivo:

1. Pide la función y la valida (reintenta si la sintaxis es inválida).
2. Calcula y muestra el dominio.
3. Pregunta si el usuario quiere ingresar manualmente un intervalo `[a, b]`, o si prefiere que el programa busque uno automáticamente con `BuscarIntervalosRaiz` (mostrando las opciones encontradas por tramo para elegir).
4. Valida que el intervalo cumpla `f(a)·f(b) < 0`.
5. Pide tolerancia deseada o cantidad de iteraciones.
6. Ejecuta la bisección y muestra cada iteración (`intervalo`, `x`, `f(x)`) y el resultado final.

Ejecutar:

```bash
cd src
python CLI.py
```

---

## `GUI.py` — Interfaz gráfica

Aplicación Tkinter en pantalla completa que sigue el mismo flujo que `CLI.py` pero por pasos guiados (wizard), reutilizando toda la lógica de los módulos anteriores sin modificarlos:

- **Panel izquierdo:** gráfico en vivo de la función (se actualiza al definir el intervalo) y, debajo, los controles del paso actual.
- **Panel derecho:** tabla de equivalencias de sintaxis matemática y la función actualmente cargada.
- **Pasos:** 1) ingresar función y calcular dominio → 2) elegir intervalo (manual o automático) → 3) elegir criterio de corte (tolerancia / cantidad de iteraciones) → 4) calcular la raíz → 5) ver la tabla de iteraciones y reproducir la animación del proceso.

- **`GUI.py`** — versión original, es la que empaqueta actualmente `instaler.bat` en el ejecutable. La animación se abre en una ventana aparte de matplotlib con botones "Reiniciar"/"Cerrar" superpuestos.

Ejecutar cualquiera de las dos:

```bash
cd src
python GUI.py
```

---

## Generar el ejecutable (`instaler.bat`)

En Windows, `instaler.bat`:

1. Crea un entorno virtual e instala `src/requirements.txt`.
2. Empaqueta `src/GUI.py` con PyInstaller (`--onefile --windowed`, ícono `micon.ico`) en `Bolzonaro.exe`.
3. Limpia los archivos temporales de build.

```bat
instaler.bat
```

---

## Sintaxis de funciones aceptada

Las funciones se escriben en sintaxis Python/SymPy:

| Matemática | String a ingresar |
|---|---|
| eˣ | `e**x` |
| x² | `x**2` |
| ⁿ√x | `x**(1/n)` |
| √x | `sqrt(x)` |
| ln(x) | `log(x)` o `ln(x)` |
| logₙ(x) | `log(x, n)` |
| sin, cos, tan | `sin(x)`, `cos(x)`, `tan(x)` |
| asin, acos, atan | `asin(x)`, `acos(x)`, `atan(x)` |
| sec, csc, cot | `sec(x)`, `csc(x)`, `cot(x)` |
| sinh, cosh, tanh, sech, csch, coth | igual que las trigonométricas, con sufijo `h` |
| (f·g)/h | `(f*g)/h` |

---

## Requisitos

```
matplotlib==3.11.0
cython==3.2.5
sympy==1.14.0
pyinstaller
```

```bash
pip install -r src/requirements.txt
```

---

## Limitaciones conocidas

- La búsqueda exponencial de intervalos tiene un máximo de 32 pasos; raíces extremadamente alejadas del origen pueden no detectarse.
- Si la función tiene infinitas raíces (como `sin(x)`), solo se reporta la primera encontrada en cada tramo/dirección.
- La detección de "raíz exacta" depende de precisión numérica flotante (64 decimales significativos); raíces irracionales se reportan como intervalo, no como valor exacto.
- En `GUI.py` (versión empaquetada en el `.exe`), la ventana de animación usa botones superpuestos sobre la figura de matplotlib en vez de estar embebidos nativamente.

Link del repositorio: [text](https://github.com/josefinaPorolli/bolzano)