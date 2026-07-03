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

_SEED_VERSION = 2
_KIND = "fundamento"
_PREFIX = "Fundamentos de trading"

# El conocimiento se organiza en LOTES versionados: al subir la versión se inyectan
# SOLO los lotes nuevos (no se duplican los anteriores). Cada entrada es
# (título, resumen buscable, contenido detallado). Todo verificable y estándar.
_BATCH1: list[tuple[str, str, str]] = [
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

# ---- LOTE 2: conocimiento PROFUNDO (nivel profesional) ----
_BATCH2: list[tuple[str, str, str]] = [
    ("Estructura de mercado: BOS y CHoCH",
     "La estructura de mercado se lee por máximos y mínimos. BOS (break of structure): el "
     "precio rompe el último máximo (alcista) o mínimo (bajista) CONTINUANDO la tendencia. "
     "CHoCH (change of character): rompe en sentido contrario, primer aviso de posible GIRO.",
     "En tendencia alcista se encadenan máximos y mínimos crecientes; un BOS al alza confirma "
     "continuación. Cuando el precio deja de hacer mínimos crecientes y rompe el último mínimo "
     "relevante, ocurre un CHoCH: la tendencia puede estar cambiando. Opera a favor de la "
     "estructura vigente y desconfía de entradas contra-estructura hasta ver CHoCH + confirmación."),

    ("Order blocks (bloques de órdenes)",
     "Un order block es la última vela contraria antes de un movimiento fuerte e impulsivo "
     "(la zona donde entró el dinero institucional). El precio suele VOLVER a testear ese bloque "
     "antes de continuar: ofrece entradas de alta probabilidad a favor del impulso.",
     "El order block alcista es la última vela bajista antes de un rally; el bajista, la última "
     "vela alcista antes de una caída. Se marca el rango de esa vela como zona de interés. La "
     "entrada busca la reacción del precio al regresar (mitigación) con confirmación (vela de "
     "rechazo, CHoCH menor). Ganan valor si coinciden con desequilibrios y liquidez cercana."),

    ("Zonas de oferta y demanda",
     "Demanda: zona donde la compra superó a la venta y el precio despegó al alza (suelo de "
     "acumulación). Oferta: zona donde la venta dominó y el precio cayó (techo de distribución). "
     "El precio tiende a reaccionar al volver a esas zonas 'frescas' (aún no testeadas).",
     "Se dibujan como rectángulos en el origen de movimientos impulsivos. Una zona pierde fuerza "
     "cada vez que se testea. Las mejores operaciones combinan una zona de demanda fresca a favor "
     "de la tendencia superior, con confluencia de Fibonacci o soporte. Entra con confirmación y "
     "stop al otro lado de la zona."),

    ("Liquidez y barridos de stops (stop hunt)",
     "Bajo mínimos y sobre máximos evidentes se acumulan órdenes stop (liquidez). El precio suele "
     "'barrer' esas zonas (falsa ruptura que caza stops) antes de girar en la dirección real. Un "
     "barrido de liquidez seguido de CHoCH es una señal de giro potente.",
     "Los grandes operadores necesitan liquidez para ejecutar volumen: empujan el precio a zonas "
     "obvias de stops, los activan y luego mueven en sentido contrario. Señales: mecha larga que "
     "supera un máximo/mínimo clave y cierra de vuelta dentro del rango. No pongas tus stops en el "
     "sitio 'obvio'; dales aire más allá de la zona de barrido."),

    ("Fair value gaps (desequilibrios)",
     "Un fair value gap (FVG) o imbalance es un hueco de ineficiencia entre tres velas donde el "
     "precio se movió tan rápido que dejó una zona sin negociar. El precio suele REGRESAR a "
     "rellenar ese desequilibrio antes de continuar.",
     "Se identifica cuando la mecha de la vela 1 y la de la vela 3 no se solapan, dejando un vacío "
     "en la vela 2 impulsiva. Actúa como imán y como zona de reentrada a favor del impulso. Los "
     "FVG combinados con order blocks y con la tendencia superior dan entradas precisas. No todo "
     "FVG se rellena de inmediato: úsalo con confirmación, no en solitario."),

    ("Método Wyckoff: acumulación y distribución",
     "Wyckoff describe cómo el 'dinero inteligente' ACUMULA en rangos antes de subidas y DISTRIBUYE "
     "antes de caídas. Fases con eventos clave: spring (barrido bajo el rango en acumulación) y "
     "upthrust (barrido sobre el rango en distribución), que preceden al movimiento real.",
     "En acumulación, tras un rango, un 'spring' perfora el soporte, caza stops y vuelve dentro: "
     "señal alcista. En distribución, el 'upthrust' hace lo simétrico sobre resistencia: señal "
     "bajista. La ley de causa-efecto: cuanto mayor el rango de acumulación, mayor el movimiento "
     "posterior. El volumen confirma cada fase (esfuerzo vs resultado)."),

    ("VWAP (precio medio ponderado por volumen)",
     "El VWAP es el precio promedio ponderado por volumen del día. Actúa como imán y como soporte/"
     "resistencia dinámico intradía. Precio sobre VWAP = sesgo comprador de la sesión; bajo VWAP = "
     "sesgo vendedor. Muy usado por institucionales para medir ejecución.",
     "En tendencia intradía, los retrocesos al VWAP ofrecen reentradas a favor. En rango, el precio "
     "oscila alrededor del VWAP (reversión a la media). Las bandas de desviación del VWAP marcan "
     "extremos. Combínalo con la apertura de sesión y niveles previos para timing de scalping y "
     "day trading."),

    ("Ichimoku Kinko Hyo (la nube)",
     "Ichimoku muestra tendencia, soporte/resistencia y momentum de un vistazo. Precio sobre la "
     "nube (Kumo) = alcista; bajo la nube = bajista; dentro = indefinido. El cruce Tenkan/Kijun y "
     "el grosor de la nube confirman fuerza y posibles giros.",
     "Componentes: Tenkan (media rápida), Kijun (media lenta, soporte dinámico), Senkou A/B que "
     "forman la nube proyectada al futuro, y Chikou (cierre desplazado atrás) que confirma. Señal "
     "alcista robusta: precio sobre nube, Tenkan sobre Kijun y Chikou libre por encima del precio. "
     "Una nube gruesa = soporte/resistencia fuerte; fina = fácil de perforar."),

    ("ADX: fuerza de la tendencia",
     "El ADX mide la FUERZA de la tendencia (no su dirección) de 0 a 100. ADX < 20: mercado sin "
     "tendencia (rango), evita estrategias de seguimiento. ADX > 25 y subiendo: tendencia fuerte, "
     "favorece seguir tendencia. Los +DI/−DI indican la dirección.",
     "Usa el ADX como filtro de régimen: con ADX bajo, prioriza reversión a la media (rango, "
     "Bollinger); con ADX alto, prioriza continuación (rupturas, medias, pullbacks). +DI sobre −DI "
     "= presión alcista; −DI sobre +DI = bajista. Un ADX que cae desde valores altos avisa de "
     "agotamiento de la tendencia."),

    ("Oscilador estocástico",
     "El estocástico compara el cierre con el rango reciente (0-100). >80 sobrecompra, <20 "
     "sobreventa. El cruce de %K sobre %D en zona baja da señal alcista; a la inversa, bajista. "
     "Sus divergencias con el precio anticipan giros, como en el RSI.",
     "Funciona mejor en mercados en RANGO; en tendencia fuerte se satura y da señales falsas "
     "(igual que el RSI). El estocástico lento (más suavizado) reduce el ruido. Combínalo con la "
     "tendencia superior: en tendencia alcista, usa sobreventa del estocástico para reentradas al "
     "alza, ignorando las señales de venta."),

    ("Divergencias regulares y ocultas",
     "Divergencia REGULAR = giro: precio hace máximo más alto pero el oscilador (RSI/MACD) máximo "
     "más bajo (bajista), o mínimo más bajo con oscilador más alto (alcista). Divergencia OCULTA = "
     "continuación: avisa de que la tendencia seguirá tras un retroceso.",
     "La divergencia oculta alcista: precio con mínimo MÁS ALTO y oscilador con mínimo más bajo, en "
     "tendencia alcista → reanudación al alza. La oculta bajista: precio con máximo más bajo y "
     "oscilador con máximo más alto, en tendencia bajista → reanudación a la baja. Las regulares "
     "buscan el giro; las ocultas, entrar a favor de la tendencia en el retroceso."),

    ("Ondas de Elliott (base)",
     "La teoría de Elliott ve el mercado en ciclos: 5 ondas a favor de la tendencia (impulso, "
     "1-2-3-4-5) seguidas de 3 ondas correctivas (A-B-C). La onda 3 suele ser la más larga y "
     "potente; la onda 2 no retrocede más allá del inicio de la 1.",
     "Reglas clave: la onda 2 nunca retrocede el 100% de la 1; la 3 no es la más corta; la 4 no "
     "solapa el territorio de la 1. Las correcciones (A-B-C) ofrecen reentradas a favor de la "
     "tendencia mayor. Elliott es interpretativo y subjetivo: úsalo como marco de contexto, "
     "confirmado con estructura y Fibonacci, no como predicción exacta."),

    ("Puntos pivote (pivot points)",
     "Los pivotes calculan niveles de soporte (S1,S2,S3) y resistencia (R1,R2,R3) a partir del "
     "máximo, mínimo y cierre del período previo. El precio sobre el pivote central = sesgo "
     "alcista del día; por debajo = bajista. Muy usados en intradía.",
     "El pivote (P = (H+L+C)/3) actúa como eje del día. Los operadores buscan rebotes en S1/R1 y "
     "rupturas hacia S2/R2. Funcionan porque muchos participantes los vigilan (profecía "
     "autocumplida). Combínalos con VWAP, apertura y niveles previos para confluencia. Los "
     "pivotes de Fibonacci usan proporciones 0.382/0.618 en lugar de fijas."),

    ("Velas: tres soldados y tres cuervos",
     "Tres soldados blancos: tres velas alcistas consecutivas con cierres crecientes tras una "
     "caída: giro alcista fuerte. Tres cuervos negros: tres velas bajistas seguidas tras una "
     "subida: giro bajista. Muestran un cambio de control sostenido.",
     "Su fiabilidad sube si los cuerpos son amplios, con mechas pequeñas y volumen creciente, y si "
     "aparecen en un nivel clave. Cuidado con entrar tarde: tras tres velas grandes el movimiento "
     "puede estar extendido y sobrevenir un retroceso. Ideal esperar un pequeño pullback para "
     "entrar con mejor riesgo/beneficio."),

    ("Velas: pinzas, harami y marubozu",
     "Pinza (tweezer): dos velas con máximos (techo) o mínimos (suelo) casi idénticos: rechazo de "
     "nivel, posible giro. Harami: vela pequeña dentro del cuerpo de la anterior grande: "
     "indecisión/pausa. Marubozu: vela sin mechas, cuerpo pleno: dominio total de un lado.",
     "La pinza en soporte/resistencia con confirmación señala giro. El harami avisa de pérdida de "
     "impulso y posible reversión, sobre todo tras tendencia extendida. Un marubozu alcista "
     "(sin mechas) muestra compradores en control absoluto y suele preceder continuación. Todos "
     "ganan fiabilidad con contexto (nivel, tendencia, volumen)."),

    ("Huecos (gaps): ruptura, continuación y agotamiento",
     "Un gap es un salto de precio sin negociación entre velas (típico en acciones al abrir). Gap "
     "de RUPTURA: inicia un movimiento desde un rango. De CONTINUACIÓN (runaway): a mitad de "
     "tendencia, la confirma. De AGOTAMIENTO: al final, suele rellenarse y avisar de giro.",
     "Muchos gaps tienden a 'rellenarse' cuando el precio vuelve a la zona del hueco. El gap de "
     "ruptura con volumen alto suele mantenerse y marcar tendencia. El de agotamiento aparece tras "
     "un movimiento extendido con volumen clímax y anticipa reversión. En cripto/forex 24h hay "
     "menos gaps salvo el de apertura del domingo en forex."),

    ("Trampas y falsas rupturas (bull/bear traps)",
     "Una falsa ruptura (fakeout) supera un nivel clave y regresa rápido, atrapando a quienes "
     "entraron en la ruptura. Trampa alcista: ruptura de resistencia que falla y cae. Trampa "
     "bajista: ruptura de soporte que falla y sube. Son fuente de barridos de liquidez.",
     "Para evitarlas: espera CIERRE de vela fuera del nivel (no solo mecha), confirma con volumen y "
     "considera el retest. Una ruptura sin volumen o contra la tendencia superior es sospechosa. "
     "Paradójicamente, una falsa ruptura confirmada (vuelta dentro del rango) es una de las "
     "señales de reversión más rentables: opera a favor del rechazo."),

    ("Régimen de mercado: tendencia vs rango",
     "El mercado alterna entre TENDENCIA (direccional) y RANGO (lateral). La táctica debe cambiar: "
     "en tendencia, seguir el movimiento (rupturas, pullbacks a medias); en rango, reversión a la "
     "media (comprar soporte, vender resistencia). Usar la estrategia equivocada al régimen pierde.",
     "Identifica el régimen con ADX (alto=tendencia, bajo=rango), la pendiente de las medias y la "
     "estructura. El mayor error es aplicar seguimiento de tendencia en un rango (te barren en los "
     "extremos) o reversión a la media en tendencia fuerte (te arrolla). Adapta indicadores y "
     "gestión al régimen actual."),

    ("Tamaño de posición por volatilidad (ATR)",
     "Ajusta el tamaño y el stop a la VOLATILIDAD (ATR), no a un número fijo. Stop = múltiplo de "
     "ATR (p.ej. 1.5–2×ATR) para dar aire al ruido; el tamaño se reduce cuando el ATR es alto para "
     "mantener constante el riesgo en dinero por operación.",
     "Fórmula: tamaño = (capital × riesgo%) / (distancia_al_stop). Si el stop se fija en ATR, en "
     "mercados volátiles el stop es más ancho y el tamaño menor (mismo riesgo $). Así normalizas el "
     "riesgo entre activos y regímenes. Nunca uses el mismo tamaño fijo en un activo tranquilo y en "
     "uno muy volátil: el riesgo real sería muy distinto."),

    ("Criterio de Kelly y Kelly fraccional",
     "Kelly calcula la fracción óptima del capital a arriesgar para maximizar el crecimiento a "
     "largo plazo, según tu probabilidad de acierto y tu ratio ganancia/pérdida. En la práctica se "
     "usa KELLY FRACCIONAL (media o cuarto de Kelly) para reducir la volatilidad y el riesgo de ruina.",
     "Kelly = W − (1−W)/R, donde W = prob. de acierto y R = ganancia media/pérdida media. Kelly "
     "completo maximiza crecimiento pero con drawdowns brutales; la mayoría usa 1/4–1/2 de Kelly. "
     "Si Kelly da negativo, tu sistema no tiene ventaja: no operes. Requiere estimaciones honestas "
     "de W y R (de tu backtest/resultados reales), no optimistas."),

    ("Riesgo de ruina y control del drawdown",
     "El riesgo de ruina es la probabilidad de perder tanto capital que no puedas recuperarte. "
     "Crece con el riesgo por operación y las rachas de pérdidas. Perder el 50% exige ganar el "
     "100% para recuperar: por eso limitar el drawdown es vital para la supervivencia.",
     "Toda estrategia sufre rachas perdedoras: con 50% de aciertos, rachas de 6-8 seguidas son "
     "normales. Arriesgar poco (1-2%) mantiene el drawdown manejable y evita la ruina. Fija un "
     "límite de pérdida diaria/semanal y detente al alcanzarlo. La matemática de la recuperación es "
     "asimétrica: cuanto más caes, exponencialmente más cuesta volver."),

    ("Correlaciones entre activos",
     "Los mercados están conectados. El dólar (DXY) suele moverse INVERSO al oro y al EUR/USD. En "
     "cripto, la dominancia de BTC guía a las altcoins. Entornos 'risk-on' favorecen acciones y "
     "cripto; 'risk-off' favorecen dólar, oro y bonos.",
     "Operar dos activos muy correlacionados a la vez DUPLICA el riesgo (es casi la misma apuesta). "
     "Usa las correlaciones como confirmación: si vas largo en oro, un DXY débil lo apoya. "
     "Divergencias entre correlacionados avisan de giros. Vigila el DXY para forex/materias y la "
     "dominancia BTC para altcoins antes de operar."),

    ("Costes: spread, slippage y comisiones",
     "Cada operación tiene costes: spread (diferencia compra/venta), slippage (ejecución a peor "
     "precio en alta volatilidad) y comisiones. En scalping y binarias los costes pesan mucho "
     "sobre el resultado: una ventaja pequeña puede desaparecer tras costes.",
     "Opera en horas líquidas para spreads estrechos y evita el momento exacto de noticias (spreads "
     "se disparan). En binarias, el 'coste' es el payout inferior al 100%: exige una ventaja real "
     "sobre el punto de equilibrio. Incluye SIEMPRE los costes en tu backtest; ignorarlos hace "
     "parecer rentable un sistema que no lo es."),

    ("Gestión de la operación: parciales y break-even",
     "Gestionar la operación abierta importa tanto como la entrada. Mueve el stop a break-even al "
     "alcanzar cierto avance (elimina el riesgo), toma beneficios PARCIALES en objetivos/niveles y "
     "deja correr el resto con trailing stop para capturar tendencia.",
     "Escalar salidas: cierra 1/3 o 1/2 en el primer objetivo (asegura ganancia y reduce estrés) y "
     "gestiona el resto con el stop en break-even. Evita escalar HACIA una posición perdedora "
     "(promediar a la baja sin plan). Un buen plan de gestión convierte aciertos medianos en "
     "operaciones rentables y limita el daño de los fallos."),

    ("Martingala vs anti-martingala",
     "Martingala (doblar tras cada pérdida para 'recuperar') es un camino directo a la ruina: una "
     "racha perdedora —que ocurre— revienta la cuenta. Anti-martingala (aumentar tamaño cuando "
     "ganas y reducir cuando pierdes) es lo correcto: aprovecha rachas buenas y protege en malas.",
     "La martingala tiene alta probabilidad de pequeñas ganancias y baja probabilidad de una "
     "pérdida catastrófica: la esperanza sigue siendo negativa y el riesgo de ruina, altísimo. En "
     "binarias es especialmente letal por el payout <100%. Usa tamaño fijo por % de capital o "
     "anti-martingala moderada; nunca persigas pérdidas subiendo la apuesta."),

    ("Análisis top-down multi-temporalidad",
     "Flujo profesional: empieza por la temporalidad ALTA (diario/4h) para la tendencia y niveles "
     "mayores; baja a la media (1h/15m) para el contexto y zonas; y a la baja (5m/1m) solo para el "
     "TIMING de entrada. Operar alineado con lo superior es lo más fiable.",
     "Define primero el sesgo (alcista/bajista/neutral) en el marco alto y las zonas de interés "
     "(soporte/resistencia, order blocks). Luego espera en la temporalidad baja una confirmación "
     "(CHoCH, patrón de vela, rechazo) DENTRO de esas zonas y a favor del sesgo. Nunca dejes que la "
     "temporalidad baja te haga operar contra la alta."),

    ("Diario de trading y expectativa por setup",
     "Registrar cada operación (motivo, entrada, stop, objetivo, resultado, emoción) es lo que "
     "convierte experiencia en mejora. Con datos calculas la EXPECTATIVA por tipo de setup y "
     "descartas los que pierden, doblando en los que ganan. Sin diario, repites errores a ciegas.",
     "Métricas a seguir: tasa de acierto, ratio riesgo/beneficio real, expectativa (ganancia media "
     "por operación), drawdown máximo y adherencia al plan. Filtra por setup, activo, hora y "
     "temporalidad para hallar tu 'edge'. El diario también revela sesgos emocionales (operar por "
     "aburrimiento, venganza). Mides, aprendes y ajustas: así se llega a ser consistente."),

    ("Checklist de entrada y confluencia",
     "Sistematiza tus entradas con una lista de verificación: solo operas cuando se cumplen varias "
     "condiciones (confluencia): tendencia superior a favor, zona/nivel válido, patrón o "
     "confirmación de vela, gestión de riesgo definida. Menos operaciones, pero mejores.",
     "Ejemplo de checklist: (1) sesgo de temporalidad alta claro; (2) precio en zona de interés "
     "(soporte/OB/Fibonacci); (3) confirmación (CHoCH, envolvente, rechazo); (4) R/B ≥ 1:2; (5) sin "
     "noticia de alto impacto inminente; (6) tamaño según riesgo 1-2%. Si falta algo, no operas. La "
     "disciplina de la checklist elimina las entradas impulsivas y de baja probabilidad."),
]

# Todos los lotes y el conjunto completo (para count() y recuperación)
_BATCHES: dict[int, list[tuple[str, str, str]]] = {1: _BATCH1, 2: _BATCH2}
ENTRIES: list[tuple[str, str, str]] = [e for v in sorted(_BATCHES) for e in _BATCHES[v]]


def already_seeded() -> bool:
    """True si la base ya está sembrada a esta versión (evita duplicar)."""
    try:
        from db import cloud
        return int(cloud.setting_get("kb_seed_version", 0) or 0) >= _SEED_VERSION
    except Exception:
        return False


def seed(force: bool = False) -> int:
    """Inyecta la base de conocimiento en Supabase. Devuelve cuántas entradas guardó.

    Incremental: inserta SOLO los lotes cuya versión aún no se ha sembrado (así al
    añadir conocimiento nuevo no se duplica el anterior). Con force=True recarga todo.
    """
    from db import cloud
    current = 0
    if not force:
        try:
            current = int(cloud.setting_get("kb_seed_version", 0) or 0)
        except Exception:
            current = 0
        if current >= _SEED_VERSION:
            return 0
    n = 0
    for v in sorted(_BATCHES):
        if v <= current:
            continue  # ese lote ya está sembrado
        for title, summary, content in _BATCHES[v]:
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
