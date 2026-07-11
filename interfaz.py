import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Rectangle, Arc
import numpy as np
import sympy as sp
s=0.3 #animation speed minimo 0.02
MAX_ITER_MOSTRADAS = 23
# ------------------------------------------------------------------
# FIX (solo visual): el eje X ahora es RELATIVO al centro del intervalo
# en vez de absoluto. Motivo: cuando el intervalo se hace mucho más chico
# que la magnitud de a/b (~1e-16 veces más chico), float64 ya no puede
# distinguir a de b como números distintos -> el eje colapsa -> diente de
# sierra. Números CHICOS centrados en cero sí se representan con toda la
# precisión de float64, por eso se resta el centro ANTES de castear a
# float (en limite_x y en actualizar_funcion). El eje Y no lo toco: los
# valores de f(x) ya son chicos cerca de la raíz, no sufren el problema.
# ------------------------------------------------------------------

def limite_x(a, b):
    a = sp.sympify(a)
    b = sp.sympify(b)

    if a > b:
        a, b = b, a

    ancho = b - a
    margen = ancho * sp.Float('0.1', 64)

    return (
        float(-(ancho/2) - margen),
        float((ancho/2) + margen)
    )

def generar_puntos(a: sp.Float, b: sp.Float, muestras: int = 400):

    a = sp.sympify(a)
    b = sp.sympify(b)

    if a > b:
        a, b = b, a

    paso = (b-a)/(muestras-1)

    return [
        a + i*paso
        for i in range(muestras)
    ]

def limite_y(funcion: callable, a, b, muestras: int = 400) -> tuple:

    a = sp.sympify(a)
    b = sp.sympify(b)

    # antes se casteaban a,b a float ACÁ, lo que colapsaba los puntos
    # generados cuando el intervalo era diminuto (quedaban todos iguales).
    # generar_puntos ahora recibe a,b en sympy y mantiene la precisión.
    xs_local = generar_puntos(a,b,muestras)

    ys_local = [
        funcion(x)
        for x in xs_local
    ]

    ymin = min(ys_local)
    ymax = max(ys_local)

    centro = (ymax + ymin) / 2
    amplitud = max(abs(ymax-centro), abs(ymin-centro))

    if amplitud == 0:
        amplitud = sp.Float(1)

    # ocupa 50% de la pantalla
    amplitud *= 2

    return (
        float(centro-amplitud),
        float(centro+amplitud)
    )

def evaluar(fn, x):

    expr = sp.sympify(fn)

    if expr.free_symbols:
        var = next(iter(expr.free_symbols))
        return expr.subs(var,x).evalf(64)

    return expr.evalf(64)

def smoothstep(t):
    return t*t*(3-2*t)

def formato_numero(x):
    x = sp.N(x, 64)

    texto = str(x)

    # separar parte decimal
    if "." in texto:
        entero, decimal = texto.split(".")

        # eliminar ceros finales
        decimal = decimal.rstrip("0")

        if decimal:
            texto = entero + "." + decimal
        else:
            texto = entero

    return texto

def lerp(a,b,t):
    # sin castear a,b a float antes de restar: si son sympy Floats de alta
    # precisión (a0,a1,b0,b1 del historial), evita perder los dígitos que
    # distinguen intervalos diminutos. Con floats normales (fase Y) se
    # comporta exactamente igual que antes.
    return a + (b-a)*t

def mostrar_raiz_exacta(fn, historial, resultado):

    a,b,x = historial[0]

    funcion_num = lambda x: evaluar(fn,x)

    fig, ax = plt.subplots(figsize=(10,6))

    xs = generar_puntos(
        a - (b-a)*0.2,
        b + (b-a)*0.2,
        400
    )

    ys = [
        funcion_num(i)
        for i in xs
    ]

    ax.plot(
        [float(i-x) for i in xs],
        [float(y) for y in ys],
        linewidth=2
    )

    ax.axhline(
        0,
        linewidth=1
    )

    centro = (a+b)/2

    ax.scatter(
        [float(resultado-centro)],
        [0],
        s=120
    )

    ax.text(
        float(resultado-centro),
        0,
        f"  Raíz exacta\n  x={formato_numero(resultado)}",
        fontsize=12
    )

    ax.set_xlim(
        limite_x(a,b)
    )

    ax.set_ylim(
        limite_y(funcion_num,a,b)
    )

    ax.set_title(
        "Raíz encontrada exactamente"
    )

    ax.grid(True)

    plt.show()

