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
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation

import restricciones as r
import BuscadorDeIntervalos as bu
import funciones_bolzano as f
import interfaz

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

        # estado del problema
        self.fn = None
        self.dominio = None
        self.excluido = None
        self.a = self.b = None
        self.n_iter = 0
        self.resultado = None
        self.historial = []
        self._anim = None

        self._build_layout()
        self.root.after(100, self.entry_fn.focus_set)

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
        body.pack(side="top", fill="both", expand=True, padx=14, pady=(0, 14))

        left = tk.Frame(body, bg=RP["base"])
        left.pack(side="left", fill="both", expand=True)

        right = RoundedPanel(body, bg=RP["surface"], width=300)
        right.pack(side="right", fill="y", padx=(14, 0))
        right.pack_propagate(False)
        self._build_reference_panel(right.inner)

        # gráfico (arriba) + controles (abajo, scrolleable)
        self.graph_panel = RoundedPanel(left, bg=RP["surface"])
        self.graph_panel.pack(side="top", fill="both", expand=True, pady=(0, 14))
        self._build_graph(self.graph_panel.inner)

        controls_holder = RoundedPanel(left, bg=RP["surface"], height=270)
        controls_holder.pack(side="bottom", fill="x")
        controls_holder.pack_propagate(False)
        self._build_controls(controls_holder.inner)

    # ------------------------------------------------------------------
    # PANEL DE REFERENCIA (derecha)
    # ------------------------------------------------------------------
    def _build_reference_panel(self, parent):
        parent.configure(bg=RP["surface"])
        tk.Label(parent, text="Sintaxis de funciones", bg=RP["surface"],
                  fg=RP["iris"], font=FONT_B).pack(anchor="w", padx=16, pady=(16, 4))
        tk.Frame(parent, bg=RP["overlay"], height=1).pack(fill="x", padx=16, pady=(0, 6))

        canvas = tk.Canvas(parent, bg=RP["surface"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        table = tk.Frame(canvas, bg=RP["surface"])
        table.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=table, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(16, 0))
        scrollbar.pack(side="right", fill="y")

        for i, (comando, funcion) in enumerate(FUNCIONES_EQUIV.items()):
            bgc = RP["overlay"] if i % 2 == 0 else RP["surface"]
            tk.Label(table, text=comando, bg=bgc, fg=RP["foam"], font=("Consolas", 9),
                      width=13, anchor="w").grid(row=i, column=0, sticky="w", ipady=2)
            tk.Label(table, text=funcion, bg=bgc, fg=RP["text"], font=("Consolas", 9),
                      width=11, anchor="w").grid(row=i, column=1, sticky="w", ipady=2)

        tk.Label(parent, text="Función actual", bg=RP["surface"], fg=RP["iris"],
                  font=FONT_B).pack(anchor="w", padx=16, pady=(10, 2))
        self.lbl_fn_actual = tk.Label(parent, text="—", bg=RP["surface"], fg=RP["text"],
                                       font=("Consolas", 11), wraplength=260, justify="left")
        self.lbl_fn_actual.pack(anchor="w", padx=16, pady=(0, 16))

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
            a_v, b_v = sp.Float(-10, 64), sp.Float(10, 64)
        else:
            a_v, b_v = sp.Float(a, 64), sp.Float(b, 64)

        xs = interfaz.generar_puntos(a_v, b_v, 500)
        xs_f, ys_f = [], []
        for x in xs:
            try:
                y = evaluador(float(x))
                if y == y and abs(y) < 1e6:  # descarta nan / valores enormes (asíntotas)
                    xs_f.append(float(x))
                    ys_f.append(float(y))
                else:
                    xs_f.append(float("nan"))
                    ys_f.append(float("nan"))
            except Exception:
                xs_f.append(float("nan"))
                ys_f.append(float("nan"))

        self.ax.plot(xs_f, ys_f, color=RP["foam"], linewidth=2)
        self.ax.axhline(0, color=RP["highlight-high"], linewidth=1)

        if a is not None and b is not None:
            self.ax.axvline(float(a_v), color=RP["pine"], linewidth=1.5, linestyle="--")
            self.ax.axvline(float(b_v), color=RP["pine"], linewidth=1.5, linestyle="--")
            self.ax.set_xlim(float(a_v) - float(b_v - a_v) * 0.15, float(b_v) + float(b_v - a_v) * 0.15)
        self.canvas.draw()

    # ------------------------------------------------------------------
    # CONTROLES (izquierda, abajo) — se arman por pasos progresivos
    # ------------------------------------------------------------------
    def _build_controls(self, parent):
        parent.configure(bg=RP["surface"])
        nb_bg = RP["surface"]

        # ---- scroll vertical para todos los pasos ----
        canvas = tk.Canvas(parent, bg=nb_bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.steps = tk.Frame(canvas, bg=nb_bg)
        self.steps.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.steps, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=16, pady=12)
        scrollbar.pack(side="right", fill="y")

        self._build_paso1()
        self._build_paso2()
        self._build_paso3()
        self._build_paso4()
        self._build_paso5()

    def _msg(self, parent):
        lbl = tk.Label(parent, text="", bg=RP["surface"], fg=RP["love"], font=FONT,
                        wraplength=700, justify="left")
        return lbl

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
        if f.evaluar(self.fn, self.resultado) == 0:
            texto = f"Raíz exacta: x = {interfaz.formato_numero(self.resultado)}"
        else:
            texto = f"Raíz aproximada: x = {interfaz.formato_numero(self.resultado)}"
        self.lbl_resultado.configure(text=texto)
        self.spin_iter.configure(to=len(self.historial))
        self.frame_paso5.pack(fill="x", pady=(0, 14))

    # ---- PASO 5: iteraciones / animación ----
    def _build_paso5(self):
        self.frame_paso5 = tk.Frame(self.steps, bg=RP["surface"])
        fp = self.frame_paso5
        tk.Label(fp, text="5. Iteraciones", bg=RP["surface"], fg=RP["gold"], font=FONT_B).pack(anchor="w")

        row = tk.Frame(fp, bg=RP["surface"])
        row.pack(anchor="w", pady=6)
        tk.Label(row, text="Ver iteración:", bg=RP["surface"], fg=RP["text"], font=FONT).pack(side="left")
        self.spin_iter = tk.Spinbox(row, from_=1, to=1, width=6, bg=RP["overlay"], fg=RP["text"],
                                     insertbackground=RP["text"], relief="flat", font=FONT)
        self.spin_iter.pack(side="left", padx=6)
        RoundedButton(row, "Confirmar", command=self._on_ver_iteracion, bg=RP["pine"],
                      hover=RP["foam"], fg=RP["base"], width=110).pack(side="left", padx=6)
        RoundedButton(row, "Ver animación", command=self._abrir_animacion, bg=RP["iris"],
                      hover=RP["rose"], fg=RP["base"], width=140).pack(side="left", padx=6)

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
    # ANIMACIÓN (overlay sobre toda la pantalla)
    # ------------------------------------------------------------------
    def _abrir_animacion(self):
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=RP["base"])
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = int(sw * 0.85), int(sh * 0.85)
        win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        bar = tk.Frame(win, bg=RP["base"])
        bar.pack(fill="x")
        tk.Label(bar, text="Animación — método de Bolzano", bg=RP["base"], fg=RP["gold"],
                  font=FONT_B).pack(side="left", padx=14, pady=8)

        def cerrar():
            if self._anim is not None:
                self._anim.event_source.stop()
                self._anim = None
            win.destroy()

        RoundedButton(bar, "✕", command=cerrar, width=34, height=28, bg=RP["love"],
                      hover=RP["rose"], fg=RP["base"]).pack(side="right", padx=12, pady=6)

        content = tk.Frame(win, bg=RP["base"])
        content.pack(fill="both", expand=True)
        loader = tk.Label(content, text="Cargando animación...", bg=RP["base"],
                           fg=RP["subtle"], font=FONT_T)
        loader.place(relx=0.5, rely=0.5, anchor="center")

        # da tiempo a que el Toplevel se pinte antes de construir la animación
        win.after(60, lambda: self._construir_animacion(win, content, loader))

    def _construir_animacion(self, win, content, loader):
        loader.destroy()

        fig = Figure(figsize=(10, 6), dpi=100)
        fig.patch.set_facecolor(RP["base"])
        ax = fig.add_subplot(111)
        self._style_axes(ax)
        canvas = FigureCanvasTkAgg(fig, master=content)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=16, pady=(4, 4))

        controles = tk.Frame(content, bg=RP["base"])
        controles.pack(fill="x", padx=16, pady=(0, 12))

        playing = {"on": True}
        btn_play = RoundedButton(controles, "⏸ Pausar", bg=RP["pine"], hover=RP["foam"],
                                  fg=RP["base"], width=130)
        btn_play.pack(side="left")

        tk.Label(controles, text="Velocidad", bg=RP["base"], fg=RP["text"], font=FONT).pack(
            side="left", padx=(20, 6))
        velocidad = tk.DoubleVar(value=1.0)
        slider = tk.Scale(controles, from_=0.2, to=3.0, resolution=0.1, orient="horizontal",
                           variable=velocidad, bg=RP["base"], fg=RP["text"],
                           troughcolor=RP["overlay"], highlightthickness=0, length=220)
        slider.pack(side="left")

        historial = self.historial
        evaluador = interfaz.crear_evaluador(self.fn)
        base_ms = 900

        def frame_data(i):
            i = min(i, len(historial) - 1)
            return historial[i]

        def actualizar(frame):
            ax.clear()
            self._style_axes(ax)
            a_i, b_i, x_i = frame_data(frame)
            xs = interfaz.generar_puntos(sp.Float(a_i, 64), sp.Float(b_i, 64), 250)
            ys = [evaluador(float(x)) for x in xs]
            ax.plot([float(x) for x in xs], ys, color=RP["foam"], linewidth=2)
            ax.axhline(0, color=RP["highlight-high"], linewidth=1)
            ax.axvline(float(a_i), color=RP["pine"], linewidth=1.5, linestyle="--")
            ax.axvline(float(b_i), color=RP["pine"], linewidth=1.5, linestyle="--")
            ax.scatter([float(x_i)], [float(evaluador(float(x_i)))], s=70, color=RP["love"], zorder=5)
            titulo = f"Iteración {min(frame, len(historial)-1)+1} de {len(historial)}"
            if frame >= len(historial) - 1:
                titulo += f"  —  Raíz ≈ {interfaz.formato_numero(self.resultado)}"
            ax.set_title(titulo, color=RP["gold"])
            return []

        self._anim = FuncAnimation(fig, actualizar, frames=len(historial) + 8,
                                    interval=base_ms / velocidad.get(), repeat=False)
        canvas.draw()

        def toggle_play():
            playing["on"] = not playing["on"]
            if playing["on"]:
                self._anim.event_source.start()
                btn_play.set_text("⏸ Pausar")
            else:
                self._anim.event_source.stop()
                btn_play.set_text("▶ Reanudar")

        btn_play.command = toggle_play

        def cambiar_velocidad(_v=None):
            if self._anim is not None:
                self._anim.event_source.interval = base_ms / velocidad.get()

        slider.configure(command=cambiar_velocidad)


def main():
    root = tk.Tk()
    BolzanoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()