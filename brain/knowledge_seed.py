"""
brain/knowledge_seed.py — BASE DE CONOCIMIENTO REAL de trading para el cerebro.

Siembra en Supabase (tabla knowledge) un cuerpo curado de fundamentos de trading
REALES y probados (acción del precio, indicadores, patrones, gestión de riesgo,
psicología, opciones binarias, análisis multi-temporalidad, sesiones y noticias).

Así el cerebro razona sobre una base sólida y honesta —no promesas mágicas— y puede
recuperar el concepto RELEVANTE a cada situación (vía cloud.knowledge_search).

Es idempotente: usa una versión (kb_seed_version en app_settings) para no duplicar.
"""
from __future__ import annotations

_SEED_VERSION = 1
_KIND = "fundamento"
_PREFIX = "Fundamentos de trading"

# (título, resumen buscable, contenido detallado). Todo verificable y estándar.
ENTRIES: list[tuple[str, str, str]] = [
    ("Tendencia (trend following)",
     "La tendencia es tu aliada. Alcista: máximos y mínimos crecientes. Bajista: "
     "máximos y mínimos decrecientes. Lateral: rango sin dirección. Operar A FAVOR "
     "de la tendencia dominante tiene mayor probabilidad que ir en contra.",
     "Identifica la tendencia con la estructura del precio (máximos/mínimos) y la "
     "pendiente de medias como SMA50/200. En tendencia alcista busca COMPRAS en "
     "retrocesos a soporte; en bajista, VENTAS en rebotes a resistencia. Operar contra "
     "la tendencia es de menor probabilidad y solo se justifica con señales de giro muy "
     "claras y confirmadas. 'The trend is your friend, until it bends'."),

    ("Soporte y resistencia",
     "Soporte: zona donde el precio suele frenar caídas y rebotar (suelo). Resistencia: "
     "zona donde suele frenar subidas (techo). Cuantas más veces se respeta un nivel, "
     "más fuerte es. Un soporte roto suele convertirse en resistencia y viceversa.",
     "Los niveles clave nacen de máximos/mínimos previos, números redondos y zonas de "
     "alto volumen. Se opera el REBOTE en el nivel o la RUPTURA confirmada (con vela de "
     "cierre y volumen). Evita operar 'en el aire', lejos de niveles. El retest de una "
     "ruptura ofrece entradas de buena relación riesgo/beneficio."),

    ("Medias móviles (SMA/EMA) y cruces",
     "Las medias suavizan el precio y marcan tendencia. Cruce de la media rápida (SMA9) "
     "sobre la lenta (SMA21) = señal alcista; por debajo = bajista. Precio sobre EMA50/200 "
     "= sesgo alcista de fondo. Actúan como soporte/resistencia dinámicos.",
     "El 'golden cross' (media 50 cruza sobre la 200) es señal alcista de largo plazo; el "
     "'death cross' (50 bajo 200), bajista. Las medias funcionan mejor en tendencia y dan "
     "señales falsas en mercados laterales. Combínalas con estructura de precio y volumen "
     "para filtrar cruces sin continuidad."),

    ("RSI y divergencias",
     "RSI(14) mide el impulso de 0 a 100. Por debajo de 30 = sobreventa (posible rebote "
     "al alza); por encima de 70 = sobrecompra (posible corrección). Una DIVERGENCIA "
     "(precio hace nuevo máximo pero el RSI no) anticipa un giro.",
     "En tendencia fuerte el RSI puede quedarse en zona extrema mucho tiempo: sobrecompra "
     "NO es orden de venta por sí sola. Su mayor valor son las divergencias: precio con "
     "máximo más alto y RSI con máximo más bajo (divergencia bajista) avisa de agotamiento "
     "alcista; lo simétrico para giros al alza. Confirma siempre con precio."),

    ("MACD (tendencia y momentum)",
     "MACD = diferencia de dos EMAs, con una línea de señal y un histograma. MACD cruzando "
     "por encima de su señal = impulso alcista; por debajo = bajista. El histograma mide "
     "la fuerza del momentum; su contracción avisa de pérdida de impulso.",
     "El MACD confirma tendencias y giros de momentum, pero se retrasa. Cruces por encima "
     "de la línea cero refuerzan sesgo alcista; por debajo, bajista. Como el RSI, sus "
     "divergencias con el precio son señales potentes de agotamiento. Úsalo para confirmar, "
     "no para anticipar en solitario."),

    ("Bandas de Bollinger y squeeze",
     "Bollinger(20,2): una media de 20 con dos bandas a 2 desviaciones típicas. Tocar la "
     "banda inferior puede ser sobreventa; la superior, sobrecompra. Bandas MUY estrechas "
     "('squeeze') anticipan un movimiento fuerte inminente.",
     "En rango, el precio oscila entre bandas (reversión a la media). En tendencia fuerte "
     "'camina' pegado a una banda: tocarla NO es señal de reversión por sí sola. El squeeze "
     "(baja volatilidad) precede a expansiones; opera la RUPTURA en la dirección confirmada. "
     "Combínalo con volumen y estructura."),

    ("Vela: martillo y hombre colgado",
     "El martillo es una vela con cuerpo pequeño arriba y mecha inferior larga que aparece "
     "tras una caída: señala posible giro al alza (rechazo de precios bajos). La misma forma "
     "tras una subida es 'hombre colgado' y avisa de posible giro a la baja.",
     "La mecha larga muestra que los vendedores empujaron pero los compradores recuperaron "
     "el control (martillo). Requiere CONFIRMACIÓN: una vela alcista posterior que cierre por "
     "encima. Su fiabilidad sube en soporte y con volumen alto. Sin confirmación, es solo "
     "indecisión."),

    ("Vela: envolvente alcista y bajista",
     "Envolvente alcista: una vela verde grande que 'envuelve' por completo la roja anterior, "
     "tras una caída: giro al alza. Envolvente bajista: vela roja que envuelve a la verde "
     "previa tras una subida: giro a la baja. Patrón de dos velas muy fiable.",
     "Refleja un cambio de control brusco entre compradores y vendedores. Es más fiable en "
     "niveles clave (soporte/resistencia), con la segunda vela de cuerpo amplio y volumen "
     "creciente. Entra en la ruptura del extremo de la envolvente y coloca el stop al otro "
     "lado del patrón."),

    ("Vela: doji, estrella del amanecer y del atardecer",
     "El doji (apertura ≈ cierre) señala INDECISIÓN y posible giro en un extremo. La estrella "
     "del amanecer (roja, doji/pequeña, verde) marca suelo; la del atardecer (verde, pequeña, "
     "roja) marca techo. Patrones de agotamiento de tres velas.",
     "Un doji aislado en medio de un rango dice poco; su valor está en extremos de tendencia "
     "y en niveles. Las estrellas del amanecer/atardecer son giros de tres velas que necesitan "
     "cierre de confirmación en la tercera. Aumentan su peso con volumen y confluencia con "
     "soporte/resistencia o Fibonacci."),

    ("Vela: estrella fugaz y martillo invertido",
     "Estrella fugaz: cuerpo pequeño abajo y mecha superior larga tras una subida: rechazo de "
     "precios altos, posible giro a la baja. Martillo invertido: misma forma tras una caída, "
     "posible giro al alza si se confirma.",
     "La mecha superior larga muestra que los compradores intentaron subir pero fueron "
     "rechazados (estrella fugaz). En resistencia y con volumen, avisa de techo. Requiere "
     "confirmación bajista posterior. El martillo invertido es su espejo en suelos y también "
     "exige confirmación al alza."),

    ("Patrón doble techo y doble suelo",
     "Doble techo (forma de M): dos máximos similares que el precio no logra superar: giro "
     "bajista al romper el mínimo intermedio (neckline). Doble suelo (forma de W): dos mínimos "
     "similares: giro alcista al romper el máximo intermedio.",
     "Marcan agotamiento de la tendencia previa. La señal se ACTIVA al romper la línea de "
     "cuello con cierre; el objetivo teórico es la altura del patrón proyectada desde la "
     "ruptura. Un retest de la neckline ofrece segunda entrada. El volumen suele caer en el "
     "segundo pico/valle y crecer en la ruptura."),

    ("Patrón hombro-cabeza-hombro",
     "Hombro-cabeza-hombro: tres picos, el central (cabeza) más alto que los laterales "
     "(hombros): giro bajista al romper la línea de cuello. Su versión invertida (en suelos) "
     "es un giro alcista. Uno de los patrones de reversión más fiables.",
     "Refleja el paso de tendencia alcista a bajista (o viceversa en el invertido). Se opera "
     "la ruptura de la neckline con cierre; objetivo = distancia de la cabeza a la neckline "
     "proyectada. El volumen decreciente hacia la cabeza y creciente en la ruptura aumenta la "
     "fiabilidad."),

    ("Patrones de continuación: triángulos y banderas",
     "Triángulos (simétrico, ascendente, descendente) y banderas son PAUSAS dentro de una "
     "tendencia. Suelen resolverse a favor de la tendencia previa. Se opera la ruptura del "
     "patrón con volumen, en la dirección dominante.",
     "El triángulo ascendente (techo plano, suelos crecientes) suele romper al alza; el "
     "descendente, a la baja. La bandera es una consolidación corta contra-tendencia tras un "
     "impulso fuerte ('mástil'). Objetivo aproximado = altura del mástil desde la ruptura. "
     "Evita anticipar: espera el cierre fuera del patrón."),

    ("El volumen confirma el movimiento",
     "El volumen es el combustible del precio. Rupturas y tendencias con volumen creciente son "
     "más fiables; movimientos con volumen bajo suelen ser falsos o agotarse. Divergencias de "
     "volumen avisan de debilidad en la tendencia.",
     "Una ruptura de resistencia con volumen alto tiene más probabilidad de continuar; con "
     "volumen flojo, sospecha de 'falsa ruptura' (fakeout). En tendencia sana el volumen "
     "acompaña los impulsos y baja en los retrocesos. El clímax de volumen en un extremo puede "
     "marcar agotamiento y giro."),

    ("Gestión de riesgo: la regla del 1-2%",
     "Nunca arriesgues más del 1-2% de tu capital en UNA operación. Con stop-loss obligatorio "
     "en cada entrada. Así una racha de pérdidas no destruye la cuenta y sobrevives para que "
     "tu ventaja estadística actúe a largo plazo.",
     "El tamaño de posición se calcula a partir de la distancia al stop y del riesgo máximo "
     "aceptado, no del capricho. Sin stop no hay gestión de riesgo. Proteger el capital es la "
     "prioridad número uno: se puede recuperar de pérdidas pequeñas, no de una catastrófica. "
     "La supervivencia precede a la rentabilidad."),

    ("Ratio riesgo/beneficio y esperanza matemática",
     "Busca operaciones con ratio riesgo/beneficio favorable (p.ej. arriesgar 1 para ganar "
     "1.5-2). Con un R/B de 1:2 puedes acertar solo el 40% y aun así ser rentable. La "
     "ESPERANZA = (prob_acierto × ganancia) − (prob_fallo × pérdida) debe ser positiva.",
     "No basta con acertar mucho: importa cuánto ganas cuando aciertas frente a cuánto pierdes "
     "cuando fallas. Un sistema con 50% de aciertos y R/B 1:2 gana dinero; uno con 70% de "
     "aciertos y R/B 1:0.3 puede perderlo. Calcula la esperanza antes de confiar en una "
     "estrategia y córtala si es negativa."),

    ("Psicología del trading: miedo, codicia y disciplina",
     "Los dos enemigos son el MIEDO (cerrar ganancias antes de tiempo, no entrar) y la CODICIA "
     "(arriesgar de más, no poner stop, perseguir el precio). La disciplina de seguir un plan "
     "escrito vence a la emoción. Opera el plan, no la corazonada.",
     "La mayoría pierde por falta de disciplina, no de conocimiento. Reglas que ayudan: define "
     "entrada, stop y objetivo ANTES de entrar; no muevas el stop en contra; acepta la pérdida "
     "como coste del negocio; no operes por 'recuperar' (venganza). Un diario de operaciones "
     "revela tus errores repetidos."),

    ("Opciones binarias: elegir la expiración",
     "En opciones binarias eliges dirección y un tiempo de vencimiento. La expiración debe "
     "encajar con la volatilidad y el marco de la señal: mercados rápidos y señales de corto "
     "plazo piden vencimientos cortos; tendencias estables permiten plazos mayores.",
     "Una expiración demasiado corta te expone al ruido aleatorio; demasiado larga puede diluir "
     "una señal de momentum. Regla práctica: que el vencimiento dé tiempo a que la tesis se "
     "cumpla sin quedar a merced de un tick. Analiza sobre velas CERRADAS para que la señal no "
     "cambie cada segundo."),

    ("Opciones binarias: payout y punto de equilibrio",
     "Con un pago (payout) del 85%, el porcentaje de aciertos de equilibrio es 1/(1+0.85) ≈ "
     "54%. Necesitas ganar MÁS del 54% de las operaciones solo para no perder. Cuanto menor el "
     "payout, mayor el % de acierto exigido.",
     "Las binarias tienen una desventaja estructural: pagas 100% al fallar pero cobras solo el "
     "payout al acertar. Por eso solo son viables con una ventaja real y sostenida por encima "
     "del punto de equilibrio, gestión de riesgo estricta y sin sobre-operar. Trátalas como "
     "probabilidad, no como lotería."),

    ("Análisis multi-temporalidad y confluencia",
     "Una señal es MÁS fiable cuando coincide en varias temporalidades (1m, 15m, 1h, diario). "
     "La CONFLUENCIA —varias señales independientes apuntando a lo mismo (tendencia + soporte + "
     "patrón de vela + RSI)— multiplica la probabilidad. Si el corto y el largo plazo se "
     "contradicen, lo prudente es ESPERAR.",
     "Usa la temporalidad alta para la DIRECCIÓN (tendencia de fondo) y la baja para el TIMING "
     "de entrada. Operar en 1m a favor del 1h y del diario es mucho más seguro que en contra. "
     "Cuando las señales chocan, no fuerces la operación: la mejor operación a veces es no "
     "operar."),

    ("Retrocesos de Fibonacci",
     "Tras un impulso, el precio suele retroceder a niveles de Fibonacci (38.2%, 50%, 61.8%) "
     "antes de continuar la tendencia. Son zonas donde buscar reentradas a favor de la "
     "tendencia. El 61.8% es el retroceso 'dorado' más vigilado.",
     "Traza Fibonacci del inicio al fin del impulso. Un retroceso al 50-61.8% que además "
     "coincide con un soporte/resistencia previo o una media (confluencia) es de alta "
     "probabilidad. Si el precio supera el 78.6% o el 100%, la tesis de continuación se "
     "debilita: probablemente sea un giro, no un retroceso."),

    ("Sesiones de mercado y volatilidad (forex)",
     "El forex opera 24h en sesiones: Asia, Londres y Nueva York. La mayor volatilidad y "
     "liquidez ocurre en el solape Londres–Nueva York (aprox. 13:00–16:00 UTC). Operar en horas "
     "de baja liquidez suele dar movimientos erráticos y spreads amplios.",
     "Cada par se mueve más en la sesión de su divisa (EUR/USD en Londres/NY; USD/JPY en Asia/"
     "NY). El solape Londres-NY concentra el mayor rango. Evita abrir posiciones justo en el "
     "cambio de sesión o en horas muertas. La volatilidad adecuada facilita que la señal se "
     "desarrolle."),

    ("Noticias y eventos macro",
     "Datos de alto impacto (tipos de interés de los bancos centrales, NFP/empleo de EE. UU., "
     "IPC/inflación, PIB) disparan volatilidad brusca e impredecible. Operar JUSTO en el "
     "impacto es una lotería: spreads se amplían y el precio pega latigazos.",
     "Consulta un calendario económico y marca los eventos rojos. Lo prudente suele ser esperar "
     "a que pase el impacto y el mercado 'digiera' la noticia antes de operar con la nueva "
     "tendencia. Las noticias explican por qué se mueve el precio; el gráfico muestra cómo. "
     "Evita sorpresas: revisa earnings de acciones y datos macro del día."),

    ("Sobre-operar (overtrading) destruye cuentas",
     "Operar demasiado —por aburrimiento, ansiedad o para 'recuperar'— acumula comisiones, "
     "pérdidas por señales débiles y desgaste emocional. La calidad supera a la cantidad: pocas "
     "operaciones de ALTA probabilidad rinden más que muchas mediocres.",
     "Señales de overtrading: entrar sin que se cumplan tus reglas, subir el tamaño tras "
     "perder, no respetar el plan. Concéntrate en una operación a la vez, espera setups claros "
     "y acepta estar en liquidez sin operar. 'No operar' es una posición válida y muchas veces "
     "la más rentable."),

    ("Backtesting y no sobre-optimizar",
     "Antes de confiar en una estrategia, pruébala en datos históricos (backtest) y mide su "
     "tasa de acierto, ratio riesgo/beneficio y racha máxima de pérdidas. Cuidado con "
     "sobre-optimizar a datos pasados (curve-fitting): lo que brilla en el histórico puede "
     "fallar en vivo.",
     "Un backtest honesto usa muestra amplia y reglas fijas, sin retocarlas hasta que 'cuadre'. "
     "Valida además fuera de muestra y con resultados reales en pequeño. Ninguna estrategia "
     "gana siempre: importa la esperanza positiva a largo plazo y sobrevivir a las rachas "
     "malas. Aprende de cada operación cerrada, acierto o fallo."),

    ("Dejar correr ganancias y cortar pérdidas",
     "Regla de oro: corta las pérdidas rápido y deja correr las ganancias. El error típico es "
     "lo contrario (cerrar ganancias por miedo y aguantar pérdidas por esperanza). El stop "
     "protege; el trailing stop y los objetivos parciales capturan tendencia.",
     "Mueve el stop a break-even cuando la operación avanza a tu favor para eliminar el riesgo. "
     "Un trailing stop sigue al precio y deja correr la tendencia mientras protege lo ganado. "
     "Toma beneficios parciales en objetivos y niveles clave. Nunca conviertas una operación "
     "perdedora en 'inversión de largo plazo' quitando el stop."),
]


def already_seeded() -> bool:
    """True si la base ya está sembrada a esta versión (evita duplicar)."""
    try:
        from db import cloud
        return int(cloud.setting_get("kb_seed_version", 0) or 0) >= _SEED_VERSION
    except Exception:
        return False


def seed(force: bool = False) -> int:
    """Inserta la base de conocimiento en Supabase. Devuelve cuántas entradas guardó.
    Idempotente: no reescribe si ya está a esta versión (salvo force=True)."""
    from db import cloud
    if not force and already_seeded():
        return 0
    n = 0
    for title, summary, content in ENTRIES:
        try:
            cloud.knowledge_save(_KIND, f"{_PREFIX} · {title}", 0.0, summary, content)
            n += 1
        except Exception:
            pass
    try:
        cloud.setting_set("kb_seed_version", _SEED_VERSION)
    except Exception:
        pass
    return n


def count() -> int:
    return len(ENTRIES)