def mostrar_bolzano(fn: sp.Expr, historial: list, resultado: sp.Float):

    if len(historial) == 1:
        mostrar_raiz_exacta(fn, historial, resultado)
        return
    funcion_num = lambda x: evaluar(fn,x)

    iteraciones_animadas = min(
        MAX_ITER_MOSTRADAS,
        max(len(historial)-1, 0)
    )

    raiz_exacta = (len(historial) == 1)

    # ================================
    # MUESTREO ADAPTATIVO
    # ================================

    x_min = min(min(i[0], i[1]) for i in historial)
    x_max = max(max(i[0], i[1]) for i in historial)

    margen = (x_max-x_min)*0.2

    lista_x = []

    # unos puntos fuera del intervalo para que al inicio
    # no se corte la función en los bordes
    # extremos
    lista_x.append(
        generar_puntos(
            x_min-margen,
            x_min,
            20
        )
    )

    lista_x.append(
        generar_puntos(
            x_max,
            x_max+margen,
            20
        )
    )

    # primer intervalo: mucha resolución
    a0, b0, _ = historial[0]

    lista_x.append(
        generar_puntos(
            a0,
            b0,
            200
        )
    )

    # el resto normal
    for a, b, _ in historial[1:iteraciones_animadas+1]:

        lista_x.append(
            generar_puntos(
                a,
                b,
                20
            )
        )

    # incluir el último extremo realmente mostrado
    lista_x.append([historial[min(iteraciones_animadas, len(historial)-1)][1]])

    # unir y ordenar (sympy soporta comparación directa). Ya no hace falta
    # np.unique/np.array: los puntos se mantienen en alta precisión, y
    # unos pocos duplicados no afectan el dibujo.
    puntos = sorted(
        (x, funcion_num(x))
        for sub in lista_x
        for x in sub
    )

    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]


    # ================================
    # ESCALAS Y PRECALCULADAS
    # ================================

    escalas_y = []

    for i in range(max(0, len(historial)-1)):

        a0,b0,_ = historial[i]
        a1,b1,_ = historial[i+1]

        escalas_y.append(
            (
                limite_y(funcion_num,a0,b0),
                limite_y(funcion_num,a1,b1)
            )
        )


    # ================================
    # TIEMPOS
    # ================================

    fps = 50
    espera_inicial = fps      # 1 segundo

    espera_frames = int(s*fps)
    zoom_frames = int(s*fps)

    frames_iteracion = (
        espera_frames*3 +
        zoom_frames
    )

    espera_final = int(s*fps)
    circulo_frames = int(0.5*fps)

    frames_totales = (
        espera_inicial
        + iteraciones_animadas*frames_iteracion
        + espera_final
        + circulo_frames
        + 1
    )

    fig,ax = plt.subplots(figsize=(10,6))

    # ================================
    # ARTISTAS FIJOS
    # ================================

    linea_funcion, = ax.plot(
        [],
        [],
        color="blue",
        linewidth=2
    )


    linea_a = ax.axvline(
        0,
        color="gray",
        linewidth=2
    )

    linea_b = ax.axvline(
        0,
        color="gray",
        linewidth=2
    )


    linea_a1 = ax.axvline(
        0,
        color="green",
        linewidth=2
    )

    linea_b1 = ax.axvline(
        0,
        color="green",
        linewidth=2
    )


    zona_verde = Rectangle(
        (0,0),
        0,
        1,
        color="green",
        alpha=0.35,
        transform=ax.get_xaxis_transform()
    )

    ax.add_patch(zona_verde)


    eje_cero = ax.axhline(
        0,
        color="black",
        linewidth=1
    )

    circulo = Arc(
        (0,0),
        0,
        0,
        color="red",
        linewidth=3
    )

    ax.add_patch(circulo)

    texto_raiz = ax.text(
        0,
        0,
        "",
        color="red",
        fontsize=12,
        ha="center",
        va="bottom"
    )

    
    ax.grid(True)

    todos = [
        linea_funcion,
        linea_a,
        linea_b,
        linea_a1,
        linea_b1,
        zona_verde,
        eje_cero,
        circulo,
        texto_raiz
    ]


    for a in todos:
        a.set_visible(False)

    def actualizar_funcion(a, b):
        a = sp.sympify(a)
        b = sp.sympify(b)

        centro_x = (a + b) / 2  # mismo centro que usará limite_x(a,b)

        izq = min(a,b)
        der = max(a,b)

        seleccion = [
            (x,y)
            for x,y in zip(xs,ys)
            if izq <= x <= der
        ]

        if seleccion:
            xs_sel, ys_sel = zip(*seleccion)
            xn = [float(x - centro_x) for x in xs_sel]  # x: relativo
            yn = [float(y) for y in ys_sel]               # y: absoluto (sin cambios)
        else:
            xn, yn = [], []

        linea_funcion.set_data(xn, yn)
        linea_funcion.set_visible(True)

        return centro_x

    def actualizar(frame):

        if len(historial) == 1:
            a, b, _ = historial[0]

            centro_x = actualizar_funcion(a, b)

            linea_a.set_xdata([float(a-centro_x)]*2)
            linea_b.set_xdata([float(b-centro_x)]*2)

            linea_a.set_visible(True)
            linea_b.set_visible(True)

            ax.set_xlim(limite_x(a, b))
            ax.set_ylim(limite_y(funcion_num, a, b))

            texto_raiz.set_position(
                (
                    float(resultado-centro_x),
                    0
                )
            )
            texto_raiz.set_text(
                f"Raíz ≈ {formato_numero(resultado)}"
            )
            texto_raiz.set_visible(True)

            ax.set_title("Raíz encontrada en la primera iteración")

            return todos

        if frame < espera_inicial:

            a, b, _ = historial[0]

            centro_x = actualizar_funcion(a, b)

            linea_a.set_xdata([float(a-centro_x)]*2)
            linea_b.set_xdata([float(b-centro_x)]*2)

            linea_a.set_visible(True)
            linea_b.set_visible(True)

            ax.set_xlim(limite_x(a, b))
            ax.set_ylim(limite_y(funcion_num, a, b))

            ax.set_title("Función inicial")

            return todos

        frame -= espera_inicial

        iteracion = frame//frames_iteracion
        fase = frame%frames_iteracion

        total_animacion = iteraciones_animadas * frames_iteracion

        if frame >= total_animacion:

            a, b, _ = historial[-1]

            if len(historial) == 1:
                ax.set_title("Raíz exacta encontrada")
            else:
                ax.set_title(
                    f"Iteración {len(historial)}"
                )

            raiz = resultado

            centro_x = actualizar_funcion(a, b)

            ylim = ax.get_ylim()

            ax.set_xlim(limite_x(a, b))
            ax.set_ylim(ylim)

            espera = frame - total_animacion
            
            if raiz_exacta:
                circulo.set_visible(True)
                circulo.theta1 = 0
                circulo.theta2 = 360

            if espera == espera_final:
                circulo.set_visible(True)
            texto_raiz.set_visible(False)         

            if espera < espera_final and not raiz_exacta:
                return todos

            p = (espera-espera_final)/circulo_frames
            p = np.clip(p, 0, 1)

            # ==========================
            # CÍRCULO DE RAÍZ
            # ==========================

            x0, x1 = ax.get_xlim()
            y0, y1 = ax.get_ylim()

            ancho = x1 - x0
            alto = y1 - y0


            # radio visible en unidades del gráfico
            radio = ancho * 0.04

            circulo.width = radio * 2

            # compensar diferencia de escala
            circulo.height = radio * 2 * (alto / ancho)

            circulo.set_center(
                (
                    float(raiz - centro_x),
                    float(funcion_num(raiz))
                )
            )

            circulo.theta1 = 90
            circulo.theta2 = 90 + 360*p

            circulo.set_visible(True)

            if p >= 1:

                ymin, ymax = ax.get_ylim()

                texto_raiz.set_position(
                    (
                        float(raiz - centro_x),
                        ymin + (ymax-ymin)*0.08
                    )
                )

                texto_raiz.set_text(
                    f"Raíz ≈ {formato_numero(raiz)}"
                )

                texto_raiz.set_visible(True)

            return todos


        if iteracion >= iteraciones_animadas:
            return todos


        a0,b0,_ = historial[iteracion]
        a1,b1,_ = historial[iteracion+1]
        ultima_iteracion = (iteracion == iteraciones_animadas - 1)

        linea_a.set_visible(False)
        linea_b.set_visible(False)
        linea_a1.set_visible(False)
        linea_b1.set_visible(False)
        zona_verde.set_visible(False)
        eje_cero.set_visible(True)



        # --------------------------
        # función visible
        # --------------------------

        vista_a=a0
        vista_b=b0


        # ==========================
        # FASE 1
        # ==========================

        if fase < espera_frames:

            centro_x = actualizar_funcion(a0,b0)

            linea_a.set_xdata([float(a0-centro_x)]*2)
            linea_b.set_xdata([float(b0-centro_x)]*2)

            linea_a.set_visible(True)
            linea_b.set_visible(True)


            ylim = escalas_y[iteracion][0]



        # ==========================
        # FASE 2
        # ==========================

        elif fase < espera_frames*2:

            centro_x = actualizar_funcion(a0,b0)

            linea_a.set_xdata([float(a0-centro_x)]*2)
            linea_b.set_xdata([float(b0-centro_x)]*2)

            linea_a1.set_xdata([float(a1-centro_x)]*2)
            linea_b1.set_xdata([float(b1-centro_x)]*2)


            linea_a.set_visible(True)
            linea_b.set_visible(True)

            linea_a1.set_visible(True)
            linea_b1.set_visible(True)


            ylim = escalas_y[iteracion][0]



        # ==========================
        # FASE 3
        # ==========================

        elif fase < espera_frames*3:

            centro_x = actualizar_funcion(a0,b0)

            linea_a.set_xdata([float(a0-centro_x)]*2)
            linea_b.set_xdata([float(b0-centro_x)]*2)

            linea_a1.set_xdata([float(a1-centro_x)]*2)
            linea_b1.set_xdata([float(b1-centro_x)]*2)


            linea_a.set_visible(True)
            linea_b.set_visible(True)

            linea_a1.set_visible(True)
            linea_b1.set_visible(True)


            xa1 = float(a1-centro_x)
            xb1 = float(b1-centro_x)
            if not ultima_iteracion:
                zona_verde.set_x(xa1)
                zona_verde.set_width(xb1-xa1)
                zona_verde.set_alpha(0.35)
                zona_verde.set_visible(True)


            ylim = escalas_y[iteracion][0]



        # ==========================
        # FASE 4 ZOOM
        # ==========================

        else:

            p = (
                fase-espera_frames*3
            )/zoom_frames

            p=smoothstep(p)


            vista_a = lerp(a0,a1,p)
            vista_b = lerp(b0,b1,p)


            centro_x = actualizar_funcion(vista_a, vista_b)


            y0,y1 = escalas_y[iteracion]


            c0=(y0[0]+y0[1])/2
            c1=(y1[0]+y1[1])/2

            r0=(y0[1]-y0[0])/2
            r1=(y1[1]-y1[0])/2


            centro=lerp(c0,c1,p)
            rango=lerp(r0,r1,p)


            ylim=(
                centro-rango,
                centro+rango
            )


            if p < 0.5:

                linea_a.set_xdata([float(a0-centro_x)]*2)
                linea_b.set_xdata([float(b0-centro_x)]*2)

                linea_a.set_visible(True)
                linea_b.set_visible(True)


            if (not ultima_iteracion) and p < 1:

                xa1 = float(a1-centro_x)
                xb1 = float(b1-centro_x)
                zona_verde.set_x(xa1)
                zona_verde.set_width(xb1-xa1)
                zona_verde.set_alpha(0.35*(1-p))
                zona_verde.set_visible(True)



        ax.set_xlim(
            limite_x(vista_a,vista_b)
        )

        ax.set_ylim(
            ylim
        )

        eje_cero.set_visible(True)


        ax.set_title(
            f"Iteración {iteracion+1}"
        )


        return todos



    anim = FuncAnimation(
        fig,
        actualizar,
        frames=frames_totales,
        interval=1000/fps,
        blit=False,
        repeat=False
    )


    plt.show()

    return anim