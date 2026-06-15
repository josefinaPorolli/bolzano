# Calculadora de Dominio y Raíces — `restricciones.py` + `BuscadorDeIntervalo.py`

Sistema modular en Python para analizar funciones matemáticas escritas como strings. Dado un string como `"(e**x+sqrt(x+1)*x*3)/x"`, el sistema calcula automáticamente el dominio real y busca intervalos donde existen raíces.

---

## Flujo general

```
fn = "(e**x + sqrt(x+1)*x*3) / x"
         │
         ▼
  restricciones.py
  CalcularDominio(fn)
         │
         ▼
  dominio = "D: {[-1,0), (0,∞)}"
         │
         ▼
    BuscadorDeIntervalo.py
  BuscarIntervalosRaiz(fn, dominio)
         │
         ▼
  [(-1, 0), (0, 1)]   ← lista de intervalos o raíces exactas
```

---

## Módulo 1: `restricciones.py`

### ¿Qué hace?

Calcula el **dominio real** de una función analizando su estructura sintáctica. No usa un CAS para parsear la expresión — la recorre carácter por carácter, identifica términos, factores y funciones, y aplica las restricciones matemáticas conocidas.

### Cómo lee la función

La función se recorre en capas:

1. **Separación en términos** — se corta por `+` o `-` que estén en el nivel raíz (fuera de paréntesis). Así `e**x + sqrt(x+1)*x` da dos términos: `e**x` y `sqrt(x+1)*x`.

2. **Separación en factores** — cada término se corta por `*` o `/`, respetando `**` (potencia) como operador indivisible. Así `sqrt(x+1)*x*3` da tres factores: `sqrt(x+1)`, `x`, `3`.

3. **Detección de argumento** — si un factor tiene paréntesis, se extrae su interior. Para `sqrt(x+1)` el argumento es `x+1`.

> **Regla de paréntesis:** un grupo como `(x+1)` se trata como una unidad en la capa actual. Sus subexpresiones solo se analizan si el grupo entero es un factor con nombre de función reconocida (como `sqrt`) o si es un paréntesis puro `(...)` sin nombre adelante.

### Restricciones aplicadas

| Función | Restricción |
|---|---|
| `sqrt(a)` | `a >= 0` |
| `log(a)` | `a > 0` |
| `asin(a)` | `-1 <= a <= 1` |
| `acos(a)` | `-1 <= a <= 1` |
| `a / b` | `b ≠ 0` |

Las funciones sin restricción (`sin`, `cos`, `tan`, `exp`, `sinh`, `cosh`, etc.) se reconocen como atómicas y no generan ninguna condición.

### Recursión

El análisis es **recursivo**: cuando se encuentra una función con restricción, se aplica la condición sobre su argumento y luego se analiza ese argumento como si fuera una nueva función completa. Esto permite manejar composiciones como `sqrt(log(x))`:

- `sqrt(log(x))` → restricción: `log(x) >= 0`
- argumento `log(x)` → restricción: `x > 0`
- resultado: `x > 0` y `log(x) >= 0` → dominio: `x >= 1`

### Resolución del dominio

Una vez obtenidas todas las condiciones como inecuaciones (`x+1 >= 0`, `x ≠ 0`, etc.), se resuelven con `sympy` y se intersectan sucesivamente sobre los reales.

### Formato de salida

El dominio se devuelve como string con la notación de intervalos estándar:

```
D: {[-1,0), (0,∞)}
```

- `[` y `]` indican extremo cerrado (incluido)
- `(` y `)` indican extremo abierto (excluido)
- `∞` y `-∞` para infinitos
- Múltiples intervalos separados por `, ` dentro de `{}`

### Ejemplos

