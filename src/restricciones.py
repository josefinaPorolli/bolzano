import sympy as sp
from sympy import *
from sympy.calculus.util import continuous_domain
from sympy.parsing.sympy_parser import parse_expr, standard_transformations
import math

NAMESPACE = {
    "e": E, "E": E, "pi": pi,
    "sin": sin, "cos": cos, "tan": tan,
    "asin": asin, "acos": acos, "atan": atan,
    "sqrt": sqrt, "log": log, "ln": log, "exp": exp,
    "sinh": sinh, "cosh": cosh, "tanh": tanh,
    "sec": sec, "csc": csc, "cot": cot,
    "csch": csch, "sech": sech, "coth": coth,
}

def preparar_funcion(fn:str) -> sp.Expr: 
    return parse_expr(fn, local_dict=NAMESPACE, transformations=standard_transformations, evaluate=True)

def obtener_variable(expr: sp.Expr) -> sp.Symbol | None:
    return next(iter(expr.free_symbols), None)

def restricciones_log(expr: sp.Expr, x: sp.Symbol) -> list[sp.Relational]:
    condiciones = []
    if len(expr.args) == 1:
        condiciones.append(expr.args[0] > 0)
    elif len(expr.args) == 2:
        argumento, base = expr.args
        condiciones.append(argumento > 0)
        if base.has(x):
            condiciones.append(base > 0)
            condiciones.append(Ne(base, 1))
    return condiciones

def restricciones_trigonometricas(expr: sp.Expr) -> list[sp.Relational]:
    condiciones = []
    argumento = expr.args[0]
    if expr.func in (tan, sec):
        condiciones.append(Ne(cos(argumento), 0))
    elif expr.func in (cot, csc):
        condiciones.append(Ne(sin(argumento), 0))
    return condiciones

def obtener_condiciones(expr: sp.Expr, x: sp.Symbol) -> list[sp.Relational]:
    if expr.is_Function:
        condiciones = []
        if expr.func == log:
            condiciones += restricciones_log(expr, x)
        elif expr.func == sqrt:
            condiciones.append(expr.args[0] >= 0)
        elif expr.func in (asin, acos):
            condiciones.append(And(expr.args[0] >= -1, expr.args[0] <= 1))
        elif expr.func in (tan, cot, sec, csc):
            condiciones += restricciones_trigonometricas(expr)
        for arg in expr.args:
            condiciones += obtener_condiciones(arg, x)
        return condiciones

    if expr.is_Atom:
        return []

    condiciones = []
    for arg in expr.args:
        condiciones += obtener_condiciones(arg, x)

    if expr.is_Pow:
        base, exponente = expr.args
        if exponente.is_negative:
            condiciones.append(Ne(base, 0))

    return condiciones


# ============================================================
# FUSIÓN DE EXCLUSIONES PERIÓDICAS
# sympy resuelve p.ej. cos(x)=0 como la unión de DOS ImageSets de
# período 2π (uno para pi/2, otro para 3pi/2), en vez de darte
# directamente un único ImageSet de período π. Esto detecta ese
# patrón y lo colapsa a un solo período mínimo cuando es posible,
# p. ej.: {2nπ} ∪ {2nπ+π}  ->  {nπ}
# ============================================================

def _es_imageset_lineal_enteros(s:sp.Set) -> bool:
    if not isinstance(s, ImageSet):
        return False
    if len(s.args) < 2 or s.args[1] != S.Integers:
        return False
    lam = s.lamda
    if len(lam.variables) != 1:
        return False
    n = lam.variables[0]
    coef = lam.expr.diff(n)
    return not coef.has(n)

def _coef_offset(s:sp.ImageSet) -> tuple[sp.Expr, sp.Expr]:
    lam = s.lamda
    n = lam.variables[0]
    expr = lam.expr
    return simplify(expr.diff(n)), simplify(expr.subs(n, 0))

def fusionar_periodicos(conjunto: sp.Set) -> sp.Set:
    if isinstance(conjunto, ImageSet):
        piezas = [conjunto]
    elif isinstance(conjunto, Union):
        if not all(isinstance(a, ImageSet) for a in conjunto.args):
            return conjunto
        piezas = list(conjunto.args)
    else:
        return conjunto

    if not all(_es_imageset_lineal_enteros(p) for p in piezas):
        return conjunto

    datos = [_coef_offset(p) for p in piezas]
    periodos = set(d[0] for d in datos)
    if len(periodos) != 1:
        return conjunto

    periodo = periodos.pop()
    k = len(datos)
    nuevo_periodo = simplify(periodo / k)

    offsets_mod = sorted({simplify(Mod(o, periodo)) for _, o in datos}, key=lambda v: float(v))
    if len(offsets_mod) != k:
        return conjunto

    base = offsets_mod[0]
    esperados = sorted(
        (simplify(Mod(base + nuevo_periodo * i, periodo)) for i in range(k)),
        key=lambda v: float(v),
    )

    if offsets_mod != esperados:
        return conjunto

    n = Symbol('n', integer=True)
    return ImageSet(Lambda(n, base + n * nuevo_periodo), S.Integers)

