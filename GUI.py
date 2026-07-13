"""
GUI.py — Interfaz gráfica para el método de Bolzano.

Reutiliza toda la lógica ya existente (restricciones, BuscadorDeIntervalos,
funciones_bolzano, interfaz) y sigue el mismo flujo que CLI.py, pero con
widgets. No se modifica ningún otro archivo del proyecto.
"""

import tkinter as tk
from tkinter import ttk
import sympy as sp

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import restricciones as r
import BuscadorDeIntervalos as bu
import funciones_bolzano as f
import interfaz
import numpy as np

RP = interfaz.RP  # paleta Rosé Pine, misma que interfaz.py

# Tabla de equivalencias mostrada en CLI.prints(). Se duplica acá (en vez de
# importar CLI.py) porque CLI.py ejecuta su bucle principal apenas se importa.
FUNCIONES_EQUIV = {
    "x**(1/n)": "ⁿ√x", "e**x": "eˣ", "log(x, n)": "logₙ(x)", "sqrt(x)": "√x",
    "ln(x)": "ln(x)", "sin(x)": "sin(x)", "cos(x)": "cos(x)", "tan(x)": "tan(x)",
    "asin(x)": "asin(x)", "acos(x)": "acos(x)", "atan(x)": "atan(x)",
    "sec(x)": "sec(x)", "csc(x)": "csc(x)", "cot(x)": "cot(x)",
    "sinh(x)": "sinh(x)", "cosh(x)": "cosh(x)", "tanh(x)": "tanh(x)",
    "csch(x)": "csch(x)", "sech(x)": "sech(x)", "coth(x)": "coth(x)",
    "x / y": "x / y", "x * y": "x ⋅ y", "x + y": "x + y", "x - y": "x - y",
    "x ** n": "xⁿ",
}

FONT = ("Segoe UI", 10)
FONT_B = ("Segoe UI", 10, "bold")
FONT_T = ("Segoe UI", 15, "bold")


# ============================================================
# WIDGETS REDONDEADOS
# ============================================================

def _rounded_points(x0, y0, x1, y1, radius):
    r_ = min(radius, (x1 - x0) / 2, (y1 - y0) / 2)
    return [
        x0 + r_, y0, x1 - r_, y0, x1, y0, x1, y0 + r_,
        x1, y1 - r_, x1, y1, x1 - r_, y1, x0 + r_, y1,
        x0, y1, x0, y1 - r_, x0, y0 + r_, x0, y0,
    ]


class RoundedButton(tk.Canvas):
    """Botón con esquinas redondeadas dibujado a mano sobre un Canvas."""

    def __init__(self, master, text, command=None, bg=RP["overlay"],
                 fg=RP["text"], hover=RP["highlight-high"], width=160,
                 height=36, radius=14, font=FONT_B, **kw):
        super().__init__(master, width=width, height=height,
                          bg=master["bg"], highlightthickness=0, **kw)
        self.command = command
        self.bg_color, self.hover_color, self.fg = bg, hover, fg
        self.radius, self.w, self.h = radius, width, height
        self.enabled = True
        self._draw(bg)
        self.text_id = self.create_text(width / 2, height / 2, text=text,
                                         fill=fg, font=font)
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", lambda e: self._draw(self.hover_color) if self.enabled else None)
        self.bind("<Leave>", lambda e: self._draw(self.bg_color) if self.enabled else None)

    def _draw(self, color):
        self.delete("bg")
        pts = _rounded_points(2, 2, self.w - 2, self.h - 2, self.radius)
        self.create_polygon(pts, smooth=True, fill=color, outline=color, tags="bg")
        self.tag_lower("bg")

    def _click(self, _e):
        if self.enabled and self.command:
            self.command()

    def set_text(self, text):
        self.itemconfigure(self.text_id, text=text)

    def set_enabled(self, enabled):
        self.enabled = enabled
        self._draw(self.bg_color if enabled else RP["highlight-low"])
        self.itemconfigure(self.text_id, fill=self.fg if enabled else RP["muted"])


class RoundedPanel(tk.Frame):
    """Frame con fondo redondeado dibujado en un Canvas de fondo."""

    def __init__(self, master, bg=RP["surface"], radius=16, **kw):
        outer_bg = master["bg"] if isinstance(master, (tk.Frame, tk.Tk)) else RP["base"]
        super().__init__(master, bg=outer_bg, **kw)
        self._bgcanvas = tk.Canvas(self, bg=outer_bg, highlightthickness=0)
        self._bgcanvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.inner = tk.Frame(self, bg=bg)
        self.inner.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._color = bg
        self.bind("<Configure>", self._redraw)

    def _redraw(self, _e=None):
        self._bgcanvas.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w > 4 and h > 4:
            pts = _rounded_points(1, 1, w - 1, h - 1, 18)
            self._bgcanvas.create_polygon(pts, smooth=True, fill=self._color,
                                           outline=self._color)


