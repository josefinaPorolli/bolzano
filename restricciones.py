from sympy import *
from sympy.calculus.util import continuous_domain
from sympy.parsing.sympy_parser import parse_expr, standard_transformations

NAMESPACE = {
    "e": E, "E": E, "pi": pi,
    "sin": sin, "cos": cos, "tan": tan,
    "asin": asin, "acos": acos, "atan": atan,
    "sqrt": sqrt, "log": log, "ln": log, "exp": exp,
    "sinh": sinh, "cosh": cosh, "tanh": tanh,
    "sec": sec, "csc": csc, "cot": cot,
    "csch": csch, "sech": sech, "coth": coth,
}

def preparar_funcion(fn):
    return parse_expr(fn, local_dict=NAMESPACE, transformations=standard_transformations, evaluate=True)

def obtener_variable(expr):
    return next(iter(expr.free_symbols), None)

def restricciones_log(expr, x):
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

def restricciones_trigonometricas(expr):
    condiciones = []
    argumento = expr.args[0]
    if expr.func in (tan, sec):
        condiciones.append(Ne(cos(argumento), 0))
    elif expr.func in (cot, csc):
        condiciones.append(Ne(sin(argumento), 0))
    return condiciones

def obtener_condiciones(expr, x):
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

def _es_imageset_lineal_enteros(s):
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

def _coef_offset(s):
    lam = s.lamda
    n = lam.variables[0]
    expr = lam.expr
    return simplify(expr.diff(n)), simplify(expr.subs(n, 0))

def fusionar_periodicos(conjunto):
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


# ============================================================
# FORMATEO ROBUSTO (Interval, Union, Complement, ImageSet, FiniteSet)
# ============================================================

def _fmt_intervalo(iv):
    izq = "-∞" if iv.start == -oo else str(iv.start)
    der = "∞" if iv.end == oo else str(iv.end)
    a = "(" if iv.left_open else "["
    b = ")" if iv.right_open else "]"
    return f"{a}{izq},{der}{b}"

def _fmt_imageset(s):
    lam = s.lamda
    n = lam.variables[0]
    expr_str = str(lam.expr).replace(str(n), "n")
    return "{" + expr_str + " : n∈ℤ}"

def _fmt_conjunto(s):
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

def _fmt_excluido(s):
    if isinstance(s, Union):
        return "(" + " ∪ ".join(_fmt_conjunto(a) for a in s.args) + ")"
    return _fmt_conjunto(s)

def formatear_dominio(dominio):
    return "D: " + _fmt_conjunto(dominio)


# ============================================================
# CÁLCULO DE DOMINIO
# ============================================================

def CalcularDominio(fn):
    variable = obtener_variable(fn)
    if variable is None:
        return S.Reals

    try:
        return simplify(continuous_domain(fn, variable, S.Reals))
    except Exception:
        pass

    # fallback: condiciones manuales. Las Ne (p. ej. de tan/cot/sec/csc,
    # o de denominadores) se resuelven con solveset (da el ImageSet
    # periódico exacto) en vez de solve_univariate_inequality, que no
    # está pensado para "≠" y puede devolver solo un período acotado.
    condiciones = obtener_condiciones(fn, variable)
    dominio = S.Reals

    for c in condiciones:
        c = simplify(c)
        if c == True:
            continue

        if isinstance(c, Ne):
            expr_igual_cero = c.lhs - c.rhs
            excluidos = solveset(Eq(expr_igual_cero, 0), variable, domain=S.Reals)
            dominio = Complement(dominio, excluidos)
        else:
            dominio = Intersection(
                dominio,
                solve_univariate_inequality(c, variable, relational=False)
            )

    return simplify(dominio)


def intervalo_en_dominio(dominio, a, b):
    return Interval(a, b).is_subset(dominio)