| Función | Condiciones | Dominio |
|---|---|---|
| `sqrt(x+1)` | `x+1 >= 0` | `D: {[-1,∞)}` |
| `log(x)` | `x > 0` | `D: {(0,∞)}` |
| `e**x/x` | `x ≠ 0` | `D: {(-∞,0), (0,∞)}` |
| `(e**x+sqrt(x+1)*x*3)/x` | `x ≠ 0`, `x+1 >= 0` | `D: {[-1,0), (0,∞)}` |
| `sin(x-1)` | _(ninguna)_ | `D: {(-∞,∞)}` |
| `asin(x)/sqrt(x)` | `-1<=x<=1`, `x>=0`, `x≠0` | `D: {(0,1]}` |

### Uso

```python
import restricciones as r

fn = "(e**x + sqrt(x+1)*x*3) / x"
dominio = r.CalcularDominio(fn)
print(dominio)
# D: {[-1,0), (0,∞)}
```

---

## Módulo 2: `BuscadorDeIntervalo.py`

### ¿Qué hace?

Dado el dominio calculado por `restricciones.py`, busca **intervalos donde existe al menos una raíz** (un valor de `x` donde `f(x) = 0`). Aplica el **teorema de Bolzano**: si `f(x₀) * f(x₁) < 0` en un intervalo `[x₀, x₁]`, entonces existe al menos una raíz en ese intervalo.

### Estrategia por tipo de intervalo

El módulo analiza cada intervalo del dominio por separado y aplica una estrategia diferente según su forma:

---

#### Intervalo cerrado `[a, b]`

Divide el intervalo en **9 secciones iguales** de tamaño `(b-a)/9` y evalúa el signo en cada extremo de sección. Si hay cambio de signo, reporta esa sección.

```
[a ----+----+----+----+----+----+----+----+---- b]
  sec1  sec2  sec3  ...                      sec9
```

**Ejemplo:** `[-1, 8]` con `f(x) = x² - 4`

- sección `[-1, 0]`: `f(-1)=−3`, `f(0)=−4` → sin cambio
- sección `[0, 1]`: `f(0)=−4`, `f(1)=−3` → sin cambio
- sección `[1, 2]`: `f(1)=−3`, `f(2)=0` → **raíz exacta en x=2**
- ...

---

#### Intervalo semiabierto `(a, b)`, `[a, b)`, `(a, b]`

Igual que el cerrado, pero los extremos abiertos se desplazan una **milésima** hacia adentro antes de dividir en 9:

- `(a, b)` → trabaja sobre `[a+0.001, b-0.001]`
- `[a, b)` → trabaja sobre `[a, b-0.001]`
- `(a, b]` → trabaja sobre `[a+0.001, b]`

Esto evita evaluar en puntos excluidos del dominio (como denominadores que se anulan).

---

#### Intervalo semiabierto hacia el infinito `[a, ∞)` o `(a, ∞)`

Usa **búsqueda exponencial hacia la derecha**: evalúa `f(a)` y luego `f(a + 2ⁿ)` para `n = 0, 1, 2, ..., 11` (máximo 12 pasos). Se detiene al encontrar la primera raíz o intervalo con cambio de signo.

```
a, a+1, a+2, a+4, a+8, a+16, ..., a+2048
```

Si el extremo `a` es abierto, se suma la milésima antes de empezar.

**Ejemplo:** `[0, ∞)` con `f(x) = x - 3`

- `f(0) = -3`, `f(1) = -2` → sin cambio
- `f(0) = -3`, `f(2) = -1` → sin cambio
- `f(0) = -3`, `f(4) = 1` → **cambio de signo → intervalo `(0, 4)`**

---

#### Intervalo semiabierto hacia el infinito negativo `(-∞, b]` o `(-∞, b)`

Igual pero **hacia la izquierda**: evalúa `f(b)` y luego `f(b - 2ⁿ)` para `n = 0, 1, ..., 11`.

---

#### Intervalo total `(-∞, ∞)`

**Búsqueda exponencial simétrica** desde `x = 0`: simultáneamente busca hacia la derecha (`0 + 2ⁿ`) y hacia la izquierda (`0 - 2ⁿ`), con máximo 12 pasos en cada dirección. Se detiene en cada dirección al encontrar la primera raíz.