def hay_excluido_en_rango(excluido, a, b):
    """¿Hay algún punto del conjunto excluido dentro del intervalo cerrado [a,b]?"""

    if excluido is None or excluido == S.EmptySet:
        return False

    a = float(a)
    b = float(b)

    if a > b:
        a, b = b, a

    if isinstance(excluido, Union):
        return any(hay_excluido_en_rango(p, a, b) for p in excluido.args)

    if isinstance(excluido, FiniteSet):
        return any(a <= float(p) <= b for p in excluido)

    if _es_imageset_lineal_enteros(excluido):
        lam = excluido.lamda
        n = lam.variables[0]
        expr = lam.expr

        coef = float(expr.diff(n))
        offset = float(expr.subs(n, 0))

        if coef == 0:
            return a <= offset <= b

        n_lo = (a - offset) / coef
        n_hi = (b - offset) / coef

        if coef < 0:
            n_lo, n_hi = n_hi, n_lo

        for n_val in range(math.floor(n_lo), math.ceil(n_hi) + 1):
            punto = offset + coef * n_val
            if a <= punto <= b:
                return True

        return False

    return False
# ============================================================
# FORMATEO ROBUSTO (Interval, Union, Complement, ImageSet, FiniteSet)
# ============================================================

def _fmt_intervalo(iv: sp.Interval) -> str:
    izq = "-∞" if iv.start == -oo else str(iv.start)
    der = "∞" if iv.end == oo else str(iv.end)
    a = "(" if iv.left_open else "["
    b = ")" if iv.right_open else "]"
    return f"{a}{izq},{der}{b}"

def _fmt_imageset(s: sp.ImageSet) -> str:
    lam = s.lamda
    n = lam.variables[0]
    expr_str = str(lam.expr).replace(str(n), "n")
    return "{" + expr_str + " : n∈ℤ}"

def _fmt_conjunto(s: sp.Set) -> str:
    if s == S.Reals:
        return "ℝ"
    if s == S.EmptySet:
        return "∅"
    if isinstance(s, Complement):
        base, excluido = s.args
        excluido = fusionar_periodicos(excluido)
        return f"{_fmt_conjunto(base)} - {_fmt_excluido(excluido)}"
    if isinstance(s, Interval):
        return _fmt_intervalo(s)
    if isinstance(s, FiniteSet):
        return "{" + ", ".join(str(e) for e in s) + "}"
    if isinstance(s, ImageSet):
        return _fmt_imageset(s)
    if isinstance(s, Union):
        return " ∪ ".join(_fmt_conjunto(a) for a in s.args)
    return str(s)

def _fmt_excluido(s: sp.Set) -> str:
    if isinstance(s, Union):
        return "(" + " ∪ ".join(_fmt_conjunto(a) for a in s.args) + ")"
    return _fmt_conjunto(s)

def formatear_dominio(dominio: sp.Set) -> str:
    return "D: " + _fmt_conjunto(dominio)


# ============================================================
# CÁLCULO DE DOMINIO
# ============================================================

def CalcularDominio(fn:sp.Expr) -> sp.Set:
    variable = obtener_variable(fn)
    if variable is None:
        return S.Reals

    try:
        dominio = simplify(continuous_domain(fn, variable, S.Reals))

        if isinstance(dominio, Complement):
            base, excluido = dominio.args
            dominio = Complement(base, fusionar_periodicos(excluido))

        return dominio

    except Exception:
        pass

    condiciones = obtener_condiciones(fn, variable)
    dominio = S.Reals

    for c in condiciones:
        c = simplify(c)
        if c == True:
            continue

        if isinstance(c, Ne):
            expr_igual_cero = c.lhs - c.rhs
            excluidos = solveset(Eq(expr_igual_cero, 0), variable, domain=S.Reals)
            excluidos = fusionar_periodicos(excluidos)
            dominio = Complement(dominio, excluidos)
        else:
            dominio = Intersection(
                dominio,
                solve_univariate_inequality(c, variable, relational=False)
            )

    dominio = simplify(dominio)

    if isinstance(dominio, Complement):
        base, excluido = dominio.args
        dominio = Complement(base, fusionar_periodicos(excluido))

    return dominio

def intervalo_en_dominio(dominio: sp.Set, a: sp.Float, b: sp.Float) -> bool:

    if a > b:
        a, b = b, a

    # Dominio = ℝ
    if dominio == S.Reals:
        return True

    # Dominio = Intervalo
    if isinstance(dominio, Interval):

        if dominio.left_open:
            if not (a > dominio.start):
                return False
        else:
            if not (a >= dominio.start):
                return False

        if dominio.right_open:
            if not (b < dominio.end):
                return False
        else:
            if not (b <= dominio.end):
                return False

        return True

    # Dominio = Unión de intervalos
    if isinstance(dominio, Union):
        return any(intervalo_en_dominio(parte, a, b)
                   for parte in dominio.args)

    # Dominio = Base - Exclusiones
    if isinstance(dominio, Complement):
        base, excluido = dominio.args

        if not intervalo_en_dominio(base, a, b):
            return False

        return not hay_excluido_en_rango(excluido, a, b)

    # Último intento usando SymPy
    r = Interval(a, b).is_subset(dominio)

    return bool(r) if r is not None else False