# ============================================================
# APLICACIÓN PRINCIPAL
# ============================================================

class BolzanoApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Bolzano")
        self.root.configure(bg=RP["base"])
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self._configurar_widgets_ttk()

        # estado del problema
        self.fn = None
        self.dominio = None
        self.excluido = None
        self.a = self.b = None
        self.n_iter = 0
        self.resultado = None
        self.historial = []
        self._scroll_canvases = []
        # El binding global recibe la rueda incluso cuando el cursor está
        # sobre un Entry, Button u otro hijo dentro de un contenedor scrolleable.
        self.root.bind_all("<MouseWheel>", self._scroll_con_rueda, add="+")

        self._build_layout()
        self.root.after(100, self.entry_fn.focus_set)

    def _configurar_widgets_ttk(self):
        """Aplica la paleta a los controles nativos que tienen flechas."""
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Dark.Vertical.TScrollbar",
            background=RP["overlay"], troughcolor=RP["base"],
            bordercolor=RP["surface"], arrowcolor=RP["text"], width=14
        )
        style.map(
            "Dark.Vertical.TScrollbar",
            background=[("active", RP["highlight-high"]), ("pressed", RP["iris"])]
        )
        style.configure(
            "Dark.TSpinbox",
            fieldbackground=RP["overlay"], background=RP["overlay"],
            foreground=RP["text"], arrowcolor=RP["foam"],
            bordercolor=RP["surface"], lightcolor=RP["overlay"], darkcolor=RP["overlay"]
        )
        style.map(
            "Dark.TSpinbox",
            background=[("active", RP["highlight-high"]), ("disabled", RP["highlight-low"])]
        )

    # ------------------------------------------------------------------
    # LAYOUT GENERAL
    # ------------------------------------------------------------------
    def _build_layout(self):
        titlebar = tk.Frame(self.root, bg=RP["base"], height=40)
        titlebar.pack(side="top", fill="x")
        tk.Label(titlebar, text="Método de Bolzano", bg=RP["base"],
                  fg=RP["gold"], font=FONT_T).pack(side="left", padx=18, pady=4)
        RoundedButton(titlebar, "✕", command=self.root.destroy, width=36, height=30,
                      bg=RP["love"], hover=RP["rose"], fg=RP["base"]).pack(side="right", padx=14, pady=5)

        body = tk.Frame(self.root, bg=RP["base"])
        body.pack(side="top", fill="both", expand=True, padx=20, pady=(0, 20))
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=3)  # gráfico + controles
        body.columnconfigure(1, weight=1)  # sintaxis: ocupa el espacio sobrante

        left = tk.Frame(body, bg=RP["base"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        left.rowconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        right = RoundedPanel(body, bg=RP["surface"])
        right.grid(row=0, column=1, sticky="nsew")
        self._build_reference_panel(right.inner)

        # gráfico (arriba, 50%) + controles (abajo, 50%, scrolleable)
        self.graph_panel = RoundedPanel(left, bg=RP["surface"])
        self.graph_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 7))
        self._build_graph(self.graph_panel.inner)

        controls_holder = RoundedPanel(left, bg=RP["surface"])
        controls_holder.grid(row=1, column=0, sticky="nsew", pady=(7, 0))
        self._build_controls(controls_holder.inner)

    # ------------------------------------------------------------------
    # PANEL DE REFERENCIA (derecha)
    # ------------------------------------------------------------------
    def _build_reference_panel(self, parent):
        parent.configure(bg=RP["surface"])

        # El pie ("Función actual") se packea primero con side="bottom" para
        # reservar su lugar; así el canvas de la tabla puede después ocupar
        # con expand=True TODO el resto del contenedor sin quedarse sin
        # espacio (si se packea al final, como widget "top" tardío, Tk ya
        # le habría dado todo el resto de la cavidad al canvas y este
        # quedaría sin lugar).
        pie = tk.Frame(parent, bg=RP["surface"])
        pie.pack(side="bottom", fill="x")
        tk.Frame(pie, bg=RP["overlay"], height=1).pack(fill="x", padx=16, pady=(6, 8))
        tk.Label(pie, text="Función actual", bg=RP["surface"], fg=RP["iris"],
                  font=FONT_B).pack(anchor="w", padx=16)
        self.lbl_fn_actual = tk.Label(pie, text="—", bg=RP["surface"], fg=RP["text"],
                                       font=("Consolas", 11), wraplength=320, justify="left")
        self.lbl_fn_actual.pack(anchor="w", padx=16, pady=(2, 16))

        tk.Label(parent, text="Sintaxis de funciones", bg=RP["surface"],
                  fg=RP["iris"], font=FONT_B).pack(anchor="w", padx=16, pady=(16, 4))
        tk.Frame(parent, bg=RP["overlay"], height=1).pack(fill="x", padx=16, pady=(0, 6))

        canvas = tk.Canvas(parent, bg=RP["surface"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview,
                                  style="Dark.Vertical.TScrollbar")
        table = tk.Frame(canvas, bg=RP["surface"])
        table.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=table, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(canvas_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(16, 0))
        scrollbar.pack(side="right", fill="y")

        self._activar_scroll_mouse(table, canvas)

        table.columnconfigure(0, weight=1)
        table.columnconfigure(1, weight=1)
        for i, (comando, funcion) in enumerate(FUNCIONES_EQUIV.items()):
            bgc = RP["overlay"] if i % 2 == 0 else RP["surface"]
            tk.Label(table, text=comando, bg=bgc, fg=RP["foam"], font=("Consolas", 9),
                      anchor="w").grid(row=i, column=0, sticky="ew", ipady=3)
            tk.Label(table, text=funcion, bg=bgc, fg=RP["text"], font=("Consolas", 9),
                      anchor="w").grid(row=i, column=1, sticky="ew", ipady=3)

    # ------------------------------------------------------------------
    # GRÁFICO
    # ------------------------------------------------------------------
    def _build_graph(self, parent):
        parent.configure(bg=RP["surface"])
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.fig.patch.set_facecolor(RP["surface"])
        self.ax = self.fig.add_subplot(111)
        self._style_axes(self.ax)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().configure(bg=RP["surface"], highlightthickness=0)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)

    def _style_axes(self, ax):
        ax.set_facecolor(RP["surface"])
        ax.tick_params(colors=RP["subtle"])
        for spine in ax.spines.values():
            spine.set_color(RP["overlay"])
        ax.grid(True, color=RP["overlay"], alpha=0.5)

    def _plot_funcion(self, a=None, b=None):
        """Dibuja la función. Si se pasan a,b, acota la vista a ese intervalo."""
        self.ax.clear()
        self._style_axes(self.ax)
        evaluador = interfaz.crear_evaluador(self.fn)

        if a is None or b is None:
            # usar el dominio calculado previamente
            extremos = self.dominio

            try:
                intervalo = list(extremos.args) if hasattr(extremos, "args") else [extremos]

                a_v = min(float(i.start) for i in intervalo if hasattr(i, "start"))
                b_v = max(float(i.end) for i in intervalo if hasattr(i, "end"))

                a_v, b_v = sp.Float(a_v, 64), sp.Float(b_v, 64)

            except Exception:
                a_v, b_v = sp.Float(-10, 64), sp.Float(10, 64)

        else:
            a_v, b_v = sp.Float(a, 64), sp.Float(b, 64) 

        xs = interfaz.generar_puntos(a_v, b_v, 500)
        xs_f, ys_f = [], []
        for x in xs:
            try:
                y = evaluador(float(x))

                if y is None:
                    raise ValueError

                y = float(y)

                if np.isfinite(y) and abs(y) < 1e6:
                    xs_f.append(float(x))
                    ys_f.append(y)
                else:
                    xs_f.append(np.nan)
                    ys_f.append(np.nan)
            except Exception:
                xs_f.append(float("nan"))
                ys_f.append(float("nan"))

        self.ax.plot(xs_f, ys_f, color=RP["foam"], linewidth=2)
        self.ax.axhline(0, color=RP["highlight-high"], linewidth=1)

        if a is not None and b is not None:
            self.ax.axvline(float(a_v), color=RP["pine"], linewidth=1.5, linestyle="--")
            self.ax.axvline(float(b_v), color=RP["pine"], linewidth=1.5, linestyle="--")
            margen = abs(float(b_v - a_v)) * 0.15

            self.ax.set_xlim(
                float(min(a_v, b_v)) - margen,
                float(max(a_v, b_v)) + margen
            )
        self.canvas.draw()

    # ------------------------------------------------------------------
    # CONTROLES (izquierda, abajo) — se arman por pasos progresivos
    # ------------------------------------------------------------------
    def _build_controls(self, parent):
        parent.configure(bg=RP["surface"])
        nb_bg = RP["surface"]

        # ---- scroll vertical para todos los pasos ----
        canvas = tk.Canvas(parent, bg=nb_bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview,
                                  style="Dark.Vertical.TScrollbar")
        self.steps = tk.Frame(canvas, bg=nb_bg)
        self.steps.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.steps, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=16, pady=12)
        scrollbar.pack(side="right", fill="y")

        self._activar_scroll_mouse(self.steps, canvas)

        self._build_paso1()
        self._build_paso2()
        self._build_paso3()
        self._build_paso4()
        self._build_paso5()

    def _msg(self, parent):
        lbl = tk.Label(parent, text="", bg=RP["surface"], fg=RP["love"], font=FONT,
                        wraplength=700, justify="left")
        return lbl

    def _activar_scroll_mouse(self, _widget, canvas):
        """Registra un canvas para scroll aunque el cursor esté sobre sus hijos."""
        self._scroll_canvases.append(canvas)

    def _scroll_con_rueda(self, event):
        widget = event.widget
        while widget is not None:
            if widget in self._scroll_canvases:
                pasos = int(-event.delta / 120)
                if pasos:
                    widget.yview_scroll(pasos, "units")
                return "break"
            widget = getattr(widget, "master", None)

    # ---- PASO 1: función y dominio ----
    def _build_paso1(self):
        f1 = tk.Frame(self.steps, bg=RP["surface"])
        f1.pack(fill="x", pady=(0, 14))

        tk.Label(f1, text="1. Función", bg=RP["surface"], fg=RP["gold"], font=FONT_B).pack(anchor="w")
        row = tk.Frame(f1, bg=RP["surface"])
        row.pack(fill="x", pady=6)
        self.entry_fn = tk.Entry(row, bg=RP["overlay"], fg=RP["text"], insertbackground=RP["text"],
                                  relief="flat", font=("Consolas", 11))
        self.entry_fn.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))
        self.entry_fn.bind("<Button-1>", lambda e: self.entry_fn.focus_set())
        RoundedButton(row, "Calcular dominio", command=self._on_calcular_dominio,
                      bg=RP["pine"], hover=RP["foam"], fg=RP["base"], width=170).pack(side="left")

        self.lbl_dominio = tk.Label(f1, text="", bg=RP["surface"], fg=RP["foam"],
                                     font=("Consolas", 10), wraplength=760, justify="left")
        self.lbl_dominio.pack(anchor="w", pady=(6, 0))
        self.msg1 = self._msg(f1)
        self.msg1.pack(anchor="w")

    def _on_calcular_dominio(self):
        self.msg1.configure(text="")
        texto = self.entry_fn.get().strip()
        if not texto:
            self.msg1.configure(text="Ingrese una función.")
            return
        try:
            self.fn = r.preparar_funcion(texto)
        except Exception:
            self.msg1.configure(text="Función inválida. Utilice la sintaxis indicada.")
            return

        self.dominio = r.CalcularDominio(self.fn)
        self.excluido = bu._excluido_de(self.dominio)
        self.lbl_dominio.configure(text=r.formatear_dominio(self.dominio))
        self.lbl_fn_actual.configure(text=str(self.fn))
        self._plot_funcion()
        self._reset_desde_paso2()
        self.frame_paso2.pack(fill="x", pady=(0, 14))

    def _reset_desde_paso2(self):
        for fr in (getattr(self, "frame_paso2", None), getattr(self, "frame_paso3", None),
                   getattr(self, "frame_paso4", None), getattr(self, "frame_paso5", None)):
            if fr is not None:
                fr.pack_forget()
        self.a = self.b = None
        self.resultado = None
        self.historial = []

    # ---- PASO 2: intervalo ----
    def _build_paso2(self):
        self.frame_paso2 = tk.Frame(self.steps, bg=RP["surface"])
        fp = self.frame_paso2

        tk.Label(fp, text="2. Intervalo de búsqueda de raíces", bg=RP["surface"],
                  fg=RP["gold"], font=FONT_B).pack(anchor="w")

        self.modo_intervalo = tk.StringVar(value="auto")
        row = tk.Frame(fp, bg=RP["surface"])
        row.pack(anchor="w", pady=6)
        for txt, val in (("Buscar automáticamente", "auto"), ("Ingresar manualmente", "manual")):
            tk.Radiobutton(row, text=txt, variable=self.modo_intervalo, value=val,
                            command=self._on_modo_intervalo, bg=RP["surface"], fg=RP["text"],
                            selectcolor=RP["overlay"], activebackground=RP["surface"],
                            activeforeground=RP["text"], font=FONT).pack(side="left", padx=(0, 16))

        self.frame_auto = tk.Frame(fp, bg=RP["surface"])
        RoundedButton(self.frame_auto, "Buscar intervalos", command=self._on_buscar_auto,
                      bg=RP["iris"], hover=RP["rose"], fg=RP["base"], width=170).pack(anchor="w")
        self.listbox_intervalos = tk.Listbox(self.frame_auto, bg=RP["overlay"], fg=RP["text"],
                                              selectbackground=RP["pine"], relief="flat",
                                              font=("Consolas", 10), height=5)
        self.listbox_intervalos.pack(fill="x", pady=6)
        RoundedButton(self.frame_auto, "Confirmar selección", command=self._on_confirmar_auto,
                      bg=RP["pine"], hover=RP["foam"], fg=RP["base"], width=170).pack(anchor="w")

        self.frame_manual = tk.Frame(fp, bg=RP["surface"])
        row2 = tk.Frame(self.frame_manual, bg=RP["surface"])
        row2.pack(anchor="w", pady=4)
        tk.Label(row2, text="a =", bg=RP["surface"], fg=RP["text"], font=FONT).pack(side="left")
        self.entry_a = tk.Entry(row2, width=12, bg=RP["overlay"], fg=RP["text"],
                                 insertbackground=RP["text"], relief="flat", font=FONT)
        self.entry_a.pack(side="left", padx=6, ipady=4)
        tk.Label(row2, text="b =", bg=RP["surface"], fg=RP["text"], font=FONT).pack(side="left")
        self.entry_b = tk.Entry(row2, width=12, bg=RP["overlay"], fg=RP["text"],
                                 insertbackground=RP["text"], relief="flat", font=FONT)
        self.entry_b.pack(side="left", padx=6, ipady=4)
        RoundedButton(row2, "Validar intervalo", command=self._on_validar_manual,
                      bg=RP["pine"], hover=RP["foam"], fg=RP["base"], width=150).pack(side="left", padx=6)

        self.msg2 = self._msg(fp)
        self.msg2.pack(anchor="w", pady=(4, 0))
        self._on_modo_intervalo()

    def _on_modo_intervalo(self):
        self.frame_auto.pack_forget()
        self.frame_manual.pack_forget()
        if self.modo_intervalo.get() == "auto":
            self.frame_auto.pack(fill="x", pady=4)
        else:
            self.frame_manual.pack(fill="x", pady=4)

    def _on_buscar_auto(self):
        self.msg2.configure(text="")
        self.listbox_intervalos.delete(0, "end")
        self._intervalos_encontrados = bu.BuscarIntervalosRaiz(self.fn, self.dominio)
        if not self._intervalos_encontrados:
            self.msg2.configure(text="No se encontraron intervalos candidatos.")
            return
        for i, item in enumerate(self._intervalos_encontrados):
            if item is None:
                texto = f"{i+1}) No se halló posible raíz."
            elif isinstance(item, tuple):
                texto = f"{i+1}) Subintervalo: [{round(float(item[0]),6)}, {round(float(item[1]),6)}]"
            else:
                texto = f"{i+1}) Raíz exacta: x = {round(float(item),6)}"
            self.listbox_intervalos.insert("end", texto)

    def _on_confirmar_auto(self):
        self.msg2.configure(text="")
        sel = self.listbox_intervalos.curselection()
        if not sel:
            self.msg2.configure(text="Seleccione un intervalo de la lista.")
            return
        item = self._intervalos_encontrados[sel[0]]
        if item is None:
            self.msg2.configure(text="Ese subintervalo no tiene raíz detectable. Elija otro.")
            return
        if not isinstance(item, tuple):
            self.msg2.configure(
                text=f"Se halló raíz exacta: x = {round(float(item),6)}. "
                     f"No se requieren iteraciones.", fg=RP["gold"])
            self.a = self.b = None
            return
        a, b = (sp.Float(x, 64) for x in item)
        self._fijar_intervalo(a, b)

    def _on_validar_manual(self):
        self.msg2.configure(text="", fg=RP["love"])
        try:
            a = sp.Float(self.entry_a.get(), 64)
            b = sp.Float(self.entry_b.get(), 64)
        except Exception:
            self.msg2.configure(text="Debe ingresar números válidos.")
            return
        if not r.intervalo_en_dominio(self.dominio, a, b):
            self.msg2.configure(text="El intervalo no pertenece al dominio.")
            return
        self._fijar_intervalo(a, b)

    def _fijar_intervalo(self, a, b):
        try:
            valido = bu.evaluar(self.fn, a) * bu.evaluar(self.fn, b) < 0
        except Exception:
            valido = False
        if not valido:
            self.msg2.configure(text="El intervalo no es válido para Bolzano: debe cumplirse f(a)·f(b) < 0.")
            return
        self.a, self.b = a, b
        self.msg2.configure(text=f"Intervalo válido: [{round(float(a),6)}, {round(float(b),6)}]", fg=RP["foam"])
        self._plot_funcion(a, b)
        self.frame_paso3.pack(fill="x", pady=(0, 14))
        self.frame_paso4.pack_forget()
        self.frame_paso5.pack_forget()

    # ---- PASO 3: tolerancia / iteraciones ----
    def _build_paso3(self):
        self.frame_paso3 = tk.Frame(self.steps, bg=RP["surface"])
        fp = self.frame_paso3

        tk.Label(fp, text="3. Criterio de parada", bg=RP["surface"], fg=RP["gold"],
                  font=FONT_B).pack(anchor="w")

        self.modo_criterio = tk.StringVar(value="tol")
        row = tk.Frame(fp, bg=RP["surface"])
        row.pack(anchor="w", pady=6)
        for txt, val in (("Tolerancia", "tol"), ("Cantidad de iteraciones", "iter")):
            tk.Radiobutton(row, text=txt, variable=self.modo_criterio, value=val, bg=RP["surface"],
                            fg=RP["text"], selectcolor=RP["overlay"], activebackground=RP["surface"],
                            activeforeground=RP["text"], font=FONT).pack(side="left", padx=(0, 16))
        self.entry_criterio = tk.Entry(row, width=14, bg=RP["overlay"], fg=RP["text"],
                                        insertbackground=RP["text"], relief="flat", font=FONT)
        self.entry_criterio.pack(side="left", padx=6, ipady=4)
        RoundedButton(row, "Confirmar", command=self._on_confirmar_criterio, bg=RP["pine"],
                      hover=RP["foam"], fg=RP["base"], width=120).pack(side="left")

        self.msg3 = self._msg(fp)
        self.msg3.pack(anchor="w", pady=(4, 0))

    def _on_confirmar_criterio(self):
        self.msg3.configure(text="", fg=RP["love"])
        try:
            if self.modo_criterio.get() == "tol":
                tol = sp.Float(self.entry_criterio.get(), 64)
                if tol <= 0:
                    raise ValueError
                self.n_iter = f.cantidad_iteraciones(self.a, self.b, tol)
                self.msg3.configure(text=f"Se realizarán {self.n_iter} iteraciones.", fg=RP["foam"])
            else:
                n = int(self.entry_criterio.get())
                if n <= 0:
                    raise ValueError
                self.n_iter = n
                self.msg3.configure(text=f"Se realizarán {n} iteraciones.", fg=RP["foam"])
        except ValueError:
            self.msg3.configure(text="Debe ingresar un número válido y positivo.")
            return
        self.frame_paso4.pack(fill="x", pady=(0, 14))
        self.frame_paso5.pack_forget()

    # ---- PASO 4: calcular raíz ----
    def _build_paso4(self):
        self.frame_paso4 = tk.Frame(self.steps, bg=RP["surface"])
        fp = self.frame_paso4
        tk.Label(fp, text="4. Cálculo", bg=RP["surface"], fg=RP["gold"], font=FONT_B).pack(anchor="w")
        RoundedButton(fp, "Calcular raíz aproximada", command=self._on_calcular_raiz,
                      bg=RP["love"], hover=RP["rose"], fg=RP["base"], width=220).pack(anchor="w", pady=6)
        self.lbl_resultado = tk.Label(fp, text="", bg=RP["surface"], fg=RP["gold"],
                                       font=FONT_B, justify="left")
        self.lbl_resultado.pack(anchor="w")

    def _on_calcular_raiz(self):
        self.resultado, self.historial = f.iterar(self.fn, self.a, self.b, self.n_iter)
        realizadas = len(self.historial)
        if f.evaluar(self.fn, self.resultado) == 0:
            texto = f"Raíz exacta: x = {interfaz.formato_numero(self.resultado)}\n"
            if realizadas < self.n_iter:
                texto += (f"Se alcanzó la raíz exacta antes de lo previsto: "
                          f"se realizaron {realizadas} de {self.n_iter} iteraciones solicitadas.")
            else:
                texto += f"Se realizaron {realizadas} iteraciones."
        else:
            texto = (f"Raíz aproximada: x = {interfaz.formato_numero(self.resultado)}\n"
                      f"Se realizaron {realizadas} iteraciones.")
        self.lbl_resultado.configure(text=texto)
        self.spin_iter.configure(to=realizadas)
        try:
            if int(self.spin_iter.get()) > realizadas:
                self.spin_iter.delete(0, "end")
                self.spin_iter.insert(0, "1")
        except ValueError:
            self.spin_iter.delete(0, "end")
            self.spin_iter.insert(0, "1")
        self.frame_paso5.pack(fill="x", pady=(0, 14))

    # ---- PASO 5: iteraciones / animación ----
    def _build_paso5(self):
        self.frame_paso5 = tk.Frame(self.steps, bg=RP["surface"])
        fp = self.frame_paso5
        tk.Label(fp, text="5. Iteraciones", bg=RP["surface"], fg=RP["gold"], font=FONT_B).pack(anchor="w")

        row = tk.Frame(fp, bg=RP["surface"])
        row.pack(anchor="w", pady=6)
        tk.Label(row, text="Ver iteración:", bg=RP["surface"], fg=RP["text"], font=FONT).pack(side="left")
        self.spin_iter = ttk.Spinbox(row, from_=1, to=1, width=6, style="Dark.TSpinbox", font=FONT)
        self.spin_iter.pack(side="left", padx=6)
        RoundedButton(row, "Confirmar", command=self._on_ver_iteracion, bg=RP["pine"],
                      hover=RP["foam"], fg=RP["base"], width=110).pack(side="left", padx=6)
        btn_anim = RoundedButton(row, "Ver animación", command=None, bg=RP["iris"],
                      hover=RP["rose"], fg=RP["base"], width=140)
        btn_anim.command = lambda: self._abrir_animacion(btn_anim)
        btn_anim.pack(side="left", padx=6)

        self.lbl_iteracion = tk.Label(fp, text="", bg=RP["surface"], fg=RP["text"],
                                       font=("Consolas", 10), justify="left")
        self.lbl_iteracion.pack(anchor="w", pady=(2, 8))

        RoundedButton(fp, "Mostrar todas las iteraciones", command=self._mostrar_todas,
                      bg=RP["overlay"], hover=RP["highlight-high"], fg=RP["text"],
                      width=230).pack(anchor="w")

    def _on_ver_iteracion(self):
        try:
            i = int(self.spin_iter.get()) - 1
            a_i, b_i, x_i = self.historial[i]
        except (ValueError, IndexError):
            self.lbl_iteracion.configure(text="Número de iteración inválido.", fg=RP["love"])
            return
        self.lbl_iteracion.configure(
            fg=RP["text"],
            text=(f"Iteración {i+1}\n"
                  f"Intervalo: [{interfaz.formato_numero(a_i)}, {interfaz.formato_numero(b_i)}]\n"
                  f"x = {interfaz.formato_numero(x_i)}\n"
                  f"f(x) = {interfaz.formato_numero(f.evaluar(self.fn, x_i))}"))

    def _mostrar_todas(self):
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.configure(bg=RP["surface"])
        w, h = 640, 520
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        bar = tk.Frame(win, bg=RP["surface"])
        bar.pack(fill="x")
        tk.Label(bar, text="Historial completo", bg=RP["surface"], fg=RP["gold"],
                  font=FONT_B).pack(side="left", padx=12, pady=8)
        RoundedButton(bar, "✕", command=win.destroy, width=32, height=28, bg=RP["love"],
                      hover=RP["rose"], fg=RP["base"]).pack(side="right", padx=10, pady=6)

        text = tk.Text(win, bg=RP["overlay"], fg=RP["text"], insertbackground=RP["text"],
                        relief="flat", font=("Consolas", 10), wrap="word")
        text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        for i, (a_i, b_i, x_i) in enumerate(self.historial, start=1):
            text.insert("end",
                f"Iteración {i}\n"
                f"Intervalo: [{interfaz.formato_numero(a_i)}, {interfaz.formato_numero(b_i)}]\n"
                f"x = {interfaz.formato_numero(x_i)}\n"
                f"f(x) = {interfaz.formato_numero(f.evaluar(self.fn, x_i))}\n\n")
        text.configure(state="disabled")

    # ------------------------------------------------------------------
    # ANIMACIÓN — el mismo sistema que usa CLI.py (interfaz.mostrar_bolzano),
    # con controles propios (velocidad, play/pausa, reiniciar, cerrar)
    # agregados sobre su propia ventana.
    # ------------------------------------------------------------------
    def _abrir_animacion(self, boton):
        boton.set_enabled(False)
        boton.set_text("Generando...")
        self.root.update_idletasks()
        self._lanzar_animacion(boton)

    def _lanzar_animacion(self, boton):
        antes = set(plt.get_fignums())

        # interfaz.mostrar_bolzano llama a plt.show() de forma bloqueante
        # (como en CLI.py). Acá se necesita que NO bloquee para poder
        # agregarle los controles propios a la ventana mientras sigue
        # abierta, así que se parchea show() temporalmente (sin tocar
        # interfaz.py) para que no espere a que se cierre la figura.
        show_original = plt.show
        plt.show = lambda *a, **k: show_original(block=False)
        try:
            anim = interfaz.mostrar_bolzano(self.fn, self.historial, self.resultado)

            if anim is not None and anim.event_source is not None:
                # La animación de matplotlib se creó para la versión CLI. En
                # esta ventana el avance se controla abajo con after(), por lo
                # que debe quedar detenida desde el primer instante.
                anim.event_source.stop()
        finally:
            plt.show = show_original

        nuevas = set(plt.get_fignums()) - antes
        fig = plt.figure(nuevas.pop()) if nuevas else plt.gcf()
        manager = fig.canvas.manager
        window = manager.window

        if anim is not None:
            # FuncAnimation queda suscripta al primer evento de dibujo y en
            # ese callback vuelve a iniciar su temporizador. Desconectarlo es
            # imprescindible para que no avance sola al abrir la ventana.
            first_draw_id = getattr(anim, "_first_draw_id", None)
            if first_draw_id is not None:
                fig.canvas.mpl_disconnect(first_draw_id)
                anim._first_draw_id = None
            if anim.event_source is not None:
                anim.event_source.stop()

        # fullscreen sin marco, gestionado por el WM (mismo criterio que la
        # ventana principal: overrideredirect no recibe foco en X11).
        window.attributes("-fullscreen", True)
        window.configure(bg=RP["base"])

        # se oculta la toolbar de matplotlib por defecto; usamos la nuestra
        if getattr(manager, "toolbar", None) is not None:
            manager.toolbar.pack_forget()

        reproduccion = {"activa": False, "frame": 0, "after_id": None}

        barra = tk.Frame(window, bg=RP["base"])
        barra.pack(side="bottom", fill="x")

        def cerrar():
            if reproduccion["after_id"] is not None:
                window.after_cancel(reproduccion["after_id"])
                reproduccion["after_id"] = None
            if anim is not None and anim.event_source is not None:
                anim.event_source.stop()
            plt.close(fig)  # ya destruye la ventana (async, vía manager.destroy() interno)
            boton.set_text("Ver animación")
            boton.set_enabled(True)

        def reiniciar():
            if anim is not None and anim.event_source is not None:
                anim.event_source.stop()
            if anim is not None:
                detener_reproduccion()
                habilitar_slider()
            reproduccion["frame"] = 0

            if anim is not None:
                # No se eliminan artistas: actualizar() conserva referencias
                # a ellos. Sólo se los oculta antes de volver al primer frame.
                ax = fig.axes[0]
                for artista in list(ax.lines[1:]) + list(ax.patches) + list(ax.texts):
                    artista.set_visible(False)
                anim._draw_next_frame(0, blit=False)
                fig.canvas.draw_idle()

        if anim is not None:
            btn_play = RoundedButton(barra, "▶ Reproducir", bg=RP["pine"], hover=RP["foam"],
                                      fg=RP["base"], width=130)
            btn_play.pack(side="left", padx=(14, 6), pady=10)

            tk.Label(barra, text="Velocidad", bg=RP["base"], fg=RP["text"], font=FONT).pack(
                side="left", padx=(20, 6))
            velocidad = tk.DoubleVar(value=interfaz.s)
            iteraciones_animadas = min(
                interfaz.MAX_ITER_MOSTRADAS, max(len(self.historial) - 1, 0)
            )

            def frames_totales_actuales():
                frames_por_fase = max(1, int(interfaz.s * 120))
                return (
                    iteraciones_animadas * frames_por_fase * 4
                    + frames_por_fase
                    + 60
                    + 1
                )

            def cambiar_velocidad(valor):
                interfaz.s = float(valor)

            def habilitar_slider():
                slider.configure(
                    state="normal", bg=RP["base"], fg=RP["text"],
                    troughcolor=RP["overlay"]
                )

            def bloquear_slider():
                slider.configure(
                    state="disabled", bg=RP["highlight-low"], fg=RP["muted"],
                    troughcolor=RP["highlight-low"]
                )

            def detener_reproduccion():
                reproduccion["activa"] = False
                if reproduccion["after_id"] is not None:
                    window.after_cancel(reproduccion["after_id"])
                    reproduccion["after_id"] = None
                btn_play.set_text("▶ Reproducir")

            def avanzar():
                reproduccion["after_id"] = None
                if not reproduccion["activa"]:
                    return

                if reproduccion["frame"] >= frames_totales_actuales():
                    detener_reproduccion()
                    return

                anim._draw_next_frame(reproduccion["frame"], blit=False)
                reproduccion["frame"] += 1
                reproduccion["after_id"] = window.after(
                    round(1000 / 120), avanzar
                )

            def toggle_play():
                if reproduccion["activa"]:
                    detener_reproduccion()
                    return

                # Si ya llegó al final, Play vuelve a iniciar desde el primer
                # cuadro, aun si antes no se había pulsado Pausa.
                if reproduccion["frame"] >= frames_totales_actuales():
                    reiniciar()
                bloquear_slider()
                reproduccion["activa"] = True
                btn_play.set_text("⏸ Pausar")
                reproduccion["after_id"] = window.after(0, avanzar)

            btn_play.command = toggle_play

            slider = tk.Scale(barra, from_=0, to=1.0, resolution=0.01, orient="horizontal",
                               variable=velocidad, command=cambiar_velocidad, bg=RP["base"],
                               fg=RP["text"], troughcolor=RP["overlay"], highlightthickness=0,
                               length=240)
            slider.pack(side="left", pady=10)

            tk.Label(barra, text="(duración de cada fase)", bg=RP["base"], fg=RP["muted"],
                      font=("Segoe UI", 8)).pack(side="left", padx=(6, 0))

            # Mostrar el estado inicial sin consumir el primer frame: la
            # reproducción comienza sólo al pulsar Play.
            reiniciar()
        else:
            tk.Label(barra, text="Raíz exacta: no hay animación para reproducir.",
                      bg=RP["base"], fg=RP["subtle"], font=FONT).pack(side="left", padx=14, pady=10)

        RoundedButton(barra, "⟲ Reiniciar", command=reiniciar, bg=RP["iris"], hover=RP["rose"],
                      fg=RP["base"], width=130).pack(side="left", padx=6, pady=10)
        RoundedButton(barra, "✕ Cerrar", command=cerrar, bg=RP["love"], hover=RP["rose"],
                      fg=RP["base"], width=120).pack(side="right", padx=14, pady=10)

        window.protocol("WM_DELETE_WINDOW", cerrar)


def main():
    root = tk.Tk()
    BolzanoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