```
... -2048, -1024, ..., -2, -1, 0, 1, 2, ..., 1024, 2048 ...
```

---

### Raíces exactas

En cualquier punto evaluado durante la búsqueda, si `f(x) = 0` exactamente, el punto se agrega directamente a la lista de resultados como número suelto (no como tupla) y la búsqueda en esa dirección se detiene.

---

### Formato de salida

`BuscarIntervalosRaiz` devuelve una **lista** donde cada elemento es:

- Un **número** (`float` o `int`) si se encontró una raíz exacta
- Una **tupla `(a, b)`** si se encontró un intervalo con cambio de signo

```python
[1, (-4, 0), (3.5, 4.0)]
#  ^raíz      ^intervalo   ^intervalo
```

Para decodificar desde main:

```python
for item in intervalos:
    if isinstance(item, tuple):
        print(f"Intervalo con raíz: [{round(item[0],6)}, {round(item[1],6)}]")
    else:
        print(f"Raíz exacta: x = {round(item, 6)}")
```

---

### Ejemplos completos

**`sin(x - 1)`** — dominio `(-∞, ∞)`

```
Búsqueda simétrica desde 0:
  f(0) = sin(-1) ≈ -0.841
  derecha: f(1) = sin(0) = 0 → Raíz exacta en x = 1
  izquierda: f(-4) = sin(-5) ≈ 0.959 → cambio de signo con f(0) → intervalo (-4, 0)
Resultado: [1, (-4, 0)]
```

**`x**2 - 2`** — dominio `(-∞, ∞)`

```
Búsqueda simétrica desde 0:
  f(0) = -2
  derecha: f(2) = 2 → cambio de signo → intervalo (0, 2)
  izquierda: f(-2) = 2 → cambio de signo → intervalo (-2, 0)
Resultado: [(-2, 0), (0, 2)]
```

**`e**x / x`** — dominio `(-∞, 0), (0, ∞)`

```
Intervalo (-∞, 0): búsqueda exponencial izquierda desde -0.001
  f(-0.001) ≈ -1000 → nunca cambia de signo
Intervalo (0, ∞): búsqueda exponencial derecha desde 0.001
  f(0.001) ≈ 1001 → nunca cambia de signo
Resultado: []  ← sin raíces reales
```

---

## Uso completo desde `main.py`

```python
import restricciones as r
import BuscadorDeIntervalo as b

fn = input("Introduce la función: ")

dominio = r.CalcularDominio(fn)
print(f"Dominio: {dominio}")

intervalos = b.BuscarIntervalosRaiz(fn, dominio)

if not intervalos:
    print("No se encontraron raíces.")
else:
    for item in intervalos:
        if isinstance(item, tuple):
            print(f"Intervalo con raíz: [{round(item[0],6)}, {round(item[1],6)}]")
        else:
            print(f"Raíz exacta: x = {round(item, 6)}")
```

---

## Sintaxis de funciones aceptadas

Las funciones deben escribirse en sintaxis Python/SymPy:

| Matemática | String a ingresar |
|---|---|
| eˣ | `e**x` |
| x² | `x**2` |
| √(x+1) | `sqrt(x+1)` |
| ln(x) | `log(x)` |
| sen(x) | `sin(x)` |
| arcsen(x) | `asin(x)` |
| arccos(x) | `acos(x)` |
| (f·g)/h | `(f*g)/h` |

---

## Limitaciones conocidas

- La búsqueda exponencial tiene un máximo de **12 pasos** (llega hasta `2¹¹ = 2048` unidades desde el origen). Funciones con raíces muy lejanas del origen pueden no ser detectadas.
- Si la función tiene infinitas raíces (como `sin(x)`), solo se reportan las primeras encontradas en cada dirección.
- La detección de raíz exacta depende de precisión numérica flotante; raíces irracionales no se detectan como exactas sino como intervalos.