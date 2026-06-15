import math

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def f(x):
    return (math.cos(x) - math.exp(x)) * (x ** 3)


def smoothstep(t):
    return t * t * (3.0 - 2.0 * t)


def lerp(left, right, t):
    return left + (right - left) * t


def sample_window(x_min, x_max, n=400):
    xs = [x_min + (x_max - x_min) * i / (n - 1) for i in range(n)]
    ys = [f(x) for x in xs]
    y_min = min(ys)
    y_max = max(ys)
    margen = max(0.4, 0.18 * (y_max - y_min if y_max != y_min else 1.0))
    return xs, ys, y_min - margen, y_max + margen


def buscar_raiz_referencia(a, b, iteraciones=80):
    fa = f(a)
    fb = f(b)

    if fa == 0:
        return a
    if fb == 0:
        return b

    for _ in range(iteraciones):
        xn = (a + b) / 2.0
        fxn = f(xn)
        if fa * fxn < 0:
            b = xn
            fb = fxn
        else:
            a = xn
            fa = fxn
    return (a + b) / 2.0


def construir_pasos():
    pasos = []
    a = -2.0
    b = -1.0
    ancho_inicial = abs(b - a)
    raiz_referencia = buscar_raiz_referencia(a, b)

    for indice in range(10):
        xn = (a + b) / 2.0
        fa = f(a)
        fb = f(b)
        fxn = f(xn)
        error_real = abs(raiz_referencia - xn)
        error_esperado = ancho_inicial / (2 ** (indice + 1))

        if fa * fxn < 0:
            nuevo_a = a
            nuevo_b = xn
            lado = "mitad izquierda"
        else:
            nuevo_a = xn
            nuevo_b = b
            lado = "mitad derecha"

        pasos.append(
            {
                "a": a,
                "b": b,
                "xn": xn,
                "fa": fa,
                "fb": fb,
                "fxn": fxn,
                "error_real": error_real,
                "error_esperado": error_esperado,
                "nuevo_a": nuevo_a,
                "nuevo_b": nuevo_b,
                "lado": lado,
            }
        )

        a = nuevo_a
        b = nuevo_b

    return pasos, raiz_referencia, ancho_inicial


def bisecion_animada():
    pasos, raiz_referencia, ancho_inicial = construir_pasos()
    frames_aparicion = 8
    frames_espera = 25
    frames_zoom = 20
    frames_resumen = 60
    hold_final = 40

    x_min_global = pasos[0]["a"] - 0.6
    x_max_global = pasos[0]["b"] + 0.6
    xs_globales, ys_globales, _, _ = sample_window(x_min_global, x_max_global, n=700)
    _, _, y_global_min, y_global_max = sample_window(x_min_global, x_max_global, n=700)
    y_global_min -= 0.35
    y_global_max += 0.35

    figura, ax = plt.subplots(figsize=(11, 6.5))

    def limite_ventana(x_left, x_right):
        _, _, y_min, y_max = sample_window(x_left, x_right, n=280)
        ancho = x_right - x_left
        margen_x = 0.18 * ancho
        return (x_left - margen_x, x_right + margen_x, y_min, y_max)

    def dibujar_resumen():
        figura.clf()
        ax_funcion, ax_error = figura.subplots(1, 2, figsize=(13, 6))

        xn_final = pasos[-1]["xn"]
        fxn_final = f(xn_final)
        x_teorica = raiz_referencia
        f_teorica = f(x_teorica)

        ax_funcion.plot(xs_globales, ys_globales, color="#1f77b4", linewidth=2.2, label="f(x)")
        ax_funcion.axhline(0, color="black", linewidth=1)
        ax_funcion.axvline(x_teorica, color="#d62728", linestyle="--", linewidth=2, label="raíz teórica")
        ax_funcion.scatter([x_teorica], [f_teorica], color="#d62728", s=85, zorder=6)
        ax_funcion.scatter([xn_final], [fxn_final], color="#2ca02c", s=70, zorder=6, label="aproximación final")
        ax_funcion.annotate(
            f"x* ≈ {x_teorica:.8f}\nf(x*) ≈ {f_teorica:.3e}",
            xy=(x_teorica, f_teorica),
            xytext=(12, 18),
            textcoords="offset points",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#d62728", alpha=0.85),
        )
        ax_funcion.annotate(
            f"xn final ≈ {xn_final:.8f}",
            xy=(xn_final, fxn_final),
            xytext=(12, -26),
            textcoords="offset points",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#2ca02c", alpha=0.85),
        )
        ax_funcion.set_title("Cierre: raíz teórica y aproximación final", fontsize=12)
        ax_funcion.set_xlabel("x")
        ax_funcion.set_ylabel("f(x)")
        ax_funcion.set_xlim(x_min_global, x_max_global)
        ax_funcion.set_ylim(y_global_min, y_global_max)
        ax_funcion.grid(True, alpha=0.22)
        ax_funcion.legend(loc="best")

        iteraciones = [paso["iteracion"] for paso in pasos]
        errores_reales = [paso["error_real"] for paso in pasos]
        errores_esperados = [paso["error_esperado"] for paso in pasos]

        ax_error.plot(iteraciones, errores_esperados, marker="o", color="#1f77b4", linewidth=2.2, label="error esperado")
        ax_error.plot(iteraciones, errores_reales, marker="s", color="#d62728", linewidth=2.2, label="error real")
        ax_error.set_title("Curva de error paso a paso", fontsize=12)
        ax_error.set_xlabel("Iteración")
        ax_error.set_ylabel("Error absoluto")
        ax_error.grid(True, alpha=0.25)
        ax_error.legend(loc="best")
        ax_error.text(
            0.02,
            0.98,
            f"Ancho inicial = {ancho_inicial:.3f}\nError esperado = (ancho inicial)/2^n",
            transform=ax_error.transAxes,
            va="top",
            ha="left",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#999999", alpha=0.9),
        )

        figura.suptitle(
            f"Conclusión: x* ≈ {x_teorica:.8f}  y  f(x*) ≈ {f_teorica:.3e}",
            fontsize=13,
        )
        figura.tight_layout(rect=[0, 0, 1, 0.94])

    def dibujar(ax_obj, paso, progreso_aparicion=1.0, progreso_zoom=0.0, final=False):
        a = paso["a"]
        b = paso["b"]
        xn = paso["xn"]
        nuevo_a = paso["nuevo_a"]
        nuevo_b = paso["nuevo_b"]
        fxn = paso["fxn"]

        p_aparicion = smoothstep(progreso_aparicion)
        p_zoom = smoothstep(progreso_zoom)

        if progreso_zoom > 0.0:
            x_izq = lerp(a, nuevo_a, p_zoom)
            x_der = lerp(b, nuevo_b, p_zoom)
            xlim_ini = limite_ventana(a, b)
            xlim_fin = limite_ventana(nuevo_a, nuevo_b)
            xlim = (
                lerp(xlim_ini[0], xlim_fin[0], p_zoom),
                lerp(xlim_ini[1], xlim_fin[1], p_zoom),
            )
            ylim = (
                lerp(y_global_min, y_global_min, p_zoom),
                lerp(y_global_max, y_global_max, p_zoom),
            )
        else:
            x_izq = a
            x_der = b
            xlim = limite_ventana(a, b)[:2]
            ylim = (y_global_min, y_global_max)

        ax_obj.clear()
        ax_obj.plot(xs_globales, ys_globales, color="#1f77b4", linewidth=2.2, label="f(x)")
        ax_obj.axhline(0, color="black", linewidth=1)

        ax_obj.axvspan(a, xn, color="#bdbdbd", alpha=0.18)
        ax_obj.axvspan(xn, b, color="#bdbdbd", alpha=0.18)
        ax_obj.axvspan(min(nuevo_a, nuevo_b), max(nuevo_a, nuevo_b), color="#2ca02c", alpha=0.10 + 0.20 * p_zoom)

        ax_obj.axvline(x_izq, color="#7f7f7f", linewidth=2, alpha=0.35 + 0.65 * max(p_aparicion, p_zoom))
        ax_obj.axvline(x_der, color="#7f7f7f", linewidth=2, alpha=0.35 + 0.65 * max(p_aparicion, p_zoom))
        ax_obj.axvline(xn, color="#d62728", linestyle="--", linewidth=2, alpha=max(p_aparicion, p_zoom))

        ax_obj.scatter([x_izq, x_der], [f(x_izq), f(x_der)], s=60, color="#9467bd", zorder=5, alpha=0.55 + 0.45 * max(p_aparicion, p_zoom))
        ax_obj.scatter([xn], [fxn], s=20 + 120 * p_aparicion, color="#d62728", zorder=6, alpha=p_aparicion)

        ax_obj.annotate(
            f"a={x_izq:.6f}",
            xy=(x_izq, f(x_izq)),
            xytext=(8, 10),
            textcoords="offset points",
            fontsize=10,
            color="#5a5a5a",
            alpha=0.7 + 0.3 * max(p_aparicion, p_zoom),
        )
        ax_obj.annotate(
            f"b={x_der:.6f}",
            xy=(x_der, f(x_der)),
            xytext=(8, 10),
            textcoords="offset points",
            fontsize=10,
            color="#5a5a5a",
            alpha=0.7 + 0.3 * max(p_aparicion, p_zoom),
        )
        ax_obj.annotate(
            f"xn={xn:.6f}",
            xy=(xn, fxn),
            xytext=(8, -20),
            textcoords="offset points",
            fontsize=10,
            color="#d62728",
            alpha=max(p_aparicion, p_zoom),
        )

        ax_obj.set_xlim(*xlim)
        ax_obj.set_ylim(*ylim)
        ax_obj.grid(True, alpha=0.22)
        ax_obj.set_xlabel("x")
        ax_obj.set_ylabel("f(x)")

        if final:
            titulo = f"Fin de las 10 iteraciones | aproximacion de la raiz: x ≈ {(a + b) / 2:.8f}"
        else:
            decision = "se conserva la mitad izquierda" if paso["nuevo_b"] == xn else "se conserva la mitad derecha"
            if progreso_zoom > 0.0:
                titulo = f"Iteracion {paso['iteracion']}: {decision} | zoom suave hacia [{nuevo_a:.6f}, {nuevo_b:.6f}]"
            else:
                titulo = f"Iteracion {paso['iteracion']}: aparece xn y se espera 1 s antes del zoom"
        ax_obj.set_title(titulo, fontsize=12)

    frames_por_paso = frames_aparicion + frames_espera + frames_zoom
    total_frames = len(pasos) * frames_por_paso + frames_resumen + hold_final

    for indice, paso in enumerate(pasos, start=1):
        paso["iteracion"] = indice

    def actualizar(frame):
        if frame >= len(pasos) * frames_por_paso:
            dibujar_resumen()
            return []

        indice_paso = frame // frames_por_paso
        frame_local = frame % frames_por_paso
        if frame_local < frames_aparicion:
            progreso_aparicion = frame_local / max(1, frames_aparicion - 1)
            dibujar(ax, pasos[indice_paso], progreso_aparicion=progreso_aparicion, progreso_zoom=0.0, final=False)
        elif frame_local < frames_aparicion + frames_espera:
            dibujar(ax, pasos[indice_paso], progreso_aparicion=1.0, progreso_zoom=0.0, final=False)
        else:
            frame_zoom = frame_local - frames_aparicion - frames_espera
            progreso_zoom = frame_zoom / max(1, frames_zoom - 1)
            dibujar(ax, pasos[indice_paso], progreso_aparicion=1.0, progreso_zoom=progreso_zoom, final=False)
        return ax.lines

    animacion = FuncAnimation(
        figura,
        actualizar,
        frames=total_frames,
        interval=40,
        blit=False,
        repeat=False,
    )

    plt.tight_layout()
    plt.show()
    return animacion


if __name__ == "__main__":
    bisecion_animada()