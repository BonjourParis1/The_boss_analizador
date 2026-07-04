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

_SEED_VERSION = 11
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

# ---- LOTE 3: ESTRATEGIAS operables + conocimiento por MERCADO (aplica en todos) ----
_BATCH3: list[tuple[str, str, str]] = [
    ("Estrategia: pullback a la EMA en tendencia",
     "Estrategia de continuación (cripto, forex, índices, acciones, materias): en tendencia "
     "clara, espera un retroceso a la EMA20/50 y entra a favor de la tendencia cuando el precio "
     "rebota con una vela de confirmación. Stop bajo el swing; objetivo, el máximo previo o 1:2.",
     "Pasos: (1) confirma tendencia alcista en temporalidad alta (máximos/mínimos crecientes, "
     "precio sobre EMA50). (2) Espera el pullback a la EMA20/50 (zona de valor). (3) Entra con "
     "confirmación (envolvente, martillo, CHoCH menor a favor). (4) Stop bajo el mínimo del "
     "retroceso; toma parcial en 1:1 y deja correr con trailing. Funciona en CUALQUIER mercado "
     "con tendencia; ajusta la EMA y el stop al ATR del activo."),

    ("Estrategia: ruptura de rango con retest",
     "Estrategia de ruptura (todos los mercados): cuando el precio rompe un rango o nivel clave "
     "con volumen, no entres a ciegas; espera el RETEST del nivel roto (ahora soporte/resistencia) "
     "y entra en la confirmación. Reduce las falsas rupturas y mejora el riesgo/beneficio.",
     "Pasos: (1) marca el rango/nivel y espera CIERRE fuera con volumen. (2) Deja que el precio "
     "vuelva a testear el nivel roto. (3) Entra si el nivel aguanta (vela de rechazo) en la "
     "dirección de la ruptura. (4) Stop al otro lado del nivel; objetivo = altura del rango "
     "proyectada. Evita rupturas sin volumen o contra la tendencia superior (suelen ser trampas)."),

    ("Estrategia: reversión en zona con divergencia",
     "Estrategia de reversión a la media (mejor en rango): en una zona de soporte/resistencia o "
     "sobre-extensión, busca una DIVERGENCIA (RSI/MACD) más una vela de rechazo para operar el "
     "giro. Ideal en mercados laterales o extremos; peligrosa contra tendencia fuerte.",
     "Pasos: (1) precio llega a zona clave y muestra agotamiento (mecha larga, divergencia "
     "regular). (2) Confirma con vela de giro (pin bar, envolvente). (3) Entra contra el "
     "movimiento extendido; stop más allá del extremo/mecha. (4) Objetivo: la media o el otro "
     "lado del rango. Filtra con ADX bajo (rango). NO la uses contra una tendencia con ADX alto."),

    ("Estrategia: barrido de liquidez + CHoCH (SMC)",
     "Estrategia de dinero inteligente: espera un BARRIDO de liquidez (falsa ruptura de un máximo/"
     "mínimo obvio que caza stops) seguido de un CHoCH (cambio de estructura). Entra en la "
     "dirección del giro, con stop más allá del barrido. Muy precisa en forex, cripto e índices.",
     "Pasos: (1) identifica liquidez (máximos/mínimos iguales, stops evidentes). (2) El precio "
     "barre esa zona con mecha y vuelve dentro. (3) Confirma con CHoCH en temporalidad menor "
     "(rompe la microestructura contraria). (4) Entra en el order block/FVG de origen; stop tras "
     "el barrido; objetivo, la liquidez opuesta. Combina liquidez, estructura y desequilibrios."),

    ("Estrategia: VWAP bounce intradía",
     "Estrategia intradía (índices, acciones, cripto, forex): en tendencia del día, los retrocesos "
     "al VWAP son reentradas a favor. Precio sobre VWAP = buscar compras en el toque; bajo VWAP = "
     "buscar ventas. Muy usada por institucionales para day trading y scalping.",
     "Pasos: (1) define el sesgo del día (precio sobre/bajo VWAP y apertura). (2) Espera el "
     "retroceso al VWAP dentro de la tendencia. (3) Entra con confirmación (vela de rechazo en el "
     "VWAP). (4) Stop al otro lado del VWAP; objetivo, el extremo del día o banda de desviación. "
     "En rango, el precio oscila alrededor del VWAP (reversión). Requiere buena liquidez de sesión."),

    ("Estrategia: ruptura del rango de apertura (ORB)",
     "Opening Range Breakout (índices y acciones sobre todo): marca el rango de los primeros 15-30 "
     "min tras la apertura; opera la ruptura de ese rango en la dirección del impulso, con el otro "
     "extremo como stop. Aprovecha la volatilidad y el volumen de la apertura.",
     "Pasos: (1) delimita máximo y mínimo del rango de apertura. (2) Entra al romper con volumen "
     "hacia arriba (largo) o hacia abajo (corto). (3) Stop en el lado opuesto del rango; objetivo "
     "= altura del rango o niveles del día previo. Filtra con la tendencia mayor y evita días de "
     "noticias que distorsionan. Aplicable al 'rango asiático' en forex."),

    ("Estrategia: confluencia Fibonacci + order block",
     "Entrada de alta probabilidad (todos los mercados): busca que un retroceso de Fibonacci "
     "(50-61.8%) coincida con un order block o zona de demanda/oferta y con la tendencia superior. "
     "La CONFLUENCIA de varios factores en el mismo punto multiplica la fiabilidad.",
     "Pasos: (1) traza Fibonacci del impulso. (2) Marca order blocks/zonas en la región 50-61.8%. "
     "(3) Si coinciden con la tendencia alta y un nivel previo, es zona premium. (4) Espera "
     "confirmación (vela/CHoCH) y entra; stop tras la zona; objetivo, la extensión o liquidez "
     "opuesta. Cuantos más factores se alinean, mayor probabilidad y mejor riesgo/beneficio."),

    ("Estrategia binarias: pin bar en nivel",
     "Para opciones binarias de corto plazo: opera un rechazo claro (pin bar/martillo/estrella "
     "fugaz) en un nivel fuerte (soporte/resistencia/VWAP) a favor de la tendencia superior, con "
     "un vencimiento de 1-3 velas. Entra tras el CIERRE de la vela de rechazo, no antes.",
     "Reglas: (1) nivel de calidad + tendencia mayor a favor. (2) vela de rechazo con mecha "
     "dominante en el nivel. (3) vencimiento acorde (1-3 velas de la temporalidad analizada). (4) "
     "evita noticias de alto impacto y horas de baja liquidez. Recuerda el punto de equilibrio del "
     "payout: necesitas ventaja real y gestión estricta; no persigas con martingala."),

    ("Mercado: criptomonedas (BTC, ETH, altcoins)",
     "Cripto (Bitcoin BTC, Ethereum ETH, Solana, altcoins) opera 24/7 con ALTA volatilidad. La "
     "DOMINANCIA de BTC guía al resto: si BTC cae, las altcoins suelen caer más. Muy sensible a "
     "sentimiento, funding y liquidaciones. Fines de semana con menor liquidez y movimientos bruscos.",
     "Claves: vigila BTC antes de operar altcoins (correlación alta); el 'funding' extremo y las "
     "liquidaciones en cascada provocan mechas violentas y barridos de liquidez. Usa stops más "
     "amplios por la volatilidad (ATR alto) y tamaño menor. Los niveles redondos (20k, 50k, 100k) "
     "son imanes psicológicos. Entorno risk-on favorece cripto; risk-off la castiga."),

    ("Mercado: forex (pares de divisas)",
     "Forex (EUR/USD, GBP/USD, USD/JPY, cross como EUR/JPY) se mueve por sesiones y por el dólar "
     "(DXY). Mayor volatilidad en el solape Londres-Nueva York. Muy sensible a bancos centrales "
     "(Fed, BCE, BoJ), tipos de interés y datos macro (NFP, IPC).",
     "Claves: DXY fuerte suele empujar EUR/USD y GBP/USD a la baja y viceversa (correlación "
     "inversa). Opera los mayores en su sesión para spreads estrechos. Evita operar en el minuto "
     "de una noticia de alto impacto (latigazos y spreads amplios). Los cross (sin USD) tienen su "
     "propia dinámica. El carry (diferencial de tipos) marca sesgos de fondo de medio plazo."),

    ("Mercado: índices bursátiles (S&P, Nasdaq, Dow)",
     "Índices (S&P 500/SPY, Nasdaq 100/QQQ, Dow/DIA) reflejan el conjunto del mercado de acciones. "
     "Gran actividad en la apertura de Nueva York. Sensibles a tipos de interés, bonos y al VIX "
     "(índice del miedo): VIX alto = miedo y caídas; VIX bajo = complacencia.",
     "Claves: la apertura de Wall Street genera gaps y volatilidad (útil para ORB). El Nasdaq "
     "(tecnología) es más volátil y sensible a tipos que el Dow. Subidas de tipos suelen presionar "
     "a la baja (sobre todo tech). Correlación fuerte entre índices: confírmalos entre sí. Vigila "
     "el VIX como termómetro de riesgo y los rendimientos de bonos."),

    ("Mercado: metales (oro y plata)",
     "Oro (gold) y plata (silver) son refugio de valor. El oro se mueve INVERSO al dólar y a los "
     "tipos de interés reales, y sube con el miedo/geopolítica e inflación. La plata es más "
     "volátil (componente industrial). Metales preciosos = protección en entornos risk-off.",
     "Claves: dólar (DXY) débil y tipos reales a la baja impulsan el oro; lo contrario lo frena. "
     "El oro rompe al alza en crisis y tensión geopolítica. La plata amplifica los movimientos del "
     "oro (mayor beta) pero con más ruido. Vigila la relación oro/plata y los rendimientos reales. "
     "Niveles psicológicos redondos (2000, 3000 en oro) son relevantes."),

    ("Mercado: petróleo (WTI/Brent)",
     "El petróleo (WTI, Brent) se rige por OFERTA y DEMANDA global: decisiones de la OPEP+, "
     "inventarios semanales (EIA en EE. UU.), crecimiento económico y geopolítica. Muy volátil "
     "ante titulares. Estacionalidad (temporada de conducción, invierno) influye en la demanda.",
     "Claves: los inventarios semanales de la EIA mueven el precio con fuerza (evita operar en el "
     "dato). Recortes de la OPEP+ tienden a subir el precio; recesión y dólar fuerte lo bajan. "
     "Respeta niveles técnicos claros porque atraen a muchos operadores. Tensión geopolítica en "
     "zonas productoras dispara la volatilidad. Ajusta stops al ATR (el crudo se mueve mucho)."),

    ("Mercado: acciones individuales",
     "Acciones (Apple, Microsoft, Tesla, Nvidia, Amazon…) se mueven por resultados (earnings), "
     "guidance, sector y su BETA respecto al índice. Los earnings provocan gaps enormes; el "
     "guidance (previsión) suele importar más que el dato pasado. Correlacionan con su índice.",
     "Claves: evita mantener posiciones sobre un earnings salvo que sea tu estrategia (riesgo de "
     "gap). Una acción de beta alta (Tesla, Nvidia) amplifica los movimientos del índice. La "
     "fuerza relativa (la acción sube más que su índice) señala liderazgo. Vigila el sector y las "
     "noticias de la empresa. Los gaps de apertura ofrecen setups (continuación o cierre de gap)."),

    ("Aplica tu método en TODOS los mercados",
     "Los principios técnicos (tendencia, soporte/resistencia, estructura, gestión de riesgo) son "
     "UNIVERSALES: valen en cripto, forex, índices, metales, petróleo y acciones. Lo que cambia es "
     "el contexto: horario, liquidez, volatilidad (ATR) y catalizadores propios de cada mercado.",
     "Adapta, no reinventes: usa la misma jerarquía (tendencia superior → zona → gatillo → gestión) "
     "en cualquier activo, pero ajusta el stop al ATR del mercado, opera en sus horas líquidas y "
     "respeta sus catalizadores (noticias macro en forex/índices, inventarios en petróleo, earnings "
     "en acciones, dominancia BTC en cripto). Un buen operador aplica el MISMO método disciplinado "
     "en todos los mercados, calibrado a cada uno."),

    ("Fuerza relativa (relative strength)",
     "La fuerza relativa compara un activo con su índice/sector o con otro activo: el que SUBE MÁS "
     "(o cae menos) es el más fuerte. En una subida general, compra los líderes (mayor fuerza "
     "relativa); en caídas, los más débiles caen más. Útil para elegir el MEJOR activo.",
     "Ejemplos: si el S&P sube y una acción sube más, tiene fuerza relativa positiva (candidata "
     "a largo). En cripto, mide altcoins frente a BTC. La fuerza relativa anticipa: los líderes "
     "suelen romper antes. No confundir con el índice RSI. Opera los fuertes al alza y los débiles "
     "a la baja para maximizar probabilidad y aprovechar la rotación de capital."),

    ("Perfil de volumen y área de valor",
     "El Volume Profile muestra CUÁNTO volumen se negoció en cada nivel de precio (no en el tiempo). "
     "El nivel de mayor volumen (POC, punto de control) y el área de valor (donde ocurrió el ~70% "
     "del volumen) actúan como imanes y como soporte/resistencia potentes.",
     "Los precios con mucho volumen (alto valor) atraen al precio (reversión a la media); las zonas "
     "de bajo volumen se cruzan rápido (movimientos veloces). El POC del día/semana previo es un "
     "nivel clave para reentradas y objetivos. Operar en el borde del área de valor con rechazo, o "
     "la ruptura fuera de ella, ofrece setups de alta calidad. Complementa al VWAP y a los niveles."),

    ("VWAP anclado (anchored VWAP)",
     "El VWAP anclado se calcula desde un EVENTO clave (un máximo/mínimo importante, un earnings, el "
     "inicio de un movimiento) en lugar de solo el día. Muestra el precio medio de todos los que "
     "entraron desde ese punto y actúa como soporte/resistencia dinámico de referencia.",
     "Ancla el VWAP a un pivote relevante para ver si los compradores desde ese evento van en "
     "ganancia (precio sobre el aVWAP) o pérdida (por debajo). El aVWAP desde un suelo importante "
     "suele actuar como soporte en tendencia alcista. Muy útil para juzgar la salud de un movimiento "
     "y para fijar entradas/objetivos en cualquier mercado con volumen fiable."),

    ("Estacionalidad y patrones de calendario",
     "Algunos activos muestran sesgos estacionales estadísticos: tendencias por meses/épocas ('sell "
     "in May', rally de fin de año en bolsa, demanda de gasolina en verano para el crudo, refugio "
     "en oro en incertidumbre). Son PROBABILIDADES históricas, no certezas.",
     "Úsalos como contexto de fondo, no como señal aislada: refuerzan una tesis técnica pero no la "
     "sustituyen. Efectos intradía también existen (mayor volatilidad en aperturas y solapes de "
     "sesión). Combina la estacionalidad con la estructura actual del precio; si ambas coinciden, "
     "la probabilidad mejora. Verifica siempre con datos y no operes 'solo por el calendario'."),

    ("Squeeze de volatilidad (Bollinger + Keltner)",
     "Cuando las Bandas de Bollinger se meten DENTRO de los canales de Keltner, la volatilidad está "
     "comprimida al máximo ('squeeze', TTM Squeeze): suele preceder a un movimiento explosivo. La "
     "compresión no dice la dirección; la ruptura sí.",
     "Detecta el squeeze (baja volatilidad, rango estrecho) y prepárate para la expansión. Opera la "
     "RUPTURA en la dirección confirmada (con volumen y a favor de la tendencia superior), no "
     "adivines antes. Tras la expansión, la volatilidad se normaliza. Funciona en todos los "
     "mercados y temporalidades; es una de las mejores señales de 'movimiento inminente'."),

    ("Killzones: horas de mayor probabilidad",
     "No todas las horas son iguales. Las 'killzones' (aperturas de Londres y Nueva York en forex/"
     "índices, apertura de Wall Street para acciones) concentran volumen, volatilidad y los "
     "movimientos direccionales del día. Operar en horas muertas da rango sucio y falsas señales.",
     "Enfoca tus operaciones en las ventanas de mayor liquidez: solape Londres-NY (aprox. 13:00-"
     "16:00 UTC) para forex e índices; la primera y última hora de Wall Street para acciones. "
     "Cripto opera 24/7 pero también tiene picos ligados a esas sesiones. Fuera de esas ventanas, "
     "reduce actividad. Alinear la señal con la hora correcta mejora la probabilidad."),

    ("Gestión de riesgo por clase de activo",
     "Cada mercado tiene su volatilidad: un stop que sirve para EUR/USD es demasiado ajustado para "
     "Bitcoin o el petróleo. Ajusta SIEMPRE el stop y el tamaño al ATR del activo para que el "
     "riesgo en dinero sea constante, sin importar el mercado.",
     "Cripto y petróleo (ATR alto) exigen stops más amplios y tamaño menor; forex mayor (ATR "
     "moderado) permite stops más ceñidos. Nunca uses el mismo número de 'pips/puntos' fijo en "
     "todos. Mantén el riesgo por operación en 1-2% del capital calculando el tamaño desde la "
     "distancia al stop. Así operas cualquier mercado con riesgo homogéneo y controlado."),

    ("Confirmación por volumen y absorción",
     "El volumen valida el movimiento en cualquier mercado: rupturas y tendencias con volumen "
     "creciente son fiables; con volumen decreciente, sospechosas. La ABSORCIÓN (mucho volumen sin "
     "que el precio avance) revela que un lado está frenando al otro: posible giro.",
     "Señales: ruptura con volumen alto = probable continuación; clímax de volumen en un extremo = "
     "posible agotamiento y giro. En acciones/índices el volumen es fiable; en forex (descentralizado) "
     "se usa el tick volume como aproximación; en cripto el volumen de exchange. La divergencia de "
     "volumen (precio sube, volumen baja) avisa de debilidad. Usa el volumen para confirmar, no como "
     "señal única."),

    ("El plan de trading escrito",
     "Un plan de trading escrito define: qué mercados operas, en qué horario, con qué estrategias y "
     "temporalidades, cuánto riesgas por operación y al día, y tus reglas de entrada/salida. Operar "
     "sin plan es improvisar; el plan convierte la disciplina en un proceso repetible.",
     "Un buen plan incluye: objetivos realistas, activos y sesiones, checklist de entrada, gestión "
     "(riesgo 1-2%, límite de pérdida diaria), reglas de gestión de la operación y un diario para "
     "revisar. El sistema automatizado ES un plan: reglas objetivas, sin emoción, aplicadas por "
     "igual en todos los mercados. Sigue el plan; cámbialo con datos, no con impulsos."),

    ("Cómo combinar todo: la jerarquía de decisión",
     "Integra el conocimiento en una jerarquía: (1) TENDENCIA/contexto de fondo (temporalidad alta y "
     "años); (2) ZONA de interés (soporte/resistencia, order block, Fibonacci, VWAP); (3) GATILLO "
     "(vela de confirmación, CHoCH, divergencia); (4) GESTIÓN (riesgo, stop por ATR, objetivos).",
     "Ninguna señal aislada basta: la fiabilidad nace de la CONFLUENCIA de los cuatro niveles a "
     "favor. Primero define la dirección de fondo, luego dónde (zona), luego cuándo (gatillo) y "
     "cuánto (gestión). Si algún nivel falla o se contradice, ESPERA. Este mismo marco se aplica a "
     "cripto, forex, índices, metales, petróleo y acciones: cambia el calibrado, no el método."),
]

# ---- LOTE 4: order flow, macro intermercado, gestión de cartera y métricas ----
_BATCH4: list[tuple[str, str, str]] = [
    ("Premium y descuento (equilibrio SMC)",
     "Divide un rango o impulso por su 50% (equilibrio): por encima es PREMIUM (caro, zona para "
     "vender), por debajo es DESCUENTO (barato, zona para comprar). En tendencia alcista busca "
     "compras en descuento; en bajista, ventas en premium. Evita comprar caro y vender barato.",
     "El precio justo es el 50% del rango relevante. Un operador profesional solo compra en la "
     "mitad inferior (descuento) y vende en la superior (premium), a favor de la tendencia de "
     "fondo. Combina el descuento con order blocks y Fibonacci (61.8%) para entradas óptimas. "
     "Vale en todos los mercados: define primero el rango correcto (del swing de la temporalidad alta)."),

    ("Optimal Trade Entry (OTE)",
     "El OTE es la zona de retroceso del 62-79% de un impulso (Fibonacci), donde entrar a favor de "
     "la tendencia ofrece el mejor riesgo/beneficio: stop pequeño (tras el 79%) y objetivo grande "
     "(la extensión). Es la 'zona premium' de entrada del dinero inteligente.",
     "Traza Fibonacci del impulso; el OTE (62-79%) suele coincidir con order blocks y desequilibrios "
     "sin rellenar. Espera confirmación (vela de rechazo, CHoCH menor) dentro de esa zona. El stop "
     "va justo tras el retroceso profundo; los objetivos, en la liquidez o extensiones (-0.27, "
     "-0.62). Da ratios 1:3 o mejores. Aplícalo en cualquier activo con un impulso claro."),

    ("Breaker block",
     "Un breaker block es un order block que FALLÓ: el precio lo rompió y luego lo usa en sentido "
     "contrario como soporte/resistencia. Marca un cambio de control. Se opera el retest del "
     "breaker tras un cambio de estructura (BOS/CHoCH) confirmado.",
     "Ejemplo alcista: tras un barrido de mínimos y un CHoCH al alza, el último order block bajista "
     "que fue superado se convierte en soporte (breaker): busca compras en su retest. Refleja el "
     "atrapamiento de quienes entraron mal. Combínalo con liquidez y desequilibrios. Es una "
     "reentrada de precisión válida en forex, cripto e índices."),

    ("Inducement (liquidez trampa)",
     "El 'inducement' es liquidez señuelo: un mínimo/máximo menor evidente que ATRAE a los "
     "operadores a entrar antes de la zona institucional real, para luego barrerlos. Reconocerlo "
     "evita entradas prematuras y te alinea con el movimiento verdadero.",
     "Antes de un order block válido suele haber un pequeño swing que 'induce' entradas; el precio "
     "toma esa liquidez y recién entonces reacciona en la zona real. Práctica: no entres en el "
     "primer nivel obvio; espera a que se barra el inducement y el precio llegue a la zona de "
     "origen con confirmación. Filtra muchas trampas y falsas señales en todos los mercados."),

    ("Displacement (vela de desplazamiento)",
     "Un displacement es un movimiento fuerte, rápido y direccional (velas amplias) que revela "
     "INTENCIÓN institucional y suele dejar un fair value gap. Confirma que un nivel importa y "
     "marca la dirección probable siguiente. Sin displacement, la señal es débil.",
     "Tras un barrido de liquidez o en un nivel clave, un desplazamiento con cierre convincente "
     "(no solo mecha) valida el giro/continuación y crea el desequilibrio al que el precio volverá. "
     "Úsalo como filtro de calidad: opera reentradas hacia el FVG/order block que dejó el "
     "displacement. Distingue un movimiento con convicción de un simple ruido de rango."),

    ("Draw on liquidity (objetivo del precio)",
     "El mercado se mueve buscando LIQUIDEZ: máximos y mínimos previos, dobles techos/suelos y "
     "números redondos son 'imanes' hacia donde el precio tiende a ir. Definir el próximo objetivo "
     "de liquidez da el sesgo direccional del día/semana.",
     "Pregúntate: ¿dónde está la liquidez obvia? Ahí suele dirigirse el precio. En tendencia "
     "alcista, el objetivo son los máximos previos (liquidez de compradores en corto); en bajista, "
     "los mínimos. Usa esta 'atracción' para fijar objetivos realistas y para entender por qué el "
     "precio barre un nivel antes de girar. Marco válido en todos los mercados."),

    ("Rango diario promedio (ADR/ATR diario)",
     "El ADR (rango diario promedio) o el ATR diario indican cuánto suele moverse un activo por día. "
     "Sirve para fijar objetivos realistas y saber si el movimiento del día ya está 'agotado' "
     "(cerca de completar su rango) o si aún le queda recorrido.",
     "Si un activo recorre de media 100 puntos al día y ya lleva 90, perseguir la ruptura tiene "
     "poco recorrido restante y más riesgo de reversión a la media. Al inicio del día, con poco "
     "rango consumido, hay margen para tendencia. Ajusta stops y objetivos al ADR de CADA mercado "
     "(cripto y petróleo mueven mucho más que un par forex tranquilo)."),

    ("Order book y profundidad de mercado (DOM)",
     "El libro de órdenes (order book/DOM) muestra las órdenes límite de compra y venta en cada "
     "nivel. Grandes muros de órdenes actúan como soporte/resistencia temporal. El precio tiende a "
     "moverse hacia donde hay más liquidez que ejecutar.",
     "Cuidado: parte de la liquidez visible puede ser 'spoofing' (órdenes falsas que se retiran). "
     "La absorción (muchas órdenes de mercado chocando contra un muro sin mover el precio) revela "
     "fuerza de un lado. En mercados centralizados (acciones, futuros, cripto) el DOM es visible; "
     "en forex es fragmentado. Úsalo como contexto de corto plazo, no como señal aislada."),

    ("Order flow: delta y absorción",
     "El order flow mide la agresión: delta = volumen comprador de mercado menos vendedor. Delta "
     "positivo fuerte = compradores agresivos. La ABSORCIÓN ocurre cuando hay mucha agresión pero "
     "el precio no avanza: alguien grande está absorbiendo con órdenes límite (posible giro).",
     "El delta acumulado (cumulative delta) que diverge del precio (precio sube pero delta baja) "
     "avisa de debilidad, como una divergencia de momentum. La absorción en un nivel (agresión "
     "vendedora que no baja el precio) suele preceder a un rebote. Es lectura fina de futuros/"
     "acciones/cripto; el principio (quién domina la agresión) refuerza cualquier análisis."),

    ("Análisis intermercado (dólar, bonos, materias, acciones)",
     "Los mercados están enlazados (teoría intermercado de Murphy): dólar, bonos, materias primas y "
     "acciones se influyen. Un dólar fuerte presiona materias y emergentes; bonos y acciones y "
     "tipos se mueven en relación. Leer el conjunto mejora las decisiones en cada activo.",
     "Relaciones típicas: dólar (DXY) inverso a oro y a muchas materias; subida de rendimientos de "
     "bonos suele presionar a las acciones de crecimiento (tech); materias al alza pueden anticipar "
     "inflación. Antes de operar un activo, mira su 'entorno': confirma tu tesis con los mercados "
     "relacionados. La confluencia intermercado da sesgos más fiables."),

    ("Rendimientos de bonos y curva de tipos",
     "Los rendimientos de los bonos y la curva de tipos son la brújula macro. Subida de tipos/"
     "rendimientos suele castigar a las acciones de crecimiento (tech/Nasdaq) y apoyar al dólar. "
     "Una curva invertida (corto plazo rinde más que largo) suele anticipar recesión.",
     "Los tipos de interés reales (nominal menos inflación) guían al oro (tipos reales altos = oro "
     "débil). Las decisiones de la Fed/BCE mueven todo el complejo. Aunque operes intradía, conocer "
     "el sesgo de tipos evita operar contra la marea macro. Es contexto de fondo que se aplica a "
     "índices, forex, metales y acciones."),

    ("Ciclo económico y rotación sectorial",
     "La economía se mueve en ciclos (expansión, pico, contracción, recuperación) y el capital ROTA "
     "entre sectores según la fase: tecnología y consumo discrecional lideran en expansión; "
     "servicios básicos, salud y utilities resisten en contracción; energía y materiales en "
     "inflación.",
     "Saber la fase del ciclo ayuda a elegir QUÉ operar al alza o a la baja. En 'risk-on' (expansión) "
     "brillan crecimiento, cripto e índices; en 'risk-off' (contracción/miedo) se busca refugio "
     "(dólar, oro, bonos, defensivos). La rotación se ve en la fuerza relativa de los sectores. "
     "Alinear el activo con la fase del ciclo mejora la probabilidad de fondo."),

    ("Risk-on / risk-off en profundidad",
     "En 'risk-on' (apetito por el riesgo) suben acciones, cripto, divisas de materias (AUD, NZD) y "
     "caen los refugios. En 'risk-off' (aversión) sube el dólar, el yen, el oro y los bonos, y caen "
     "acciones y cripto. Identificar el régimen orienta TODAS tus operaciones.",
     "Termómetros del régimen: el VIX (alto = risk-off), los rendimientos de bonos, el oro y el "
     "dólar. En risk-off, ser comprador de cripto o acciones va contra la corriente. Antes de "
     "operar, define si el mercado está en risk-on o risk-off y opera a favor: es un filtro de "
     "fondo que reduce operaciones perdedoras en cualquier activo."),

    ("Volatilidad implícita, realizada y VIX",
     "La volatilidad implícita (esperada por las opciones, VIX) suele ser mayor que la realizada "
     "(la que ocurre). VIX alto = miedo, movimientos amplios; VIX bajo = calma/complacencia. "
     "Picos de VIX suelen coincidir con suelos del mercado (pánico = oportunidad).",
     "La volatilidad es cíclica: tras compresión (baja vol) viene expansión y viceversa. En vol "
     "alta, amplía stops y reduce tamaño; en vol baja, prepárate para rupturas (squeeze). El VIX "
     "extremo (>30-40) marca capitulación y posibles rebotes; VIX muy bajo, complacencia y riesgo "
     "de giro. La gestión debe adaptarse al régimen de volatilidad, no ignorarlo."),

    ("Riesgo de cartera y correlación",
     "El riesgo no es por operación aislada sino AGREGADO: abrir varias posiciones correlacionadas "
     "(p.ej. largo en EUR/USD y en GBP/USD, o en varias altcoins) es casi la misma apuesta con "
     "riesgo multiplicado. Controla la exposición total, no solo el riesgo por trade.",
     "Suma el riesgo de todas las posiciones abiertas ('heat' de la cuenta) y ponle un tope (p.ej. "
     "máximo 4-6% en riesgo a la vez). Diversifica en activos poco correlacionados o reduce el "
     "tamaño si están correlacionados. Una noticia adversa puede mover todo un bloque a la vez. "
     "Pensar en cartera, no en operaciones sueltas, evita ruinas por concentración."),

    ("Estilos de trading: scalping, day, swing",
     "Elige un estilo acorde a tu tiempo y carácter. Scalping: muchas operaciones de segundos/"
     "minutos, alta concentración, costes importan mucho. Day trading: intradía, cierras en el día. "
     "Swing: operaciones de días/semanas, menos ruido, más paciencia.",
     "El scalping exige spreads mínimos, ejecución rápida y disciplina férrea; el swing tolera más "
     "ruido pero requiere aguantar oscilaciones y usar temporalidades altas. No mezcles estilos en "
     "la misma operación (entrar como scalper y quedarte como swing por miedo es un error clásico). "
     "Define tu estilo, su temporalidad y sus reglas, y sé coherente en todos los mercados."),

    ("Detectar el agotamiento de una tendencia",
     "Señales de que una tendencia se agota: clímax de volumen (pico extremo), velas de reversión "
     "en un extremo, divergencias múltiples en osciladores, alcance del rango diario/objetivo de "
     "liquidez, y pérdida de la estructura (CHoCH). Avisan de tomar beneficios o esperar giro.",
     "Ninguna señal aislada basta; busca CONFLUENCIA de agotamiento. Una tendencia extendida y "
     "sobre-extendida (lejos de la media, tras un impulso parabólico) es más vulnerable. No "
     "'shortees' techos ni 'compres' suelos solo por estar extendido: espera confirmación de giro "
     "(barrido + CHoCH, vela de reversión con volumen). Aplica igual en cripto, forex e índices."),

    ("Ruptura falsa vs verdadera",
     "Distinguir una ruptura real de una falsa (fakeout) es clave. Verdadera: cierre convincente "
     "fuera del nivel, con volumen, a favor de la tendencia, y aguanta el retest. Falsa: mecha que "
     "supera el nivel pero cierra dentro, sin volumen, contra la tendencia; suele revertir rápido.",
     "Filtros: exige CIERRE (no mecha) fuera del nivel; confirma con volumen/displacement; valora el "
     "contexto (rupturas a favor de la tendencia mayor son más fiables). El retest exitoso confirma; "
     "la vuelta rápida dentro del rango delata la trampa (y ofrece operar el rechazo). En rangos y "
     "cerca de liquidez obvia abundan las falsas rupturas: paciencia antes de perseguir."),

    ("Métricas de rendimiento del sistema",
     "Mide tu sistema con datos, no sensaciones: tasa de acierto, ratio riesgo/beneficio, "
     "EXPECTATIVA (ganancia media por operación), PROFIT FACTOR (ganancias brutas / pérdidas "
     "brutas, >1 es rentable), drawdown máximo y ratio de Sharpe (retorno ajustado a riesgo).",
     "Un profit factor >1.5 y expectativa positiva sostenida indican ventaja real. Vigila también "
     "MAE/MFE (excursión adversa/favorable máxima) para afinar stops y objetivos. No juzgues por "
     "unas pocas operaciones: se necesita muestra amplia. Estas métricas, aplicadas a los resultados "
     "reales en todos los mercados, dicen si el sistema tiene 'edge' o hay que corregirlo."),

    ("Gestión emocional avanzada (tilt, FOMO)",
     "El 'tilt' (operar alterado tras una pérdida o racha) y el FOMO (miedo a quedarse fuera, "
     "perseguir el precio) destruyen cuentas. La codicia hace arriesgar de más; el miedo cierra "
     "ganancias pronto. Reconocer el estado emocional y PARAR a tiempo es una habilidad clave.",
     "Reglas anti-tilt: límite de pérdida diaria (al alcanzarlo, se cierra la jornada); pausa tras "
     "2-3 pérdidas seguidas; nunca aumentar el tamaño para 'recuperar' (revenge trading). Contra el "
     "FOMO: si perdiste la entrada, espera el siguiente setup, no persigas. El sistema automatizado "
     "ayuda porque quita la emoción: sigue sus reglas incluso cuando 'sientes' otra cosa."),

    ("Pensar en probabilidades y series",
     "Cada operación es UNA de una serie larga: el resultado individual (ganar o perder) no valida "
     "ni invalida el sistema. Con ventaja positiva, basta ejecutar consistentemente y dejar que la "
     "probabilidad actúe en el conjunto. Un acierto no te hace genio ni un fallo, un inútil.",
     "El error mental típico es sobrerreaccionar a la última operación (euforia o frustración) y "
     "romper el plan. Piensa como un casino: no importa una mano, importa la esperanza sobre miles. "
     "Acepta que perderás un % de las veces AUNQUE hagas todo bien. La consistencia en el proceso, "
     "no el resultado puntual, produce rentabilidad en todos los mercados."),

    ("Gestión de noticias y eventos",
     "Ante datos de alto impacto (tipos, NFP, IPC, earnings, inventarios) hay tres tácticas: (1) "
     "EVITAR: no operar en el impacto (lo más prudente); (2) esperar el RETEST tras la reacción y "
     "operar la nueva tendencia; (3) straddle: colocar órdenes a ambos lados (avanzado y arriesgado).",
     "En el minuto del dato, spreads se disparan, hay slippage y latigazos: la mayoría debe evitarlo. "
     "Lo profesional suele ser dejar que el mercado reaccione y 'digiera' la noticia, y luego operar "
     "el retest de la ruptura con la tendencia resultante. Marca los eventos del día en el calendario "
     "económico y no te dejes sorprender con posiciones abiertas de corto plazo."),

    ("La ventaja (edge) es lo primero",
     "Sin una VENTAJA real (una razón estadística por la que ganas más de lo que pierdes a largo "
     "plazo), ninguna gestión de riesgo ni psicología te salva: solo alargan la pérdida. Primero "
     "demuestra el edge (backtest + resultados reales), luego optimiza gestión y ejecución.",
     "La ventaja puede venir de un patrón con esperanza positiva, de leer mejor el contexto "
     "(multi-temporalidad, confluencia) o de una ejecución disciplinada donde otros fallan. Se mide "
     "con expectativa y profit factor positivos y sostenidos. Protégela: no la diluyas con "
     "over-trading, ni la rompas saltándote las reglas. El edge + gestión + disciplina = "
     "rentabilidad consistente en cualquier mercado."),
]

# ---- LOTE 5: patrones avanzados, indicadores de volumen, canales, internos y macro ----
_BATCH5: list[tuple[str, str, str]] = [
    ("Patrones de cuña (wedge)",
     "La cuña es un patrón de líneas convergentes inclinadas. Cuña ASCENDENTE (dos rectas al "
     "alza que se estrechan) suele ser BAJISTA (agotamiento comprador). Cuña DESCENDENTE (dos "
     "rectas a la baja que convergen) suele ser ALCISTA. Se opera la ruptura confirmada.",
     "Una cuña ascendente en tendencia alcista avisa de pérdida de impulso: al romper el soporte "
     "inferior, giro bajista. La descendente en tendencia bajista anticipa rebote al romper la "
     "resistencia superior. Objetivo aproximado: la altura de la cuña. Confirma con volumen "
     "decreciente dentro del patrón y creciente en la ruptura. Válida en todos los mercados."),

    ("Rectángulo y taza con asa",
     "El rectángulo es un rango horizontal (consolidación) que se opera en la ruptura de su techo "
     "o suelo. La 'taza con asa' (cup and handle) es un patrón alcista de continuación: una base "
     "redondeada (taza) seguida de un pequeño retroceso (asa) antes de romper al alza.",
     "En el rectángulo, el objetivo tras la ruptura es la altura del rango proyectada. En la taza "
     "con asa, la ruptura de la resistencia del asa con volumen confirma continuación alcista; "
     "objetivo = profundidad de la taza. Ambos requieren cierre con volumen y ganan fiabilidad a "
     "favor de la tendencia previa. Frecuentes en acciones e índices, útiles en cualquier activo."),

    ("Patrones armónicos (Gartley, Bat, Butterfly, Crab)",
     "Los patrones armónicos usan proporciones de Fibonacci para anticipar zonas de giro. Gartley, "
     "Bat, Butterfly y Crab son estructuras de 5 puntos (XABCD) donde el punto D marca una zona de "
     "reversión potencial (PRZ) según ratios concretos. El AB=CD es su base simétrica.",
     "Cada patrón define el punto D por un ratio de Fibonacci del tramo XA (Gartley ~0.786, Bat "
     "~0.886, Butterfly ~1.27, Crab ~1.618). En la PRZ se busca confirmación (vela de rechazo, "
     "divergencia) para operar el giro con stop ajustado tras D. Son precisos pero exigen medición "
     "correcta; combínalos con estructura y niveles. Aplicables a forex, cripto, índices y materias."),

    ("Velas: penetrante, nube oscura y tres dentro/fuera",
     "Línea penetrante (piercing): vela alcista que cierra por encima del punto medio de la roja "
     "previa: giro alcista. Nube oscura (dark cloud cover): su espejo bajista. 'Tres dentro/fuera' "
     "son harami o envolventes con una tercera vela de confirmación del giro.",
     "La penetrante y la nube oscura son giros de dos velas en extremos de tendencia; cuanto más "
     "penetra en el cuerpo previo, más fuerte. 'Tres dentro arriba' = harami alcista confirmado por "
     "una tercera vela verde; 'tres fuera arriba' = envolvente alcista confirmada. La confirmación "
     "en la tercera vela aumenta la fiabilidad. Ganan peso en soporte/resistencia y con volumen."),

    ("Líneas de tendencia y canales",
     "Una línea de tendencia une mínimos crecientes (alcista) o máximos decrecientes (bajista) y "
     "actúa como soporte/resistencia dinámico. Un canal añade una paralela: el precio oscila dentro. "
     "Se opera el rebote en el borde o la RUPTURA del canal con confirmación.",
     "Traza con al menos dos-tres toques válidos; cuantos más toques, más relevante. En un canal "
     "alcista, compra en la base y toma beneficio en el techo; la ruptura del canal avisa de cambio "
     "de ritmo. Evita 'forzar' la línea a tu sesgo. Una línea de tendencia con mucha pendiente es "
     "insostenible. Herramienta universal en todos los mercados y temporalidades."),

    ("Canales de Donchian y sistema Turtle",
     "Los canales de Donchian marcan el máximo y el mínimo de las últimas N velas. El sistema "
     "'Turtle' (tortugas) fue una estrategia famosa de seguimiento de tendencia: comprar la "
     "ruptura del máximo de 20 días y vender la del mínimo, con gestión por volatilidad (ATR).",
     "Es seguimiento de tendencia puro: entras en la ruptura del canal en la dirección del "
     "movimiento y sales con un canal más corto o un múltiplo de ATR. Funciona en mercados con "
     "tendencias sostenidas (materias, cripto, índices) y sufre en rangos (muchas falsas rupturas). "
     "La clave del Turtle fue la GESTIÓN de riesgo y la disciplina, no solo la señal de entrada."),

    ("Parabolic SAR y Supertrend",
     "El Parabolic SAR pone puntos que siguen al precio y sirven de trailing stop: cuando el precio "
     "los cruza, la tendencia se invierte (stop and reverse). El Supertrend usa el ATR para trazar "
     "una línea de tendencia dinámica: precio por encima = alcista; por debajo = bajista.",
     "Ambos son excelentes para SEGUIR tendencias y gestionar salidas, pero dan muchas señales "
     "falsas en rango (whipsaw). Úsalos como trailing stop para dejar correr ganancias y como filtro "
     "de dirección, no como entrada aislada. Combínalos con un filtro de régimen (ADX) para "
     "evitar operarlos en mercados laterales. Válidos en cualquier activo y temporalidad."),

    ("Indicadores de volumen (OBV, MFI, CMF, A/D)",
     "Miden la presión de compra/venta con el volumen. OBV (On Balance Volume) acumula volumen "
     "según el cierre. MFI (Money Flow Index) es un RSI ponderado por volumen (sobrecompra/venta). "
     "Chaikin Money Flow y la línea de Acumulación/Distribución miden si entra o sale dinero.",
     "Su mayor valor son las DIVERGENCIAS: si el precio sube pero el OBV/CMF cae, la subida no "
     "tiene respaldo de volumen (debilidad). Un OBV que rompe su propia tendencia suele adelantar al "
     "precio. El MFI en extremos (>80/<20) marca agotamiento. En forex se usa el tick volume como "
     "aproximación; en acciones/cripto/futuros el volumen es fiable. Confirman, no sustituyen al precio."),

    ("Tipos de gráfico: Heikin Ashi, Renko, Point & Figure",
     "Heikin Ashi suaviza las velas para ver la TENDENCIA con menos ruido (velas del mismo color "
     "seguidas = tendencia sana). Renko dibuja 'ladrillos' por movimiento de precio ignorando el "
     "tiempo. Point & Figure usa columnas de X/O y filtra el ruido, resaltando niveles.",
     "Heikin Ashi ayuda a aguantar tendencias y detectar giros (cambio de color y mechas), pero "
     "oculta el precio real de cierre: no lo uses para fijar entradas exactas. Renko y P&F son "
     "excelentes para ver estructura y soporte/resistencia sin el ruido temporal. Son formas "
     "alternativas de VER el mismo mercado; complementan a las velas japonesas, no las reemplazan."),

    ("Internos del mercado (TICK, TRIN, línea A/D)",
     "Para índices/acciones, los 'internos' miden la amplitud del mercado. El TICK cuenta cuántas "
     "acciones suben menos las que bajan en tiempo real. El TRIN (Arms Index) >1 es bajista, <1 "
     "alcista. La línea Avance/Descenso (A/D) muestra si la subida la sostienen muchas acciones.",
     "Una subida del índice con amplitud DÉBIL (pocas acciones suben, A/D no confirma) es "
     "sospechosa (posible techo). El TICK en extremos (+1000/−1000) marca euforia/pánico intradía. "
     "La divergencia entre el índice y su amplitud avisa de agotamiento. Son herramientas de "
     "day trading de índices que dan contexto de fuerza al conjunto del mercado."),

    ("Sentimiento contrario (put/call, Fear & Greed, COT)",
     "El sentimiento extremo suele ser CONTRARIAN: cuando todos están eufóricos, escasea el "
     "comprador nuevo (techo); en pánico extremo, el vendedor se agota (suelo). El ratio put/call "
     "alto = miedo (alcista contrarian); el índice Fear & Greed y el informe COT miden posicionamiento.",
     "El COT (Commitment of Traders) muestra cómo están posicionados los grandes operadores "
     "(comerciales vs especuladores) en futuros: extremos suelen preceder giros. 'Sé temeroso "
     "cuando otros son codiciosos y codicioso cuando otros temen'. El sentimiento no da timing "
     "exacto: es contexto de fondo que, en extremos, avisa de reversiones en índices, materias y forex."),

    ("Indicadores económicos y su impacto",
     "Los datos macro mueven los mercados: PMI (>50 expansión), empleo (NFP, paro), inflación (IPC/"
     "IPP), PIB y ventas minoristas. Dato mejor de lo esperado suele fortalecer la divisa y, según "
     "el contexto, subir o presionar bolsa (por expectativa de tipos).",
     "Lo que mueve el precio es la SORPRESA frente a lo esperado, no el dato absoluto. Inflación "
     "alta → expectativa de subidas de tipos → dólar fuerte y presión en bolsa/oro. Empleo fuerte "
     "→ economía sólida pero posibles más tipos. Consulta el calendario económico, marca los datos "
     "rojos y evita operar en el impacto. Afecta sobre todo a forex, índices, bonos y metales."),

    ("Política de bancos centrales (hawkish/dovish, QE/QT)",
     "Los bancos centrales (Fed, BCE, BoJ) marcan la marea de fondo. Postura HAWKISH (dura: subir "
     "tipos/retirar estímulo) fortalece la divisa y presiona bolsa y oro. DOVISH (blanda: bajar "
     "tipos/estimular) debilita la divisa y suele impulsar activos de riesgo.",
     "La 'forward guidance' (lo que anticipan hacer) mueve más que la decisión ya esperada. QE "
     "(compra de bonos, inyecta liquidez) es alcista para riesgo; QT (retirada) es restrictivo. El "
     "tono del comunicado y la rueda de prensa disparan volatilidad. Conocer el sesgo del banco "
     "central evita operar contra la política monetaria en forex, índices, bonos y metales."),

    ("Futuros: contango, backwardation y curva",
     "En futuros (materias, VIX) el precio a distintos vencimientos forma una curva. CONTANGO: los "
     "futuros lejanos valen más que el spot (curva ascendente). BACKWARDATION: valen menos (curva "
     "descendente), típico de escasez inmediata. Afecta a los ETF que 'rolan' contratos.",
     "El 'roll yield' erosiona a los ETF de materias en contango (compran caro el siguiente "
     "contrato) y beneficia en backwardation. En el VIX, el contango es lo normal (mercado tranquilo) "
     "y la backwardation aparece en pánico. Entender la curva evita sorpresas al operar productos "
     "basados en futuros (petróleo, gas, VIX) frente al precio 'spot'."),

    ("Carry trade y rollover en forex",
     "El carry trade consiste en comprar una divisa de tipo de interés ALTO financiándose en una de "
     "tipo BAJO, cobrando el diferencial (swap/rollover) por mantener la posición. Funciona en "
     "entornos estables (risk-on) y se deshace bruscamente en risk-off.",
     "Cada día que mantienes la posición abierta cobras o pagas el rollover según el diferencial de "
     "tipos y la dirección. Pares clásicos de carry usan divisas de alto rendimiento contra el yen "
     "o el franco. El riesgo: en episodios de aversión al riesgo, el carry se deshace violentamente "
     "(la divisa de alto tipo se desploma). Es un sesgo de fondo de medio plazo, no una señal intradía."),

    ("Estrategia: turtle soup (falsa ruptura)",
     "La 'turtle soup' opera la REVERSIÓN de una falsa ruptura: cuando el precio rompe un máximo/"
     "mínimo evidente (de ~20 velas) y vuelve rápido dentro del rango, se entra a favor del rechazo. "
     "Aprovecha el barrido de liquidez que atrapa a los que persiguieron la ruptura.",
     "Pasos: (1) identifica un máximo/mínimo obvio (liquidez). (2) el precio lo supera brevemente y "
     "CIERRA de vuelta dentro. (3) entra en la reversión con stop tras el extremo del barrido. (4) "
     "objetivo, el otro lado del rango o la liquidez opuesta. Es la contraparte de la ruptura y una "
     "de las reversiones más fiables. Válida en forex, índices, cripto y materias."),

    ("Pirámide: escalar a favor (scaling in)",
     "Piramidar es AÑADIR a una posición ganadora a medida que la tendencia avanza, no a una "
     "perdedora. Cada añadido es menor que el anterior y el stop del conjunto se sube para proteger. "
     "Maximiza el beneficio en tendencias fuertes sin aumentar el riesgo inicial.",
     "Reglas: añade solo si la operación ya va en ganancia y la estructura lo confirma (nuevo BOS, "
     "pullback a media); mueve el stop para que, en el peor caso, salgas en break-even o pequeña "
     "ganancia. NUNCA promedies a la baja una posición perdedora sin plan (eso es lo contrario y "
     "arruina). Bien hecho, convierte una buena tendencia en una operación excelente."),

    ("Selectividad: operar solo setups A+",
     "No todas las oportunidades valen igual. Clasifica tus setups (A+, B, C) según cuántos factores "
     "de confluencia se alinean y opera SOLO los de máxima calidad. Menos operaciones, pero de mayor "
     "probabilidad y mejor riesgo/beneficio: la selectividad es una ventaja en sí misma.",
     "Un setup A+ reúne: tendencia superior a favor, zona clave, confirmación (gatillo), R/B ≥ 1:2 y "
     "sin eventos de riesgo inminentes. Los B/C se dejan pasar. Esperar el pitch perfecto (como un "
     "bateador) evita el over-trading y eleva la tasa de acierto. La paciencia para no operar "
     "mediocridades distingue al profesional en cualquier mercado."),

    ("Líneas de Andrews (pitchfork) y medianas",
     "El pitchfork de Andrews traza tres líneas paralelas desde tres pivotes: una línea MEDIANA "
     "central y dos paralelas. El precio tiende a gravitar hacia la mediana y a reaccionar en las "
     "paralelas, que actúan como soporte/resistencia dinámicos del canal de tendencia.",
     "La mediana funciona como imán: si el precio no la alcanza, la tendencia es fuerte; si la "
     "supera, puede acelerar. Las paralelas exterior/interior dan zonas de entrada y objetivo dentro "
     "de la tendencia. Es una herramienta geométrica para enmarcar el movimiento y anticipar dónde "
     "reaccionará el precio. Útil en tendencias claras de cualquier mercado."),

    ("Bandas de Keltner y medias Guppy (GMMA)",
     "Los canales de Keltner usan una EMA con bandas basadas en ATR (volatilidad): el precio "
     "'caminando' por la banda superior indica tendencia alcista fuerte. La GMMA (Guppy) superpone "
     "varias EMAs cortas y largas: su separación mide la fuerza y el acuerdo de la tendencia.",
     "Keltner (más suave que Bollinger) filtra el ruido y confirma tendencia; su combinación con "
     "Bollinger define el 'squeeze' de volatilidad. En la GMMA, cuando el grupo de medias cortas se "
     "separa con claridad del grupo largo, la tendencia es robusta; cuando se enredan, hay "
     "indecisión/rango. Ayudan a decidir cuándo seguir tendencia y cuándo esperar, en todos los mercados."),

    ("Backtesting: sesgos y robustez",
     "Un backtest engaña si tiene sesgos: 'look-ahead' (usar datos futuros sin querer), "
     "'survivorship' (probar solo con activos que sobrevivieron) y sobre-optimización (ajustar "
     "parámetros hasta que el pasado brille, pero falla en vivo). Un sistema robusto funciona con "
     "reglas simples y estables.",
     "Valida con datos FUERA de muestra (out-of-sample) y walk-forward (optimizar en un tramo, "
     "probar en el siguiente). Las simulaciones de Monte Carlo estiman el rango de resultados y el "
     "drawdown posible. Incluye costes (spread, comisiones, slippage). Desconfía de curvas de "
     "equity 'perfectas': suelen ser sobre-ajuste. La robustez importa más que un retorno histórico brillante."),

    ("Cobertura (hedging)",
     "Cubrirse (hedge) es abrir una posición que compensa el riesgo de otra: p.ej. proteger una "
     "cartera de acciones con cortos en el índice, o usar un activo inversamente correlacionado "
     "(oro/dólar en risk-off). Reduce la exposición sin cerrar la posición principal.",
     "El hedge tiene coste (reduce beneficio potencial) y sirve para atravesar incertidumbre "
     "(eventos, noticias) sin liquidar todo. Cubrir con activos correlacionados o con opciones "
     "(puts de protección) acota pérdidas. No es gratis ni elimina todo el riesgo (correlaciones "
     "cambian). Concepto clave de gestión: proteger el capital ante escenarios adversos conocidos."),

    ("Salidas por tiempo y por estructura",
     "Además del stop y el objetivo, existen salidas por TIEMPO (cerrar al vencimiento, fin de "
     "sesión o si el trade no se mueve en X velas) y por ESTRUCTURA (salir si se pierde el nivel/"
     "media que sostenía la tesis, o aparece un CHoCH en contra). Definir la salida es tan vital "
     "como la entrada.",
     "Una operación que no avanza consume capital y atención: una salida por tiempo libera recursos. "
     "La salida por estructura protege ganancias cuando el motivo de la operación deja de existir "
     "(rompe la línea de tendencia, cambia el carácter). En binarias la salida es el vencimiento "
     "fijo: por eso elegirlo bien es crucial. Planifica TODAS las formas de salir antes de entrar."),
]

# ---- LOTE 6: conocimiento de FUENTES FIABLES (autores, obras y datos oficiales) ----
_BATCH6: list[tuple[str, str, str]] = [
    ("Teoría de Dow (Charles Dow)",
     "La Teoría de Dow, base del análisis técnico moderno (Charles Dow, fundador del Wall Street "
     "Journal y del Dow Jones), postula: el precio lo descuenta todo; hay tres tendencias "
     "(primaria, secundaria, menor); la tendencia persiste hasta señales claras de giro; y el "
     "volumen debe confirmar la tendencia.",
     "Principios clave: (1) los índices deben confirmarse entre sí (industriales y transportes en "
     "su origen); (2) una tendencia se compone de fases (acumulación, participación pública, "
     "distribución); (3) la tendencia primaria dura meses/años; las secundarias son correcciones. "
     "Es el marco conceptual del que derivan tendencia, confirmación y volumen. Fuente fundacional "
     "y fiable, aplicable a cualquier mercado."),

    ("John Murphy — Análisis Técnico e Intermercado",
     "John J. Murphy, en 'Análisis Técnico de los Mercados Financieros', es una referencia estándar "
     "del AT. También popularizó el análisis INTERMERCADO: dólar, bonos, materias y acciones se "
     "influyen y deben leerse en conjunto. Fuente rigurosa y ampliamente reconocida.",
     "De Murphy se toma la disciplina de combinar tendencia, patrones, indicadores y volumen, y la "
     "idea de que ningún mercado se mueve aislado. Su enfoque intermercado guía el contexto macro "
     "(dólar fuerte presiona materias; bonos y acciones se relacionan con los tipos). Es lectura "
     "obligada y base sólida para operar con criterio en todos los mercados."),

    ("Edwards & Magee — patrones clásicos",
     "'Technical Analysis of Stock Trends' (Robert Edwards y John Magee, 1948) es la obra clásica "
     "que catalogó los patrones gráficos (hombro-cabeza-hombro, dobles techos/suelos, triángulos, "
     "banderas) y las líneas de tendencia. Base histórica y fiable del chartismo.",
     "Estableció reglas para trazar tendencias, medir objetivos de patrones y usar el volumen como "
     "confirmación. Muchos conceptos que hoy se dan por sentados provienen de aquí. Aporta rigor: "
     "los patrones se definen con criterios objetivos, no a ojo. Referencia canónica para el "
     "reconocimiento de patrones en cualquier activo."),

    ("Thomas Bulkowski — estadística de patrones",
     "Thomas Bulkowski ('Encyclopedia of Chart Patterns') midió el RENDIMIENTO ESTADÍSTICO de los "
     "patrones: tasa de acierto, objetivo alcanzado, fallos y mejores condiciones. Enseña que no "
     "todos los patrones son iguales y que conviene operar los de mayor probabilidad histórica.",
     "Aporta datos en vez de folclore: algunos patrones cumplen su objetivo con más frecuencia y en "
     "ciertos contextos (a favor de la tendencia, con ruptura por volumen). Su lección práctica: "
     "elige patrones con buen historial, confirma la ruptura y gestiona el riesgo porque incluso "
     "los mejores fallan un % de las veces. Enfoque basado en evidencia, fiable y medible."),

    ("Steve Nison — velas japonesas",
     "Steve Nison introdujo formalmente las velas japonesas en Occidente ('Japanese Candlestick "
     "Charting Techniques'). Es la referencia sobre patrones de velas (martillo, envolvente, doji, "
     "estrellas) y su interpretación como lucha entre compradores y vendedores.",
     "De Nison se aprende que una vela cuenta una historia (apertura, máximos, mínimos, cierre) y "
     "que los patrones ganan valor en contexto: en soporte/resistencia, tras tendencia y con "
     "confirmación. Las velas son un lenguaje universal aplicable a cripto, forex, índices y "
     "acciones. Fuente autorizada del análisis de velas."),

    ("Mark Douglas — psicología (Trading in the Zone)",
     "Mark Douglas ('Trading in the Zone', 'The Disciplined Trader') es la referencia en psicología "
     "de trading. Su tesis: el mercado es incierto y hay que pensar en PROBABILIDADES, no en "
     "certezas; el resultado de una operación individual es aleatorio dentro de una ventaja estadística.",
     "Enseña a operar 'sin miedo ni euforia' aceptando que cualquier operación puede perder aunque "
     "hagas todo bien. Las claves: definir el riesgo de antemano, ejecutar sin apego al resultado y "
     "confiar en la ventaja a lo largo de una serie. Elimina el revenge trading y el FOMO. Fuente "
     "esencial para la disciplina mental en cualquier mercado."),

    ("Van Tharp — sizing, expectativa y R-múltiplos",
     "Van K. Tharp ('Trade Your Way to Financial Freedom') popularizó que lo importante no es "
     "'acertar' sino la EXPECTATIVA y el TAMAÑO de posición. Mide los resultados en R-múltiplos: "
     "cada operación se expresa en múltiplos del riesgo inicial (1R = lo que arriesgaste).",
     "Si arriesgas 1R y ganas 3 veces esa cantidad, es +3R. La expectativa = R promedio por "
     "operación; positiva y sostenida = sistema rentable. El 'position sizing' (cuánto arriesgar) "
     "determina el crecimiento y el riesgo de ruina más que la entrada. Pensar en R estandariza "
     "resultados entre activos y mercados. Fuente clave de gestión monetaria."),

    ("Alexander Elder — Trading for a Living y triple pantalla",
     "Alexander Elder ('Trading for a Living') aporta el sistema de TRIPLE PANTALLA y reglas de "
     "gestión monetaria: la regla del 2% (máximo riesgo por operación) y la del 6% (máxima pérdida "
     "mensual). Integra análisis, gestión y psicología (los 'tres pilares').",
     "La triple pantalla decide en tres pasos: (1) tendencia en la temporalidad ALTA (con un "
     "indicador de tendencia); (2) un oscilador en la temporalidad INTERMEDIA para el retroceso; "
     "(3) el gatillo de entrada en la temporalidad BAJA. Combina multi-temporalidad con timing. "
     "Sus reglas 2%/6% protegen la cuenta. Fuente práctica y fiable aplicable a todos los mercados."),

    ("Welles Wilder — RSI, ATR, ADX y Parabolic SAR",
     "J. Welles Wilder ('New Concepts in Technical Trading Systems', 1978) CREÓ varios de los "
     "indicadores más usados: RSI, ATR (rango medio verdadero), ADX/DMI (fuerza de tendencia) y el "
     "Parabolic SAR. Fuente original de estas herramientas.",
     "Conocer la intención del autor evita malos usos: el RSI mide impulso (no es orden de compra/"
     "venta por sí solo), el ATR mide volatilidad para stops, el ADX mide FUERZA (no dirección) y "
     "el SAR es un trailing stop. Wilder diseñó indicadores complementarios: combinar fuerza (ADX), "
     "impulso (RSI) y volatilidad (ATR) da una lectura completa en cualquier mercado."),

    ("John Bollinger y Gerald Appel — Bandas y MACD",
     "John Bollinger creó las Bandas de Bollinger ('Bollinger on Bollinger Bands') y advierte: tocar "
     "una banda NO es señal por sí sola, hay que confirmar. Gerald Appel creó el MACD. Usar un "
     "indicador según su creador evita interpretaciones erróneas.",
     "Bollinger enseña que en tendencia el precio 'camina' por una banda y que el squeeze (bandas "
     "estrechas) precede a movimientos; combina las bandas con otros indicadores no correlacionados. "
     "Appel diseñó el MACD para captar cambios de tendencia/momentum vía cruces y divergencias. "
     "Respetar la lógica original de cada herramienta mejora su fiabilidad."),

    ("Ondas de Elliott y método Wyckoff (fuentes)",
     "Ralph Nelson Elliott ('The Wave Principle') describió los ciclos de 5 ondas de impulso y 3 "
     "correctivas. Richard Wyckoff formuló las leyes de oferta/demanda, causa/efecto y esfuerzo/"
     "resultado, y el concepto del 'operador compuesto' (dinero inteligente). Fuentes clásicas.",
     "Elliott aporta un marco de estructura ondulatoria (subjetivo: úsalo con Fibonacci y "
     "confirmación). Wyckoff aporta cómo acumula y distribuye el dinero inteligente y cómo el "
     "volumen (esfuerzo) debe corresponder al movimiento (resultado). Ambos son bases del análisis "
     "de estructura y de la lógica institucional moderna (SMC). Fuentes reconocidas y atemporales."),

    ("Jack Schwager — Market Wizards (lecciones)",
     "Jack Schwager entrevistó a grandes operadores en la serie 'Market Wizards'. Lecciones comunes "
     "de los mejores: cortar pérdidas rápido, gestión de riesgo estricta, disciplina, tener un edge "
     "y un método propio, y controlar la psicología. No hay un único estilo ganador.",
     "Los 'magos del mercado' coinciden más en la GESTIÓN y la MENTALIDAD que en la técnica: "
     "arriesgar poco por operación, adaptarse, aceptar errores y ser consistentes. Muchos usan "
     "enfoques distintos (tendencia, contrarian, sistemático), lo que prueba que el edge + la "
     "disciplina importan más que una 'estrategia mágica'. Fuente inspiradora y realista."),

    ("Educación fiable: Babypips, Investopedia, CMT/CFA",
     "Para aprender con rigor y gratis, fuentes fiables son Babypips (escuela de forex), "
     "Investopedia (diccionario y guías de finanzas) y los cuerpos de conocimiento de la CMT "
     "Association (Chartered Market Technician) y el CFA Institute. Enseñan con evidencia y ética, "
     "no promesas de riqueza.",
     "Estas fuentes explican conceptos verificables y advierten de los riesgos. La certificación CMT "
     "cubre análisis técnico serio; el CFA cubre finanzas e inversión. Babypips es ideal para "
     "fundamentos de forex; Investopedia para definiciones claras. Prioriza SIEMPRE material que "
     "hable de gestión de riesgo y probabilidades frente a 'gurús' que prometen ganancias seguras."),

    ("Datos oficiales y calendarios fiables",
     "Para datos macro fiables usa fuentes oficiales: BLS de EE. UU. (empleo NFP e inflación IPC), "
     "EIA (inventarios de petróleo), la CFTC (informe COT de posicionamiento), Eurostat y los "
     "bancos centrales (Fed, BCE). Para agenda de eventos, calendarios como Forex Factory o "
     "Investing.com.",
     "Operar con datos de primera mano evita rumores. Los calendarios económicos marcan la hora y el "
     "impacto esperado de cada evento (para evitar operar en el momento del dato). El COT de la CFTC "
     "muestra cómo se posicionan los grandes en futuros. Verificar la fuente y el consenso previo es "
     "parte del análisis fundamental serio en forex, índices, materias y bonos."),

    ("Cómo evaluar una fuente de trading",
     "No todas las fuentes valen. Señales de fuente FIABLE: habla de probabilidades y gestión de "
     "riesgo, muestra evidencia/datos, admite que se pierde parte de las veces, no promete "
     "resultados. Señales de ALERTA: 'señales infalibles', ganancias garantizadas, urgencia para "
     "vender un curso, sin gestión de riesgo.",
     "Aplica escepticismo: desconfía de gurús que enseñan lujo en vez de método, de sistemas 'sin "
     "pérdidas' y de la ausencia de gestión de riesgo. Prioriza autores contrastados, material "
     "académico (CMT/CFA) y datos oficiales. Verifica afirmaciones con backtest y resultados "
     "reales. Una fuente honesta te prepara para perder bien, no solo para soñar con ganar."),

    ("R-múltiplos y calidad del sistema (SQN)",
     "Medir en R-múltiplos (Van Tharp) estandariza resultados: cada trade se expresa como múltiplo "
     "del riesgo (R). Con la distribución de R se calculan expectativa (R medio) y consistencia. El "
     "SQN (System Quality Number) valora la calidad de un sistema combinando expectativa y regularidad.",
     "Ventaja: comparar operaciones y sistemas entre activos y tamaños de forma homogénea. Una "
     "expectativa de +0.5R por trade sobre muchas operaciones es una buena ventaja. La consistencia "
     "(baja dispersión de R) importa tanto como la media. Registra cada operación en R para saber si "
     "tu sistema realmente tiene edge y en qué mercados rinde mejor."),

    ("Las cuatro fases del mercado (ciclo)",
     "Todo mercado cicla por cuatro fases (Wyckoff/Weinstein): ACUMULACIÓN (rango tras caída, "
     "dinero inteligente compra), AVANCE/tendencia alcista, DISTRIBUCIÓN (rango tras subida, se "
     "vende a la multitud) y DECLIVE/tendencia bajista. Identificar la fase orienta la táctica.",
     "En acumulación y distribución conviene operar rangos (comprar soporte/vender resistencia); en "
     "avance y declive, seguir tendencia (pullbacks, rupturas). El mayor error es aplicar la táctica "
     "de una fase en otra. La fase se reconoce por la estructura del precio respecto a una media "
     "larga (p.ej. la de 30 semanas de Weinstein). Marco de contexto válido en todos los mercados."),

    ("Stan Weinstein — análisis de etapas",
     "Stan Weinstein ('Secrets for Profiting in Bull and Bear Markets') define 4 ETAPAS usando la "
     "media móvil de 30 semanas: Etapa 1 (base/acumulación), Etapa 2 (avance alcista, comprar), "
     "Etapa 3 (techo/distribución), Etapa 4 (declive, evitar o vender). Compra en Etapa 2.",
     "La clave: operar a favor de la Etapa 2 (precio sobre una MM30 al alza, tras romper la base con "
     "volumen) y evitar comprar en Etapa 4 (precio bajo la MM30 a la baja). La fuerza relativa frente "
     "al índice ayuda a elegir los líderes. Es un método de swing/posición sencillo y robusto, "
     "aplicable a acciones, índices, cripto y materias."),

    ("Curtis Faith / Turtles — reglas y disciplina",
     "El experimento de las 'Tortugas' (Richard Dennis y William Eckhardt; relatado por Curtis "
     "Faith en 'Way of the Turtle') demostró que un sistema de seguimiento de tendencia con reglas "
     "claras y GESTIÓN de riesgo puede enseñarse y ser rentable. La disciplina pesó más que el talento.",
     "Reglas turtle: entradas por ruptura de canales (Donchian), tamaño por volatilidad (ATR), "
     "añadir a ganadores, cortar pérdidas y seguir el sistema sin excepciones. Lección central: un "
     "edge modesto aplicado con disciplina absoluta y buena gestión supera a la intuición "
     "indisciplinada. Base del trading sistemático y del control de riesgo."),

    ("Ley de esfuerzo y resultado (volumen-precio)",
     "Principio de Wyckoff y del Análisis Volumen-Precio (VSA, Tom Williams): el VOLUMEN es el "
     "esfuerzo y el movimiento del precio, el resultado. Cuando el esfuerzo (volumen alto) no "
     "produce resultado (el precio apenas avanza), hay ANOMALÍA: alguien absorbe, y suele avisar giro.",
     "Ejemplos: volumen enorme en un máximo con cierre débil = distribución (posible techo); volumen "
     "alto en un mínimo con cierre fuerte = absorción de compra (posible suelo). Poco volumen en una "
     "subida = falta de interés (débil). Leer la relación esfuerzo/resultado detecta la mano fuerte "
     "detrás del precio. Fundamento del análisis de volumen fiable en mercados con volumen real."),

    ("Larry Williams y Linda Raschke — momentum y swing",
     "Larry Williams (creador del %R y campeón de trading real) y Linda Raschke ('Street Smarts') "
     "son referencias en momentum y swing trading de corto plazo. Aportan setups probados como la "
     "'turtle soup' (reversión de falsa ruptura) y el uso del momentum con gestión estricta.",
     "Enseñan a combinar momentum, patrones de corto plazo y una gestión de riesgo disciplinada, y a "
     "operar con un plan claro de entrada/salida. Su enfoque práctico (setups repetibles, no "
     "predicciones) encaja con el trading intradía y de swing en futuros, forex e índices. Fuentes "
     "fiables de estrategias concretas y realistas."),

    ("El sistema aprende de sus operaciones (refuerzo)",
     "Este sistema se FORTALECE operando: cada señal se registra con su 'foto' de indicadores; al "
     "vencer se marca acierto/fallo con el precio real; y un modelo aprende qué condiciones tienden "
     "a acertar, ajustando la confianza futura. Además contrasta con el conocimiento y la tendencia "
     "de fondo. Cuantas más operaciones evaluadas, más fiable.",
     "El bucle de mejora: operar (motor autónomo + terminal) → registrar → evaluar con resultado "
     "real → reentrenar el modelo y actualizar la precisión por activo/duración. El conocimiento "
     "(estos fundamentos) da el marco de razonamiento y el histórico da la calibración. Mantén el "
     "motor autónomo encendido para que acumule resultados en todos los mercados y el sistema mejore "
     "con el tiempo, con honestidad (probabilidades, no certezas)."),
]

# ---- LOTE 7: gestión monetaria matemática, momentum, finanzas conductuales, datos ----
_BATCH7: list[tuple[str, str, str]] = [
    ("Ralph Vince — Optimal f (matemática del dinero)",
     "Ralph Vince ('The Mathematics of Money Management') formuló la 'f óptima': la fracción del "
     "capital por operación que MAXIMIZA el crecimiento geométrico dado tu histórico de ganancias/"
     "pérdidas. La f óptima completa es muy agresiva (grandes drawdowns); en la práctica se usa una "
     "fracción de ella.",
     "Igual que Kelly, optimal f busca el tamaño que más hace crecer la cuenta a largo plazo, pero "
     "operar a la f completa produce oscilaciones brutales y riesgo de ruina si las estimaciones "
     "fallan. Los profesionales usan 'f fraccional' (una parte de la óptima) para suavizar el "
     "drawdown. Lección: el TAMAÑO de posición, no la entrada, domina el resultado a largo plazo; "
     "calcúlalo con datos reales y con margen de seguridad."),

    ("Ryan Jones — Fixed Ratio position sizing",
     "Ryan Jones ('The Trading Game') propuso el 'Fixed Ratio': aumentar el tamaño solo cuando la "
     "ganancia acumulada alcanza un múltiplo (delta) del beneficio por contrato. Crece más despacio "
     "que optimal f al principio (protege) y acelera cuando hay colchón de ganancias.",
     "Frente al 'fixed fractional' (arriesgar siempre un % fijo), el fixed ratio ajusta cuán rápido "
     "escalas según cuánto has ganado ya. Un delta grande = crecimiento conservador; pequeño = "
     "agresivo. La idea clave: escalar el tamaño de forma controlada a medida que la cuenta crece, "
     "sin exponerte de más al principio. Es gestión monetaria disciplinada aplicable a cualquier mercado."),

    ("Ed Thorp — Kelly aplicado a los mercados",
     "Ed Thorp ('Beat the Market', 'A Man for All Markets'), matemático que venció al blackjack y a "
     "Wall Street, popularizó el criterio de Kelly para dimensionar apuestas/operaciones según la "
     "ventaja. Demostró que con un edge real y un sizing correcto se crece de forma óptima y se "
     "evita la ruina.",
     "Thorp enseña que primero necesitas una VENTAJA medible; luego el tamaño óptimo (Kelly) "
     "maximiza el crecimiento, pero conviene usar Kelly fraccional para reducir volatilidad. Sin "
     "ventaja, ningún sizing ayuda. Su legado une matemática, gestión de riesgo y disciplina: apostar "
     "poco cuando la ventaja es pequeña y evitar el riesgo de ruina por encima de todo."),

    ("Michael Covel — Trend Following",
     "Michael Covel ('Trend Following') documentó que seguir tendencias es una ventaja histórica "
     "robusta: no se predice, se REACCIONA. Se gana en pocas operaciones muy grandes (las grandes "
     "tendencias) y se pierde poco en muchas pequeñas, con gestión de riesgo estricta.",
     "El seguidor de tendencia acepta muchas pérdidas pequeñas y algunas ganancias enormes: la "
     "distribución es asimétrica y la disciplina para cortar pérdidas es esencial. No intenta acertar "
     "el techo/suelo; entra en la fuerza y deja correr con trailing stop. Funciona en materias, "
     "índices, forex y cripto en horizontes de swing/posición. Requiere aguantar rachas laterales sin abandonar."),

    ("Meb Faber — el filtro de la media de 200",
     "Meb Faber ('A Quantitative Approach to Tactical Asset Allocation') mostró que una regla simple "
     "—estar comprado solo cuando el precio está por encima de su media de ~200 sesiones (10 meses), "
     "y fuera cuando está por debajo— reduce drásticamente los grandes drawdowns con retornos "
     "similares.",
     "Es un FILTRO DE RÉGIMEN: opera al alza solo en 'modo alcista' (sobre la MM200) y evita el "
     "mercado en 'modo bajista' (bajo la MM200), esquivando lo peor de las caídas. No mejora tanto el "
     "retorno como REDUCE el riesgo y la volatilidad. Regla mecánica, sin emoción, verificada con "
     "datos largos. Aplícala como filtro de fondo para saber cuándo el viento sopla a favor."),

    ("Gary Antonacci — Dual Momentum",
     "Gary Antonacci ('Dual Momentum Investing') combina dos momentums: RELATIVO (elegir el activo "
     "más fuerte frente a otros) y ABSOLUTO (operarlo solo si su propia tendencia es positiva frente "
     "a un activo seguro). La combinación mejora el retorno ajustado a riesgo y evita mercados bajistas.",
     "El momentum relativo selecciona a los líderes; el absoluto (trend filter) te saca cuando "
     "incluso el líder cae. Así se capturan tendencias fuertes y se evita el desastre en caídas "
     "generalizadas. Es la base de la rotación entre activos/clases por fuerza. Principio aplicable a "
     "acciones, índices, materias y cripto: compra lo fuerte, pero solo si su tendencia es al alza."),

    ("Kahneman y Tversky — Teoría Prospectiva",
     "Daniel Kahneman y Amos Tversky (Teoría Prospectiva, Nobel de Kahneman) demostraron la AVERSIÓN "
     "A LA PÉRDIDA: perder duele psicológicamente ~2 veces más que el placer de ganar lo mismo. Por "
     "eso los traders cierran ganancias pronto (miedo) y aguantan pérdidas (esperanza), justo al revés.",
     "Somos irracionales bajo incertidumbre: sobrevaloramos lo seguro frente a lo probable y "
     "cambiamos de conducta según cómo se 'enmarca' una decisión. Consecuencia práctica: hay que "
     "IMPONER reglas (stop, objetivos, dejar correr ganancias) para contrarrestar el instinto. "
     "'Thinking, Fast and Slow' de Kahneman es lectura de referencia. Entender el sesgo es el primer "
     "paso para no ser su víctima en cualquier mercado."),

    ("Sesgos cognitivos del trader",
     "El cerebro nos engaña: sesgo de CONFIRMACIÓN (solo ves lo que apoya tu idea), de RECENCIA "
     "(sobrepesar lo último), de ANCLAJE (fijarte en un precio de referencia), coste HUNDIDO "
     "(aguantar por lo ya perdido) y falacia del jugador (creer que 'toca' un giro). Todos dañan la ejecución.",
     "Contramedidas: un plan escrito y una checklist objetiva; buscar activamente la tesis CONTRARIA; "
     "un diario para detectar patrones de error; y aceptar que cada operación es independiente (el "
     "mercado no 'debe' nada). Un sistema mecánico ayuda porque ejecuta sin estos sesgos. Reconocer el "
     "sesgo en el momento y volver a las reglas es una habilidad clave del trader profesional."),

    ("El efecto disposición",
     "El 'efecto disposición' (Shefrin y Statman) es la tendencia documentada a VENDER LOS GANADORES "
     "demasiado pronto y AGUANTAR LOS PERDEDORES demasiado tiempo. Es el error más común y caro, y "
     "nace de la aversión a la pérdida: cerrar una pérdida 'duele' y se pospone.",
     "Es lo contrario de lo correcto ('corta pérdidas, deja correr ganancias'). Combatirlo: define el "
     "stop y el objetivo ANTES de entrar y respétalos; usa trailing stop para dejar correr; nunca "
     "muevas el stop en contra para no 'realizar' la pérdida. Medir tus operaciones en R revela si "
     "sufres este efecto. Corregirlo transforma la curva de resultados en cualquier mercado."),

    ("Nassim Taleb — cisnes negros y antifragilidad",
     "Nassim Taleb ('Fooled by Randomness', 'The Black Swan', 'Antifragile') advierte de los eventos "
     "raros y extremos ('cisnes negros') que los modelos subestiman (colas gruesas). Lo esencial no es "
     "predecirlos, sino SOBREVIVIRLOS: evitar la ruina y buscar exposiciones de riesgo asimétrico.",
     "Claves: nunca te expongas a una pérdida que te saque del juego (riesgo de ruina); prefiere "
     "payoffs convexos (pierdes poco, puedes ganar mucho); desconfía de la falsa precisión y del "
     "apalancamiento excesivo. 'Antifrágil' = beneficiarse del desorden. En trading: gestión de riesgo "
     "que resista shocks (stops, tamaño prudente, no vender volatilidad a lo loco). Sobrevivir primero, optimizar después."),

    ("Burton Malkiel y la eficiencia del mercado",
     "Burton Malkiel ('A Random Walk Down Wall Street') y Eugene Fama (Hipótesis del Mercado "
     "Eficiente) sostienen que gran parte del movimiento es aleatorio y difícil de batir de forma "
     "consistente. Enseña HUMILDAD: la mayoría no supera al mercado y los costes/impuestos restan.",
     "Aunque existan ineficiencias explotables (de ahí el trading técnico y cuantitativo), conviene "
     "asumir que el edge es pequeño y frágil: exige evidencia, gestiona costes y desconfía de patrones "
     "que pueden ser ruido. Esta perspectiva escéptica protege de sobreconfianza y de 'ver' señales "
     "donde no las hay. Combina técnica con humildad estadística: opera tu ventaja, pero sin creerte infalible."),

    ("Larry Connors — reversión a la media (RSI-2)",
     "Larry Connors y Cesar Alvarez ('Short Term Trading Strategies That Work') probaron con datos "
     "estrategias de REVERSIÓN A LA MEDIA de corto plazo, como el RSI de 2 periodos: en mercados sobre "
     "su media de 200, comprar cuando el RSI(2) cae a valores extremos (<5-10) y salir al rebotar.",
     "La lógica: en tendencia alcista, los retrocesos bruscos (sobreventa de muy corto plazo) tienden "
     "a rebotar. Se opera A FAVOR de la tendencia mayor (filtro MM200) comprando el miedo pasajero. "
     "Es lo opuesto a seguir rupturas: aquí se compra debilidad temporal en un contexto alcista. "
     "Requiere disciplina y salidas rápidas. Enfoque cuantitativo, medible y aplicable a índices/acciones/cripto."),

    ("Pairs trading y arbitraje estadístico",
     "El pairs trading (arbitraje estadístico) es MERCADO-NEUTRAL: se opera el diferencial (spread) "
     "entre dos activos muy correlacionados/cointegrados. Cuando el spread se aleja de su media, se "
     "vende el fuerte y se compra el débil, apostando a que vuelvan a converger.",
     "No apuesta a la dirección del mercado sino a la RELACIÓN entre dos activos (dos acciones del "
     "mismo sector, dos cripto correlacionadas). Requiere que la relación sea estable (cointegración) "
     "y gestión del riesgo si se rompe. Es una estrategia de reversión a la media relativa, poco "
     "correlacionada con el mercado general, que diversifica el 'edge'. Concepto cuantitativo clásico y fiable."),

    ("Trend following vs reversión a la media",
     "Existen dos grandes ventajas (edges) casi opuestas: SEGUIR TENDENCIA (comprar fuerza, vender "
     "debilidad; gana en mercados direccionales) y REVERSIÓN A LA MEDIA (comprar debilidad, vender "
     "fuerza; gana en rangos). Aplicar la equivocada al régimen actual pierde dinero.",
     "El truco es identificar el RÉGIMEN (ADX, MM200, volatilidad) y usar el edge adecuado: "
     "seguimiento en tendencia fuerte; reversión en rango/baja volatilidad. Muchos sistemas robustos "
     "combinan ambos con un filtro de régimen. No hay un método único correcto; hay que casar la "
     "táctica con las condiciones. Esta flexibilidad, con reglas claras, es señal de madurez en cualquier mercado."),

    ("Tipos de órdenes",
     "Órdenes básicas: de MERCADO (ejecuta ya al mejor precio, con posible slippage), LÍMITE (solo a "
     "tu precio o mejor, puede no ejecutarse), STOP (se activa al tocar un nivel, para cortar pérdidas "
     "o romper), STOP-LÍMITE (stop que luego pone un límite) y TRAILING (stop que sigue al precio).",
     "La OCO ('one cancels other') une objetivo y stop: al ejecutar uno, cancela el otro. Usa límite "
     "para entrar con precisión y control de coste; mercado cuando la ejecución inmediata importa más "
     "que el precio exacto. El stop es imprescindible para gestionar riesgo. Elegir bien el tipo de "
     "orden reduce slippage y ejecuta tu plan tal como lo diseñaste, en cualquier mercado."),

    ("Vigencia de la orden y ejecución",
     "La 'vigencia' (time in force) define cuánto vive una orden: DÍA (expira al cierre), GTC "
     "('good till cancelled', hasta cancelar), IOC ('immediate or cancel', ejecuta lo posible ya y "
     "cancela el resto) y FOK ('fill or kill', todo o nada al instante). Afecta cómo y cuándo entras.",
     "En mercados poco líquidos, una orden grande a mercado puede tener 'impacto' (mueve el precio en "
     "tu contra). Fraccionar la orden o usar límites reduce ese impacto. IOC/FOK sirven para no "
     "quedar con ejecuciones parciales no deseadas. Conocer estos detalles de microestructura mejora "
     "la calidad de ejecución, sobre todo en scalping y en activos con poca profundidad."),

    ("Apalancamiento y margen",
     "El apalancamiento permite controlar una posición grande con poco capital (margen). AMPLIFICA "
     "por igual ganancias Y pérdidas: 10x significa que un movimiento del 10% en contra liquida tu "
     "margen. El 'margin call' o liquidación cierra la posición forzosamente al agotarse la garantía.",
     "El apalancamiento es la causa número uno de ruina de traders novatos: convierte un movimiento "
     "normal en catastrófico. Úsalo con extrema prudencia: el tamaño de la posición debe fijarse por "
     "el RIESGO (distancia al stop y 1-2% del capital), no por el margen disponible. En cripto y "
     "forex el apalancamiento alto es tentador y peligroso. Menos apalancamiento = más supervivencia."),

    ("Ratios de rendimiento: Sortino y Calmar",
     "Además del Sharpe (retorno por unidad de riesgo total), el SORTINO penaliza solo la volatilidad "
     "a la BAJA (la que duele), y el CALMAR relaciona el retorno anual con el MÁXIMO DRAWDOWN. Miden "
     "la calidad del rendimiento ajustada al riesgo que de verdad importa.",
     "Un sistema puede tener buen retorno pero drawdowns insoportables: Calmar lo revela (retorno/"
     "peor caída). Sortino distingue la volatilidad 'mala' (caídas) de la 'buena' (subidas). Úsalos "
     "para comparar sistemas/activos con criterio, no solo por la ganancia bruta. Un rendimiento "
     "estable con drawdown contenido es preferible a uno alto pero errático. Aplican a cualquier estrategia y mercado."),

    ("Volatility targeting y filtro de régimen",
     "El 'volatility targeting' ajusta el tamaño de posición para mantener CONSTANTE la volatilidad "
     "del riesgo: cuando el activo (o la cartera) está más volátil, reduces tamaño; cuando está "
     "tranquilo, lo aumentas. Combinado con un filtro de régimen (MM200) mejora el retorno ajustado a riesgo.",
     "Sin ajuste, una posición 'normal' arriesga mucho más en épocas volátiles. Dimensionar por "
     "volatilidad (ATR) normaliza el riesgo en el tiempo y entre activos. Un filtro de régimen "
     "(operar a favor solo sobre la MM200) evita lo peor de los mercados bajistas. Juntas, dan una "
     "curva de capital más suave y controlada, principio usado por fondos cuantitativos en todos los mercados."),

    ("Fuentes de datos fiables",
     "Para datos de calidad usa fuentes primarias: FRED (Reserva Federal de EE. UU.) para macro, las "
     "webs oficiales de exchanges y de los bancos centrales, TradingView para gráficos, y CoinGecko/"
     "CoinMarketCap para datos de cripto. Verifica siempre el origen antes de fiarte de una cifra.",
     "Datos fiables evitan decisiones sobre rumores o cifras manipuladas. FRED ofrece series "
     "históricas gratuitas (tipos, inflación, empleo). Los exchanges publican precio y volumen "
     "reales; para cripto, CoinGecko agrega múltiples mercados. Cruza fuentes cuando algo sea "
     "importante. Un análisis solo es tan bueno como los datos que lo alimentan: prioriza lo oficial y contrastado."),

    ("Análisis on-chain en cripto",
     "En cripto existe una fuente única: los datos ON-CHAIN (la propia cadena de bloques), provistos "
     "por plataformas como Glassnode. Métricas como flujos hacia/desde exchanges, direcciones activas, "
     "SOPR y MVRV muestran qué hacen realmente los tenedores, algo imposible en mercados tradicionales.",
     "Grandes salidas de monedas desde exchanges suelen indicar acumulación (menos oferta para vender, "
     "sesgo alcista); grandes entradas, posible presión vendedora. El MVRV compara el precio con el "
     "coste medio de los tenedores (extremos marcan techos/suelos). El on-chain complementa al análisis "
     "técnico con la conducta real de la red. Es conocimiento específico y fiable para Bitcoin y cripto."),

    ("Cripto: halving, funding y open interest",
     "El BTC tiene ciclos ligados al 'halving' (cada ~4 años se reduce a la mitad la emisión), "
     "históricamente asociados a grandes movimientos. El 'funding rate' de futuros perpetuos y el "
     "'open interest' (contratos abiertos) revelan el apalancamiento y el sesgo del mercado cripto.",
     "Funding muy positivo = exceso de largos apalancados (riesgo de purga a la baja); muy negativo = "
     "exceso de cortos (posible squeeze al alza). Subidas fuertes de open interest con precio plano "
     "avisan de apalancamiento acumulado y volatilidad inminente (liquidaciones en cascada). Estas "
     "métricas, junto al on-chain y la dominancia BTC, dan una lectura del riesgo específica y fiable en cripto."),

    ("Griegas de opciones y posicionamiento de dealers",
     "Aunque no operes opciones, su mercado influye en el subyacente. Las 'griegas' miden sensibilidad: "
     "delta (dirección), gamma (cambio de delta), theta (decaimiento temporal) y vega (volatilidad). "
     "El posicionamiento de los 'dealers' (gamma/GEX) y el 'max pain' pueden imantar el precio cerca "
     "de vencimientos.",
     "Con gamma positiva, los dealers estabilizan (compran caídas, venden subidas): el precio tiende a "
     "'pegarse' a niveles; con gamma negativa, amplifican los movimientos (volatilidad). El 'max pain' "
     "es el precio donde expira sin valor el mayor número de opciones, y suele atraer al subyacente en "
     "el vencimiento. Es contexto avanzado útil en índices y acciones con mercado de opciones líquido."),
]

# ---- LOTE 8: cuantitativo/algorítmico, carteras, grandes maestros y playbooks ----
_BATCH8: list[tuple[str, str, str]] = [
    ("Trading sistemático y algorítmico",
     "El trading sistemático opera reglas OBJETIVAS y probadas, sin emoción: define entradas, "
     "salidas y tamaño de forma mecánica, se puede backtestear y ejecutar de manera consistente. "
     "Su ventaja no es la genialidad puntual, sino la DISCIPLINA repetible y medible a lo largo de "
     "muchas operaciones.",
     "Frente al discrecional (juicio humano), el sistemático elimina el miedo, el FOMO y la duda, y "
     "permite validar la ventaja con datos. Requiere: reglas claras, backtest honesto (con costes y "
     "sin sobreajuste), y disciplina para SEGUIR el sistema aun en rachas malas. Un sistema mediocre "
     "ejecutado con consistencia suele batir a uno brillante mal ejecutado. Este propio motor es un "
     "sistema: reglas + aprendizaje de resultados reales."),

    ("Machine learning en trading (con honestidad)",
     "El aprendizaje automático puede hallar patrones en los datos, pero su gran enemigo es el "
     "SOBREAJUSTE (overfitting): memorizar el pasado y fallar en vivo. Claves para que sea fiable: "
     "muchos datos, validación fuera de muestra, pocas variables relevantes y evitar el 'data "
     "snooping' (probar mil cosas hasta que una parezca funcionar por azar).",
     "Un modelo debe generalizar, no memorizar: se valida con datos que no vio (walk-forward, "
     "validación cruzada) e incluyendo costes. Las 'features' (indicadores) deben tener lógica, no "
     "ser ruido. Un ML honesto da PROBABILIDADES, no certezas, y se combina con reglas y gestión de "
     "riesgo. Este sistema aprende de los resultados reales (aciertos/fallos) para ajustar la "
     "confianza, con esa cautela anti-sobreajuste."),

    ("Sistema mecánico vs discrecional",
     "El enfoque MECÁNICO sigue reglas fijas (objetivo, backtesteable, sin emoción). El DISCRECIONAL "
     "usa el juicio del operador para adaptarse al contexto. Ambos pueden ganar; lo peligroso es "
     "mezclarlos mal: saltarse las reglas 'por intuición' suele destruir la ventaja del sistema.",
     "El mecánico aporta consistencia y permite medir el edge; el discrecional aporta flexibilidad "
     "pero depende de la disciplina y experiencia, y es difícil de validar. Muchos profesionales usan "
     "un núcleo sistemático con un filtro discrecional acotado (p.ej. evitar noticias). Si eliges "
     "reglas, RESPÉTALAS; si eres discrecional, ten un plan y un diario. La incoherencia es el "
     "verdadero enemigo, en cualquier mercado."),

    ("Ejecución algorítmica (TWAP/VWAP, trocear)",
     "Ejecutar bien importa tanto como decidir. Órdenes grandes se TROCEAN para reducir el impacto en "
     "el precio: TWAP reparte la ejecución uniformemente en el tiempo; la ejecución tipo VWAP la "
     "reparte según el volumen del día. Así se entra/sale cerca del precio medio sin mover el mercado.",
     "En activos poco líquidos, lanzar todo a mercado provoca slippage y mueve el precio en tu contra. "
     "Fraccionar en el tiempo (TWAP) o según el perfil de volumen (VWAP) mejora el precio medio de "
     "ejecución. Para el operador minorista, la lección es: usa límites, evita horas ilíquidas y no "
     "muevas tamaños grandes de golpe. La calidad de ejecución protege el 'edge' de una buena señal."),

    ("Harry Markowitz — Teoría Moderna de Carteras",
     "Harry Markowitz (Nobel, Teoría Moderna de Carteras, 1952) demostró que combinar activos POCO "
     "correlacionados reduce el riesgo total sin sacrificar retorno: la diversificación es 'el único "
     "almuerzo gratis'. La 'frontera eficiente' es el conjunto de carteras con el mejor retorno para "
     "cada nivel de riesgo.",
     "Lo que importa no es el riesgo de cada activo aislado, sino cómo se COMBINAN (correlaciones). "
     "Dos activos volátiles pero poco correlacionados pueden formar una cartera más estable. "
     "Diversificar entre clases (acciones, bonos, oro, cripto) y estilos reduce la volatilidad de la "
     "cuenta. Principio base de la construcción de carteras: no pongas todo en una sola apuesta ni en "
     "apuestas que suben/bajan juntas."),

    ("William Sharpe — CAPM, beta y ratio de Sharpe",
     "William Sharpe (Nobel) desarrolló el CAPM y el famoso RATIO DE SHARPE (retorno en exceso por "
     "unidad de volatilidad). Distingue BETA (exposición al mercado, riesgo sistemático) de ALFA "
     "(retorno extra por habilidad, más allá del mercado). Mide si el retorno compensa el riesgo asumido.",
     "Beta 1 = se mueve como el mercado; >1 amplifica; <1 amortigua. Ganar solo por beta (subir "
     "cuando todo sube) no es habilidad; el alfa sí. El Sharpe permite comparar estrategias con "
     "criterio: un retorno alto con volatilidad enorme puede tener peor Sharpe que uno moderado y "
     "estable. Busca alfa real y buen Sharpe, no solo retorno bruto. Vale para carteras y sistemas en cualquier mercado."),

    ("Diversificación y correlación en la cartera",
     "Diversificar de verdad exige activos con BAJA correlación: tener 10 cripto es casi una sola "
     "apuesta (se mueven juntas). Mezclar clases que reaccionan distinto a los eventos (acciones, "
     "bonos, oro, dólar, cripto) suaviza la curva de capital y reduce el riesgo de un golpe único.",
     "Las correlaciones CAMBIAN: en pánico (risk-off) muchos activos caen juntos (la correlación "
     "sube justo cuando más querrías diversificación). Por eso se añaden refugios (oro, dólar, bonos) "
     "y se controla el riesgo AGREGADO. Diversificación no es tener muchas posiciones, sino tener "
     "apuestas poco relacionadas. Es la primera línea de defensa del capital en cualquier entorno."),

    ("Rebalanceo de cartera",
     "Rebalancear es devolver la cartera a sus pesos objetivo vendiendo lo que subió mucho y "
     "comprando lo que quedó rezagado. Impone disciplina (vender caro, comprar barato), controla el "
     "riesgo (evita que un activo domine) y captura la reversión a la media entre clases de activos.",
     "Sin rebalanceo, una posición ganadora crece hasta concentrar el riesgo de toda la cuenta. "
     "Rebalancear por calendario (trimestral) o por umbrales (cuando un peso se desvía X%) mantiene "
     "el perfil de riesgo deseado. Tiene coste (comisiones/impuestos), así que no se abusa. Es una "
     "herramienta de gestión de riesgo de cartera, complementaria a la gestión por operación."),

    ("Asignación de activos (estratégica y táctica)",
     "La asignación de activos (cómo repartes el capital entre clases) explica la mayor parte del "
     "resultado a largo plazo, más que la selección individual. La ESTRATÉGICA fija pesos de base "
     "(p.ej. 60% acciones / 40% bonos); la TÁCTICA los ajusta según el ciclo, la tendencia o el momentum.",
     "Una cartera clásica 60/40 busca equilibrio crecimiento/estabilidad. Estrategias tácticas usan "
     "filtros (MM200, momentum) para reducir exposición en mercados bajistas. La lección para el "
     "trader: decide primero CUÁNTO riesgo total y en qué clases, y luego las operaciones concretas. "
     "La asignación marca el rumbo; el trading fino, la ejecución. Aplica a carteras multi-mercado."),

    ("Ray Dalio — All Weather y risk parity",
     "Ray Dalio (Bridgewater, 'Principles') diseñó la cartera 'All Weather' basada en RISK PARITY: "
     "equilibrar el RIESGO (no el capital) entre activos que se comportan bien en distintos entornos "
     "económicos (crecimiento/recesión, inflación/deflación), para rendir en 'cualquier clima'.",
     "Risk parity asigna más peso a activos de baja volatilidad (bonos) y menos a los volátiles "
     "(acciones) para igualar su contribución al riesgo total. La idea de Dalio: no sabemos qué "
     "entorno vendrá, así que preparamos la cartera para todos, diversificando por MOTORES económicos, "
     "no solo por activos. Su marco de la 'máquina económica' (ciclos de crédito) ayuda a entender el "
     "contexto macro que mueve todos los mercados."),

    ("Benjamin Graham — margen de seguridad y Mr. Market",
     "Benjamin Graham ('El Inversor Inteligente'), padre del value investing y maestro de Buffett, "
     "aporta dos ideas atemporales: el MARGEN DE SEGURIDAD (comprar con suficiente descuento para "
     "protegerte de errores) y 'Mr. Market' (el mercado como un socio maníaco-depresivo que cada día "
     "te ofrece precios emocionales).",
     "Mr. Market unos días está eufórico (precios altos) y otros deprimido (precios de saldo): tú "
     "decides si le haces caso o aprovechas sus excesos. El margen de seguridad es gestión de riesgo "
     "pura: no pagues de más, deja colchón para el error. Aunque es inversión de valor, la lección "
     "sirve al trader: aprovecha el pánico/euforia ajenos y protégete siempre con un margen."),

    ("Warren Buffett — largo plazo y círculo de competencia",
     "Warren Buffett enseña paciencia, pensar a LARGO PLAZO, operar dentro de tu 'círculo de "
     "competencia' (lo que entiendes) y ser 'temeroso cuando otros son codiciosos y codicioso cuando "
     "otros temen'. Prioriza no perder: sus reglas 1 (no perder dinero) y 2 (no olvidar la 1).",
     "Aunque Buffett es inversor, sus principios aplican al trading: opera lo que comprendes, evita la "
     "sobreactividad, controla la emoción y protege el capital por encima de todo. El interés "
     "compuesto a largo plazo premia la CONSISTENCIA y la paciencia sobre los golpes de suerte. Menos "
     "operaciones y mejores, dentro de tu competencia, superan a la hiperactividad indisciplinada."),

    ("Jesse Livermore — lecciones clásicas",
     "Jesse Livermore ('Reminiscences of a Stock Operator', de Edwin Lefèvre) dejó lecciones eternas: "
     "opera A FAVOR de la tendencia, entra en 'pivotal points' (puntos de ruptura clave), corta "
     "pérdidas rápido, NUNCA promedies a la baja, y gana el dinero grande 'sentándote' en las "
     "operaciones correctas, no operando sin parar.",
     "Livermore insistía en la PACIENCIA ('el dinero se hace esperando, no operando'), en respetar la "
     "tendencia y en la disciplina de aceptar pérdidas pequeñas. También advirtió contra la emoción y "
     "el exceso de apalancamiento (que a él mismo le arruinó). Un siglo después, sus principios "
     "—tendencia, timing, gestión de pérdidas y paciencia— siguen vigentes en todos los mercados."),

    ("William O'Neil — CAN SLIM y fuerza relativa",
     "William O'Neil ('How to Make Money in Stocks', fundador de IBD) creó el método CAN SLIM para "
     "acciones de crecimiento: busca fuerte crecimiento de beneficios, liderazgo (alta FUERZA "
     "RELATIVA), respaldo institucional y compra rupturas de bases sólidas (como la taza con asa) en "
     "un mercado alcista.",
     "CAN SLIM combina fundamentales (beneficios crecientes) con técnico (rupturas con volumen, líderes "
     "del mercado) y timing (operar con la tendencia general al alza). Enfatiza cortar pérdidas al "
     "7-8% y comprar solo los LÍDERES, no los rezagados. Aporta un marco disciplinado y basado en "
     "evidencia para seleccionar y cronometrar acciones de alto momentum."),

    ("Nicolas Darvas — teoría de las cajas",
     "Nicolas Darvas ('How I Made $2,000,000 in the Stock Market') desarrolló la 'teoría de las cajas': "
     "el precio se mueve en rangos (cajas) sucesivos; se compra la RUPTURA de la caja al alza con "
     "volumen y se sube el stop bajo la nueva caja, dejando correr la tendencia por escalones.",
     "Es seguimiento de tendencia por rupturas con gestión por 'cajas': cada nuevo rango más alto "
     "confirma la fuerza y protege ganancias con un stop ascendente. Darvas ignoraba el ruido y solo "
     "actuaba en rupturas claras de líderes en tendencia. Su método, sencillo y disciplinado, prefigura "
     "el trading por rupturas y el trailing stop estructural usados hoy en todos los mercados."),

    ("Ed Seykota — trend following sistemático",
     "Ed Seykota (pionero de los sistemas informatizados, entrevistado en 'Market Wizards') es "
     "referencia del trend following sistemático. Frases clave: 'los elementos del buen trading son "
     "cortar pérdidas, cortar pérdidas y cortar pérdidas'; y 'todos obtienen del mercado lo que "
     "realmente quieren' (la psicología manda).",
     "Seykota operaba señales mecánicas de tendencia con gestión de riesgo estricta y una fuerte "
     "conciencia psicológica: seguir el sistema, controlar el riesgo por operación y no dejar que la "
     "emoción rompa las reglas. Su legado une sistematización, seguimiento de tendencia y dominio "
     "mental. Recuerda que el mejor sistema fracasa si el operador no tiene la disciplina de ejecutarlo."),

    ("Druckenmiller y Soros — macro y asimetría",
     "Stanley Druckenmiller y George Soros son leyendas del trading MACRO. Enseñan a apostar FUERTE "
     "cuando la convicción y la asimetría son altas ('no importa si aciertas, sino cuánto ganas "
     "cuando aciertas y cuánto pierdes cuando fallas') y a recortar rápido cuando la tesis falla.",
     "Druckenmiller: concentra el capital en tus mejores ideas (con gestión de riesgo), no lo diluyas "
     "en muchas mediocres. Soros: busca reflexividad y desequilibrios macro, y no teme cambiar de "
     "opinión al instante si los hechos cambian. Lección: la GESTIÓN del tamaño según la convicción y "
     "la flexibilidad para admitir errores importan más que 'tener razón'. Aplicable al posicionamiento en cualquier mercado."),

    ("Inversión sistemática (dollar cost averaging)",
     "El 'dollar cost averaging' (DCA) invierte una cantidad FIJA a intervalos regulares, sin intentar "
     "cronometrar el mercado. Compra más unidades cuando el precio está bajo y menos cuando está alto, "
     "promediando el coste y reduciendo el riesgo de entrar todo en el peor momento.",
     "Es una estrategia de acumulación de largo plazo (muy usada en índices y en Bitcoin) que quita "
     "emoción y timing a la ecuación. No maximiza el retorno teórico, pero reduce el arrepentimiento y "
     "el riesgo de mal timing, y es sostenible psicológicamente. Complementa (no sustituye) al trading "
     "activo: sirve para la parte 'inversión' de una estrategia global de gestión del capital."),

    ("Interés compuesto y consistencia",
     "El interés compuesto —reinvertir las ganancias— hace crecer el capital de forma EXPONENCIAL con "
     "el tiempo. En trading, ganancias porcentuales modestas pero CONSISTENTES, compuestas, superan a "
     "los golpes espectaculares seguidos de grandes pérdidas. La regularidad vence a la brillantez errática.",
     "La otra cara: las pérdidas también componen y la recuperación es asimétrica (perder 50% exige "
     "ganar 100%). Por eso proteger el capital y evitar grandes drawdowns es clave para que el "
     "compounding trabaje a tu favor. Objetivo realista: una ventaja pequeña, gestión de riesgo "
     "estricta y consistencia durante mucho tiempo. La paciencia y el compounding son el verdadero motor de la riqueza."),

    ("Playbook: Bitcoin (hábitos y niveles)",
     "Bitcoin (BTC): activo 24/7, muy volátil, líder de todo el mercado cripto (dominancia). Respeta "
     "niveles redondos psicológicos (20k, 50k, 100k), reacciona a funding/open interest y "
     "liquidaciones, y sigue ciclos ligados al halving. Sensible al entorno risk-on/risk-off y a la "
     "liquidez global.",
     "Plan de trabajo con BTC: define el sesgo con la tendencia de fondo (semanal/diario) y el "
     "on-chain (flujos de exchanges); opera en zonas clave con confirmación; usa stops AMPLIOS por su "
     "alta volatilidad (ATR) y tamaño reducido. Vigila la dominancia (guía a las altcoins), el funding "
     "(exceso de apalancamiento) y los fines de semana (menor liquidez, mechas). Evita perseguir "
     "velas parabólicas: espera retrocesos a zonas de valor."),

    ("Playbook: Oro (drivers y comportamiento)",
     "El oro (XAU/Gold) es refugio de valor. Sube con el miedo, la geopolítica y la inflación; se "
     "mueve INVERSO al dólar (DXY) y a los tipos de interés REALES (nominal menos inflación). "
     "Respeta niveles redondos (2000, 3000) y tiende a movimientos tendenciales largos en crisis.",
     "Plan con el oro: comprueba el DXY y los tipos reales (dólar débil + tipos reales a la baja = "
     "viento a favor); úsalo como cobertura en entornos risk-off. Reacciona a bancos centrales y "
     "datos de inflación (evita operar en el dato). Combina el sesgo macro con niveles técnicos y "
     "confirmación. La plata amplifica sus movimientos con más ruido. El oro premia la paciencia en "
     "tendencias de fondo, no el scalping errático."),

    ("Playbook: EUR/USD e índices",
     "EUR/USD: el par más líquido; se mueve por el DÓLAR (DXY), el diferencial de tipos Fed–BCE y los "
     "datos macro (NFP, IPC). Mayor rango en el solape Londres–Nueva York. Índices (S&P 500, Nasdaq): "
     "gran actividad en la apertura de Wall Street, sensibles a tipos, bonos y al VIX.",
     "Plan con EUR/USD: opera en horas líquidas, alinea con el sesgo del dólar y evita el minuto de las "
     "noticias de alto impacto; respeta soportes/resistencias y medias. Plan con índices: usa la "
     "apertura para rupturas del rango (ORB), vigila el VIX (miedo) y los rendimientos de bonos, y "
     "recuerda que los índices se confirman entre sí. En ambos, el mismo método (tendencia > zona > "
     "gatillo > gestión) calibrado a su volatilidad y horario."),
]

# ---- LOTE 9: microestructura/subastas, estadística, gestión de crisis e instrumentos ----
_BATCH9: list[tuple[str, str, str]] = [
    ("Teoría de subastas y Market Profile",
     "Peter Steidlmayer creó el Market Profile / Teoría de Subastas: el mercado es una SUBASTA "
     "continua que busca precios donde se negocia volumen (equilibrio) y rechaza donde no. Conceptos: "
     "TPO (tiempo-precio), balance inicial (rango de la primera hora), área de valor (~70% del "
     "volumen) y POC (precio de control).",
     "El precio pasa de FASES DE EQUILIBRIO (rango, área de valor amplia) a DESEQUILIBRIO (tendencia, "
     "que crea 'single prints' y extensiones del rango). Operar dentro del área de valor favorece la "
     "reversión a la media; la ruptura del balance inicial con aceptación favorece la tendencia. Es un "
     "marco para entender DÓNDE el mercado acepta o rechaza precio, complementario a soporte/resistencia y VWAP."),

    ("Subastas de apertura y cierre",
     "Las bolsas casan órdenes en SUBASTAS de apertura y cierre a un precio único de equilibrio. La "
     "subasta de CIERRE concentra un volumen enorme (fondos e índices ejecutan ahí) y fija el precio "
     "oficial del día; la de APERTURA descuenta las noticias nocturnas y suele generar volatilidad y gaps.",
     "La primera hora tras la apertura marca el 'balance inicial' y suele ser la más volátil y "
     "direccional (útil para ORB). El cierre (última media hora) mueve mucho volumen por rebalanceos y "
     "'market on close'. Conocer estos momentos ayuda a elegir cuándo operar (aperturas para "
     "rupturas) y a evitar el ruido de las subastas si no es tu estrategia. Aplica a acciones e índices."),

    ("Proveedores y tomadores de liquidez (maker/taker)",
     "En cada operación hay un 'maker' (pone liquidez con órdenes LÍMITE en el libro) y un 'taker' "
     "(la consume con órdenes de MERCADO). El taker paga el spread y suele pagar más comisión; el "
     "maker cobra o paga menos. El spread bid-ask es el coste inmediato de entrar y salir.",
     "En scalping y alta frecuencia, ser maker (límites) reduce costes pero arriesga no ejecutar; ser "
     "taker garantiza ejecución pero paga spread + posible slippage. En activos ilíquidos el spread es "
     "ancho y castiga. Elegir el tipo de orden según prisa vs coste, y operar en horas líquidas, "
     "protege tus resultados. La microestructura (quién provee liquidez) explica parte del movimiento intradía."),

    ("La distribución de los retornos no es normal",
     "Los retornos de los mercados NO siguen una campana de Gauss: tienen COLAS GRUESAS (curtosis "
     "alta) y sesgo. Los movimientos extremos ocurren mucho más a menudo de lo que predice el modelo "
     "normal, y las caídas suelen ser más bruscas que las subidas (sesgo negativo en acciones).",
     "Consecuencia práctica: los modelos que asumen normalidad SUBESTIMAN el riesgo de eventos "
     "extremos (crashes). Por eso stops, tamaño prudente y evitar apalancamiento excesivo son vitales: "
     "el 'evento de 6 sigma' que 'no debería pasar nunca' pasa. Planifica para las colas, no para el "
     "promedio. La volatilidad además se agrupa: las grandes sacudidas vienen en tandas."),

    ("Significancia estadística y tamaño de muestra",
     "Una estrategia necesita una MUESTRA suficiente para saber si su ventaja es real o suerte. Con "
     "pocas operaciones, cualquier resultado (bueno o malo) puede ser azar. La ley de los grandes "
     "números dice que solo con muchas repeticiones la media converge a la esperanza real del sistema.",
     "Juzgar un sistema por 10 operaciones es engañoso; se necesitan decenas o cientos para tener "
     "confianza estadística. Igual que no cambias de sistema por 3 pérdidas seguidas (normales), no te "
     "enamoras por 3 aciertos. Mide con muestra amplia, intervalos de confianza y fuera de muestra. "
     "Este sistema muestra la precisión con el número de operaciones evaluadas justo por esto: sin muestra, no hay conclusión."),

    ("Sesgo de minería de datos (data mining)",
     "Si pruebas MIL combinaciones de indicadores/parámetros, algunas 'funcionarán' de maravilla en el "
     "pasado solo por AZAR (multiple testing / p-hacking). Ese brillo no se repite en vivo. Es la "
     "trampa más común del backtesting y la razón de que muchos 'sistemas ganadores' fracasen al operar.",
     "Defensas: parte de una HIPÓTESIS con lógica (no busques a ciegas), usa pocos parámetros, valida "
     "fuera de muestra y con walk-forward, y desconfía de resultados demasiado perfectos. Cuantas más "
     "cosas pruebas, más probable es encontrar un falso positivo. La robustez (funcionar con reglas "
     "simples en datos no vistos) importa más que optimizar el pasado. Honestidad estadística ante todo."),

    ("Volatilidad: agrupamiento y persistencia",
     "La volatilidad se AGRUPA (volatility clustering): a días tranquilos siguen días tranquilos, y a "
     "sacudidas fuertes siguen más sacudidas. Es persistente y predecible en parte (modelos GARCH), "
     "aunque la DIRECCIÓN del precio no lo sea. La volatilidad sube en las caídas y baja en las subidas lentas.",
     "Uso práctico: tras un pico de volatilidad, espera más volatilidad (amplía stops, reduce tamaño); "
     "tras compresión prolongada, prepárate para una expansión (squeeze). Dimensionar por volatilidad "
     "(ATR / volatility targeting) normaliza el riesgo en el tiempo. Saber que 'la calma engendra "
     "calma y la tormenta, tormenta' ayuda a gestionar el riesgo en cualquier mercado."),

    ("Value at Risk (VaR) y Expected Shortfall",
     "El VaR estima la pérdida máxima esperada con cierta probabilidad en un horizonte (p.ej. 'con "
     "95% de confianza no perderé más de X en un día'). El Expected Shortfall (CVaR) mide la pérdida "
     "MEDIA cuando se supera el VaR: describe mejor la severidad de las COLAS que el VaR solo.",
     "Advertencia (Taleb): el VaR puede dar falsa seguridad porque ignora cuán MALO es el peor caso más "
     "allá del umbral, y asume distribuciones que subestiman las colas. Úsalo como referencia de riesgo, "
     "no como garantía. Complementa con pruebas de estrés (¿qué pasa en un −20%?) y con el CVaR. La "
     "gestión de riesgo debe preparar para el escenario extremo, no solo para el 95% normal."),

    ("Drawdown y tiempo bajo el agua",
     "El drawdown es la caída desde un máximo de capital hasta el siguiente mínimo; el 'tiempo bajo el "
     "agua' es cuánto tardas en recuperar ese máximo. Ambos miden el DOLOR real de una estrategia: un "
     "sistema puede ser rentable pero con drawdowns y periodos de recuperación insoportables.",
     "La recuperación es asimétrica (perder 50% exige +100%). Conocer el drawdown máximo histórico y "
     "el tiempo de recuperación prepara psicológicamente y evita abandonar el sistema en su peor "
     "momento (que suele preceder a la recuperación). El ratio Calmar (retorno/drawdown) resume esto. "
     "Controlar el drawdown con tamaño y filtros de régimen es clave para la supervivencia y la constancia."),

    ("Probabilidad condicional y pensamiento bayesiano",
     "El trader razona con probabilidades CONDICIONALES: 'dado A (una señal, un contexto), ¿cuál es la "
     "probabilidad de B (que suba)?'. El pensamiento bayesiano ACTUALIZA esa probabilidad con cada "
     "nueva evidencia (confluencia, confirmación, resultado), partiendo de una tasa base honesta.",
     "Ejemplo: la probabilidad base de una ruptura puede ser modesta; añade volumen alto y tendencia a "
     "favor (nueva evidencia) y la probabilidad sube; añade una noticia adversa y baja. No se busca "
     "certeza, sino MEJORAR la probabilidad con factores independientes (confluencia). Cuidado con la "
     "falacia de la tasa base (ignorar la probabilidad de partida). Pensar en condicionales y actualizar es el núcleo del análisis probabilístico."),

    ("Gestión de crisis y flash crashes",
     "En crisis y 'flash crashes' la liquidez DESAPARECE de golpe: el precio salta, los spreads se "
     "disparan y los stops se ejecutan muy lejos (slippage brutal). Ejemplos: flash crash de 2010, "
     "sacudidas de marzo 2020, colapsos cripto. Prepararse para lo extremo es parte de operar.",
     "Medidas: reduce apalancamiento y tamaño ANTES de eventos de riesgo; usa órdenes límite (no "
     "confíes solo en stops de mercado en momentos ilíquidos); no coloques stops en el nivel 'obvio' "
     "donde todos los tienen; ten liquidez/coberturas. En una cascada de liquidaciones (cripto), el "
     "movimiento se autoalimenta. Sobrevivir a la crisis importa más que exprimir el último punto: protege el capital."),

    ("Interruptores del mercado (circuit breakers)",
     "Las bolsas tienen 'circuit breakers' que HALTAN la negociación ante caídas extremas (en el S&P "
     "500, umbrales de −7%, −13% y −20% detienen el mercado por minutos o el día). Sirven para frenar "
     "el pánico y restaurar orden. Algunos futuros y cripto tienen límites o pausas similares.",
     "Implicaciones: durante un halt no puedes operar ni ajustar posiciones (riesgo si estás "
     "apalancado). Tras la reapertura suele haber volatilidad. En forex (descentralizado) no hay "
     "circuit breakers, pero sí baja liquidez en shocks. Conocer estos mecanismos evita sorpresas y "
     "refuerza por qué no conviene ir sobreapalancado en momentos de estrés extremo del mercado."),

    ("Contagio: las correlaciones tienden a 1",
     "En crisis, la DIVERSIFICACIÓN falla justo cuando más la necesitas: activos normalmente poco "
     "correlacionados caen todos juntos ('todo se vuelve 1'). El contagio y la búsqueda de liquidez "
     "hacen que se venda lo que se puede, no solo lo débil. El único refugio suele ser el efectivo, el dólar o los bonos.",
     "Por eso el control del riesgo AGREGADO importa: en un shock, varias posiciones 'diversificadas' "
     "pueden perder a la vez. Ten en cuenta la correlación en estrés (no la de tiempos tranquilos), "
     "reduce exposición ante eventos de riesgo y considera coberturas o efectivo. La verdadera "
     "diversificación se prueba en la crisis, no en la calma. Planifica para el escenario de correlación extrema."),

    ("Cobertura de cola (tail hedging)",
     "La cobertura de cola protege la cartera de eventos extremos (crashes) con exposiciones que ganan "
     "MUCHO cuando todo cae: puts fuera de dinero, posiciones en oro/dólar/bonos, o efectivo. Tiene un "
     "coste continuo (como un seguro), pero evita la ruina en el cisne negro (idea de Taleb).",
     "El objetivo no es ganar con la cobertura sino SOBREVIVIR y poder comprar barato tras el pánico "
     "(convexidad: pierdes poco de forma continua, ganas mucho en el shock). No sobre-cubrirse (drena "
     "retorno) ni infra-cubrirse (te expone a la ruina). Para el minorista, la 'cobertura' más simple "
     "es reducir tamaño/apalancamiento y mantener efectivo ante incertidumbre. Preservar capital habilita el compounding futuro."),

    ("Riesgo de contraparte y custodia (cripto)",
     "Más allá del mercado, existe el riesgo de CONTRAPARTE: que el bróker o exchange quiebre, congele "
     "fondos o sea fraudulento (caso FTX). En cripto rige 'not your keys, not your coins': si no "
     "custodias tú las claves, dependes de la solvencia y honestidad del exchange.",
     "Mitigación: usa plataformas REGULADAS y solventes, no dejes más fondos de los necesarios en el "
     "exchange, y en cripto considera la autocustodia para el largo plazo. Diversifica el riesgo de "
     "plataforma. El mejor análisis técnico no sirve si pierdes los fondos por un colapso del "
     "custodio. La seguridad operativa (dónde y con quién operas) es parte de la gestión de riesgo integral."),

    ("Stablecoins y riesgo de 'depeg'",
     "Las stablecoins (USDT, USDC…) buscan mantener 1:1 con el dólar y son la 'liquidez' del ecosistema "
     "cripto. Pero pueden PERDER LA PARIDAD ('depeg') si su respaldo es dudoso o hay pánico: el colapso "
     "de UST/Terra (2022) borró miles de millones; USDC sufrió un depeg temporal por exposición bancaria.",
     "No todas son iguales: las respaldadas por efectivo/bonos de corto plazo y auditadas son más "
     "fiables que las algorítmicas (que han fracasado). Un depeg de la stablecoin que usas afecta a "
     "todas tus posiciones y a la liquidez. Conocer el respaldo y el riesgo de cada stablecoin es "
     "parte del análisis de riesgo en cripto. La 'estabilidad' no está garantizada."),

    ("Instrumentos: spot, futuros, CFD y opciones",
     "Se puede operar un mismo activo con distintos instrumentos: SPOT (posees el activo), FUTUROS "
     "(apalancados, con vencimiento y curva), CFD (contrato por diferencia, OTC del bróker, con coste "
     "de financiación nocturna) y OPCIONES (derecho, no obligación; con griegas y vencimiento). Cada uno "
     "tiene costes y riesgos distintos.",
     "Los futuros y CFD ofrecen apalancamiento (y su peligro) y costes de rollover/swap; las opciones "
     "permiten estrategias no lineales y cobertura. El spot es el más simple y sin vencimiento. Elige "
     "el instrumento según tu horizonte, coste y necesidad de apalancamiento. Entender la mecánica "
     "(financiación, vencimiento, contraparte) evita sorpresas que erosionan el resultado."),

    ("Brokers regulados y protección del cliente",
     "Operar con un bróker REGULADO (por una autoridad seria) aporta protección: fondos segregados de "
     "los del bróker, supervisión, y a veces esquemas de compensación. Un bróker no regulado o en "
     "paraísos opacos añade riesgo de fraude, manipulación de precios o impago de retiros.",
     "Antes de depositar, verifica la licencia en el regulador correspondiente, lee opiniones sobre "
     "RETIROS (no solo depósitos) y desconfía de bonos agresivos o presión para operar. La seguridad de "
     "tu dinero es tan importante como tu estrategia: un gran sistema no sirve con un bróker que no te "
     "paga. Elegir bien la plataforma es la base de una operativa profesional y segura."),

    ("Opciones binarias: riesgos y conflicto de interés",
     "Las opciones binarias (pago fijo si aciertas dirección/tiempo) tienen desventajas ESTRUCTURALES: "
     "el payout es <100% (necesitas ganar >~54% solo para empatar) y muchos brokers OTC son la "
     "CONTRAPARTE de tu operación (ganan cuando pierdes), un conflicto de interés. Varios reguladores "
     "(p.ej. la ESMA en la UE) las restringieron o prohibieron para minoristas.",
     "Trátalas como producto de ALTO RIESGO: opera solo con plataformas serias, con gestión estricta, "
     "sin martingala, y siendo consciente de la ventaja de la casa. Prioriza la calidad de la señal y "
     "el punto de equilibrio del payout. Este sistema busca darte una ventaja probabilística real, pero "
     "ninguna estrategia elimina el riesgo estructural: opera con honestidad sobre las probabilidades y protege tu capital."),

    ("Sentimiento minorista y posicionamiento",
     "El posicionamiento del público minorista suele ser un indicador CONTRARIAN en extremos: cuando la "
     "gran mayoría de traders retail está en una dirección, el mercado a menudo hace lo contrario "
     "(barre esa liquidez). Algunos brokers publican el % de clientes largos/cortos; el COT muestra a "
     "los grandes.",
     "Ejemplo: si el 85% de retail está largo en un par, hay mucha liquidez de stops debajo y sesgo a "
     "una caída que los barra. No es timing exacto, sino contexto: en extremos de sentimiento, "
     "prepárate para reversiones. Combina el sentimiento (retail contrarian, COT de grandes) con la "
     "estructura técnica. 'Cuando todos piensan igual, casi nadie está pensando': úsalo como filtro de fondo."),

    ("Playbook: Petróleo (WTI/Brent)",
     "El petróleo (WTI, Brent) es muy volátil y se rige por OFERTA/DEMANDA: OPEP+, inventarios "
     "semanales de la EIA, crecimiento global, dólar y geopolítica. Reacciona con fuerza a titulares y "
     "tiene estacionalidad (temporada de conducción, invierno). Respeta niveles técnicos muy vigilados.",
     "Plan con el crudo: marca el dato de inventarios de la EIA y NO operes en el minuto del dato; "
     "sigue el sesgo de la OPEP+ (recortes = alcista) y del dólar (fuerte = bajista); usa stops AMPLIOS "
     "por su alto ATR y tamaño reducido. Vigila la geopolítica de zonas productoras (dispara "
     "volatilidad) y la curva de futuros (contango/backwardation) si operas ETFs. Opera rupturas y "
     "rebotes en niveles claros con confirmación."),

    ("Playbook: Nasdaq y tecnología",
     "El Nasdaq 100 (QQQ) y las tecnológicas (Apple, Nvidia, Tesla) son más VOLÁTILES y sensibles a los "
     "TIPOS de interés que el mercado amplio: subidas de tipos/rendimientos suelen presionar al "
     "'growth'. Gran actividad en la apertura de Wall Street; el VIX y los bonos marcan el tono de riesgo.",
     "Plan con Nasdaq/tech: alinéate con la tendencia del índice y con el entorno de tipos (dovish "
     "favorece tech; hawkish la presiona); usa la apertura para rupturas (ORB) y vigila el VIX. En "
     "acciones concretas, cuidado con los EARNINGS (gaps enormes) y opera los LÍDERES con fuerza "
     "relativa. La beta alta amplifica los movimientos del índice: ajusta el tamaño. Confirmación de "
     "volumen en rupturas de bases (taza con asa, CAN SLIM)."),
]

# ---- LOTE 10: playbooks por activo, patrones intradía, relaciones macro y rutinas ----
_BATCH10: list[tuple[str, str, str]] = [
    ("Playbook: Ethereum y altcoins",
     "Ethereum (ETH) es la segunda cripto y líder de las altcoins. Suele seguir a Bitcoin pero con "
     "MÁS beta (amplifica los movimientos). La 'altseason' llega cuando la dominancia de BTC cae y el "
     "capital rota a ETH y altcoins. Sensible a gas/red, staking, ETFs y al apetito de riesgo general.",
     "Plan con ETH/altcoins: primero mira a BTC y su dominancia (si BTC cae, las alts caen más; si BTC "
     "se estabiliza tras subir, puede empezar altseason). Opera las alts MÁS fuertes (fuerza relativa) "
     "solo en tendencia alcista de BTC. Usa stops amplios (volatilidad extrema) y tamaño reducido; las "
     "alts pequeñas son ilíquidas y manipulables. El ETH/BTC ratio indica si ETH lidera o rezaga. "
     "Evita perseguir 'pumps' parabólicos: espera retrocesos a zonas de valor."),

    ("Playbook: GBP/USD ('Cable')",
     "El GBP/USD ('Cable') es un par mayor VOLÁTIL, con rangos amplios. Se mueve sobre todo en la "
     "sesión de Londres, reacciona al Banco de Inglaterra (BoE), a los datos del Reino Unido y al "
     "riesgo político (elecciones, tensiones). Sensible también al dólar (DXY) y al sentimiento risk-on/off.",
     "Plan con Cable: opera en la sesión de Londres y el solape con Nueva York (máxima liquidez); "
     "alinéate con el sesgo del dólar y del BoE; respeta niveles redondos y soportes/resistencias. Por "
     "su volatilidad, usa stops adecuados (ATR alto) y evita el minuto de las noticias del Reino Unido "
     "y de EE. UU. El riesgo político puede provocar gaps y latigazos: reduce tamaño ante eventos. "
     "Buen par para tendencia, exigente para scalping por su ruido."),

    ("Playbook: USD/JPY",
     "El USD/JPY se rige por el DIFERENCIAL DE TIPOS EE.UU.–Japón y por los rendimientos de los bonos "
     "de EE. UU.: si suben los tipos/rendimientos USA, el par tiende a subir. El yen (JPY) es refugio: "
     "en risk-off SUBE (el par baja). El Banco de Japón (BoJ) y sus intervenciones pueden mover el par con fuerza.",
     "Plan con USD/JPY: vigila los rendimientos de los bonos de EE. UU. (correlación positiva con el "
     "par) y el tono de la Fed vs BoJ. En pánico de mercado (risk-off), espera fortaleza del yen "
     "(caídas del par) aunque los tipos digan otra cosa. Cuidado con las INTERVENCIONES del BoJ en "
     "niveles extremos (movimientos bruscos). Es un par clave del 'carry trade': se deshace violentamente "
     "en risk-off. Opera con el contexto macro, no solo el gráfico."),

    ("Playbook: S&P 500",
     "El S&P 500 (SPY/ES) es el índice de referencia del mercado de EE. UU. y termómetro global. "
     "Sensible a tipos de interés, resultados empresariales, el VIX y la AMPLITUD (breadth): una "
     "subida sostenida por pocas acciones es frágil. Los futuros (ES) operan casi 24h; la sesión "
     "clave es la de Nueva York.",
     "Plan con el S&P: define el sesgo de fondo con la tendencia (diario/semanal) y el entorno de "
     "tipos; usa la apertura de Wall Street para rupturas (ORB) y niveles del día previo; vigila el VIX "
     "(miedo) y la amplitud (línea A/D, TICK). Reacciona a la Fed y a los datos macro (evita el "
     "impacto). Los índices se confirman entre sí (S&P, Nasdaq, Dow). Es más 'ordenado' que activos "
     "individuales: respeta medias y niveles con confirmación de volumen."),

    ("Playbook: Plata (Silver)",
     "La plata (Silver/XAG) es un metal HÍBRIDO: refugio como el oro pero con fuerte componente "
     "INDUSTRIAL. Es más volátil que el oro (mayor beta) y con más ruido. Sigue la dirección del oro "
     "pero exagera sus movimientos. El ratio oro/plata (cuántas onzas de plata equivalen a una de oro) "
     "tiende a revertir a la media.",
     "Plan con la plata: usa el oro y el dólar (DXY) como brújula (dólar débil y tipos reales a la "
     "baja la favorecen); opera con stops amplios por su volatilidad. Cuando el ratio oro/plata está "
     "en un extremo histórico, suele corregir (plata muy barata frente al oro = posible recuperación). "
     "Añade el factor de demanda industrial (ciclo económico). La plata premia a quien respeta su "
     "volatilidad con tamaño prudente; castiga el exceso de apalancamiento."),

    ("Patrones por hora del día",
     "El día de trading tiene ritmos: la APERTURA (primera hora) suele ser la más volátil y direccional; "
     "el MEDIODÍA ('lunch lull') pierde volumen y se vuelve lateral/sucio; y la ÚLTIMA hora ('power "
     "hour') recupera volumen y movimiento. Operar en la hora equivocada da señales de baja calidad.",
     "Uso práctico: busca rupturas y tendencia en la apertura y el power hour; evita perseguir "
     "movimientos en el lunch lull (rango errático, falsas rupturas). En forex, los picos son las "
     "aperturas de Londres y Nueva York y su solape. Alinear la señal con la hora de mayor "
     "probabilidad mejora los resultados. Muchas 'malas rachas' vienen de operar en horas de baja "
     "liquidez: elige tus ventanas."),

    ("Día de tendencia vs día de rango",
     "Hay dos tipos de día: de TENDENCIA (abre cerca de un extremo y cierra cerca del contrario, un "
     "solo sentido) y de RANGO (oscila entre soporte y resistencia sin dirección). Identificarlo "
     "temprano decide la táctica: seguir tendencia o fade de extremos.",
     "Pistas de día de tendencia: apertura con fuerza, ruptura del balance inicial que se ACEPTA "
     "(no vuelve), pocas velas en contra. Día de rango: la apertura vuelve dentro del rango previo, "
     "los extremos se rechazan. En día de tendencia, no operes reversiones (te arrolla); en día de "
     "rango, no persigas rupturas (te barren). Adaptar el estilo al carácter del día es una habilidad "
     "clave del day trading en índices, forex y cripto."),

    ("Estrategia: cierre de gap (gap fill)",
     "En acciones e índices, un GAP de apertura (salto respecto al cierre previo) a menudo se 'rellena' "
     "cuando el precio vuelve al cierre anterior. Los gaps PEQUEÑOS sin noticia tienden a rellenarse "
     "(fade); los GRANDES con catalizador fuerte suelen continuar ('gap and go'). Distinguirlos es la clave.",
     "Plan: un gap moderado en contra de la tendencia y sin noticia relevante se puede operar hacia el "
     "cierre previo (fade del gap) con confirmación de rechazo. Un gap grande con volumen y noticia "
     "(earnings) suele continuar: opera a favor tras un pequeño retroceso ('gap and go'). Marca el "
     "cierre previo como objetivo/nivel. Gestiona el riesgo: si el 'fade' no funciona rápido, puede ser "
     "un gap de continuación. Estrategia clásica de la apertura bursátil."),

    ("Estrategia: ruptura del rango asiático (forex)",
     "En forex, la sesión ASIÁTICA suele ser tranquila y forma un rango estrecho. La estrategia marca "
     "el máximo y el mínimo de ese rango y opera su RUPTURA en la apertura de Londres, cuando entra la "
     "liquidez y el movimiento direccional del día. El otro extremo del rango sirve de stop.",
     "Pasos: (1) delimita el rango asiático (máx/mín). (2) espera la apertura de Londres. (3) opera la "
     "ruptura con volumen/impulso en su dirección; stop al otro lado del rango; objetivo = amplitud del "
     "rango o niveles clave. Filtra con la tendencia mayor y evita días de noticias importantes. Cuidado "
     "con la 'falsa ruptura' inicial (barrido de liquidez) antes del movimiento real: la 'turtle soup' "
     "puede aplicarse si la ruptura falla."),

    ("Estrategia: operar tras la noticia (retest)",
     "En vez de operar EN el dato (lotería de spreads y latigazos), una táctica más segura es esperar a "
     "que el mercado reaccione, rompa un nivel por la noticia y luego lo RETESTEE: se entra en el "
     "retest a favor de la nueva tendencia, con el impulso ya definido y los spreads normalizados.",
     "Pasos: (1) marca el nivel clave antes del dato y NO operes en el impacto. (2) tras la reacción, "
     "espera que el precio rompa y vuelva a probar el nivel roto (ahora soporte/resistencia). (3) entra "
     "con confirmación en la dirección del movimiento post-noticia; stop al otro lado. Deja que el "
     "mercado 'digiera' la noticia y muestre su sesgo. Convierte un evento peligroso en una entrada "
     "estructurada. Aplica a forex, índices y materias en datos macro/earnings."),

    ("Estacionalidad del calendario",
     "Existen sesgos estadísticos de calendario: el 'Santa Claus rally' (fortaleza a fin de año), el "
     "'efecto enero' (small caps), 'sell in May and go away' (verano más flojo en bolsa) y el efecto "
     "'turn of the month' (fuerza en torno al cambio de mes por flujos). Son PROBABILIDADES históricas, no certezas.",
     "Úsalos como contexto de fondo que refuerza (no sustituye) una tesis técnica. Los flujos "
     "institucionales (nóminas, rebalanceos de fin de mes/trimestre) crean patrones recurrentes. No "
     "operes 'solo por el calendario', pero si la estacionalidad y el gráfico coinciden, la probabilidad "
     "mejora. Verifica con datos actuales: los patrones estacionales se debilitan cuando se vuelven "
     "muy conocidos. Aplican sobre todo a índices y acciones."),

    ("Medidor de fuerza de divisas",
     "En forex conviene medir la FUERZA RELATIVA de cada divisa comparándola en todos sus pares: si el "
     "euro sube frente al dólar, la libra, el yen y el franco a la vez, el euro está fuerte 'de verdad'. "
     "La mejor operación es comprar la divisa MÁS fuerte contra la MÁS débil.",
     "Un movimiento en EUR/USD puede deberse a un euro fuerte O a un dólar débil: el medidor de fuerza "
     "lo distingue. Operar 'fuerte vs débil' maximiza el impulso y la probabilidad, frente a operar dos "
     "divisas ambas neutrales. Combina la fuerza de divisas con la estructura técnica del par elegido. "
     "Es una forma de aplicar la fuerza relativa (concepto universal) al mundo forex, mejorando la "
     "selección del par a operar."),

    ("Trades de correlación (materias y divisas)",
     "Algunas divisas están ligadas a materias primas: el dólar australiano (AUD) correlaciona con el "
     "ORO y con el ciclo de materias; el dólar canadiense (CAD) con el PETRÓLEO; la corona noruega "
     "(NOK) con el crudo. Estas relaciones sirven de confirmación y de alerta de divergencias.",
     "Ejemplo: si el oro sube con fuerza, el AUD suele acompañar (Australia es gran exportador); si el "
     "petróleo cae, el CAD se debilita (USD/CAD sube). Cuando la materia y su divisa DIVERGEN, avisa de "
     "un posible ajuste. Úsalas como confluencia intermercado: confirma tu tesis en el par con su "
     "materia asociada. Conocer estos enlaces mejora las decisiones en forex y materias, y evita "
     "operar contra una relación de fondo."),

    ("Divergencia de bancos centrales",
     "Una de las fuerzas más potentes en forex es la DIVERGENCIA de política monetaria: cuando un banco "
     "central sube tipos (hawkish) mientras otro los baja o mantiene (dovish), la divisa del primero "
     "tiende a fortalecerse frente a la del segundo de forma sostenida (sesgo de medio plazo).",
     "Operar 'a favor de la divergencia' (largo en la divisa del banco que endurece, corto en la del "
     "que relaja) alinea la operación con un viento macro de fondo. El mercado descuenta las "
     "EXPECTATIVAS de tipos, así que importa la sorpresa frente a lo esperado. Vigila reuniones, actas "
     "y discursos de la Fed, BCE, BoE, BoJ. Esta lógica de tipos guía las tendencias de fondo de los "
     "pares mayores; el técnico da el timing."),

    ("Relación bonos-acciones y curva de tipos",
     "Bonos y acciones suelen moverse de forma relacionada: en 'risk-on', suben las acciones y bajan "
     "los bonos (sube su rendimiento); en 'risk-off', se buscan bonos (refugio). La CURVA de tipos "
     "(corto vs largo plazo) es una brújula macro: una curva INVERTIDA (corto rinde más que largo) ha "
     "precedido recesiones.",
     "Subidas rápidas de los rendimientos suelen presionar a las acciones de crecimiento (tech). El "
     "rendimiento del bono a 10 años es una referencia clave del apetito de riesgo. Para el trader de "
     "índices, vigilar bonos y curva da contexto de fondo: operar largos de riesgo con rendimientos "
     "disparándose es ir contra la marea. La macro (tipos, curva) enmarca; el gráfico ejecuta. "
     "Relación esencial entre renta fija y variable."),

    ("Teoría de la 'sonrisa del dólar'",
     "La 'sonrisa del dólar' (Stephen Jen) explica cuándo se fortalece el USD: en los DOS extremos. "
     "En pánico global (risk-off) sube como refugio; y en fuerte crecimiento de EE. UU. (mejor que el "
     "resto) también sube. Se DEBILITA en el medio: crecimiento global sincronizado y moderado, con "
     "apetito de riesgo.",
     "Es una forma 'U' (sonrisa): dólar fuerte en miedo y en dominio económico USA; débil en la zona "
     "cómoda intermedia. Ayuda a interpretar por qué el DXY sube tanto en crisis como en auges de EE. "
     "UU. Para el trader: identifica en qué parte de la sonrisa estamos para anticipar el sesgo del "
     "dólar, que mueve forex, materias y mercados emergentes. Marco macro útil para el contexto de fondo."),

    ("Rotación sectorial con ETFs",
     "El mercado de acciones se divide en SECTORES (tecnología XLK, energía XLE, financieras XLF, salud "
     "XLV, consumo, utilities XLU…), y el capital ROTA entre ellos según el ciclo económico. Ver qué "
     "sector lidera o rezaga (fuerza relativa) da pistas de la fase del mercado y de dónde operar.",
     "En expansión temprana lideran tecnología y consumo discrecional; en fases tardías/inflacionarias, "
     "energía y materiales; en contracción, defensivos (salud, utilities, consumo básico). Operar los "
     "sectores y acciones más FUERTES al alza y los más débiles a la baja aprovecha la rotación. Los "
     "ETFs sectoriales permiten leer el mercado 'por dentro'. La amplitud sectorial confirma o "
     "cuestiona la salud de un rally del índice."),

    ("Dominancia de BTC y rotación cripto",
     "En cripto, la DOMINANCIA de Bitcoin (BTC.D, % de capitalización que es BTC) guía la rotación. "
     "BTC.D subiendo = el dinero se refugia en BTC (alts débiles); BTC.D cayendo con BTC estable o "
     "subiendo = 'altseason' (las altcoins superan a BTC). Es la brújula para decidir entre BTC y alts.",
     "Secuencia típica de ciclo: sube BTC primero (dominancia alta), luego rota a ETH (large caps) y "
     "después a altcoins pequeñas (dominancia baja, altseason). Operar altcoins con BTC cayendo es "
     "peligroso (caen más). Vigila BTC.D + el par ETH/BTC para el timing de rotación. Combina esta "
     "lectura macro-cripto con el on-chain, el funding y la estructura técnica de cada moneda. Guía "
     "específica y muy útil del mercado cripto."),

    ("Revisión semanal y calificación de operaciones",
     "El progreso viene de REVISAR: cada semana repasa tus operaciones, califica cada setup (A/B/C "
     "según confluencia y ejecución), y separa lo que funciona de lo que no. Anota qué activos, horas, "
     "estrategias y estados emocionales dan mejores y peores resultados. Sin revisión, repites errores.",
     "Preguntas de la revisión: ¿seguí mi plan? ¿tomé solo setups A? ¿respeté stops y tamaño? ¿qué "
     "patrón se repite en mis pérdidas? Con los datos, DOBLA en lo que funciona y elimina lo que no. La "
     "mejora es un bucle: operar → registrar → revisar → ajustar. Este sistema hace ese bucle con datos "
     "(precisión por activo/duración); tú puedes hacerlo también a nivel de proceso y disciplina. La "
     "consistencia nace de la revisión honesta."),

    ("Regla de riesgo diario (circuit breaker personal)",
     "Además del riesgo por operación (1-2%), fija un TOPE de pérdida DIARIA (p.ej. 3-6% o un número de "
     "operaciones perdedoras) y, al alcanzarlo, DETENTE por hoy. Es tu 'circuit breaker' personal "
     "contra el tilt y el revenge trading, que evita convertir un mal día en un desastre.",
     "Tras varias pérdidas seguidas, el juicio se deteriora y la tentación de 'recuperar' crece: parar "
     "protege el capital y la mente. Igualmente, considera un tope tras un gran día ganador (para no "
     "devolverlo por exceso de confianza). La disciplina de horario y de límites diarios distingue al "
     "profesional del jugador. Un sistema automatizado ayuda, pero la regla del día es tuya. Protege "
     "tu capital y tu estabilidad emocional."),

    ("Ejemplo de dimensionamiento de posición",
     "El tamaño se calcula desde el RIESGO, no desde el capricho. Fórmula: riesgo en dinero = capital × "
     "% de riesgo; tamaño = riesgo en dinero / distancia al stop. Así cada operación arriesga lo mismo, "
     "sin importar el activo ni la amplitud del stop.",
     "Ejemplo: capital 1.000, riesgo 2% = 20 de riesgo. Si el stop está a 50 puntos, el tamaño = 20/50 "
     "= 0,4 por punto. Si el stop fuera de 100 puntos, el tamaño baja a 0,2 (mismo riesgo, 20). Con "
     "esto, un stop más ancho NO significa más riesgo: significa menos tamaño. Ajusta el stop al ATR y "
     "el tamaño a la fórmula. Este cálculo, aplicado siempre, mantiene el riesgo homogéneo y controlado "
     "en todos los mercados y es la base de la supervivencia."),

    ("Incluir los costes en la esperanza",
     "La rentabilidad REAL es la esperanza BRUTA menos los COSTES (spread, comisiones, slippage, "
     "financiación). Un sistema con ventaja pequeña puede volverse perdedor tras costes, sobre todo en "
     "scalping y en binarias (payout <100%). Calcula siempre la esperanza NETA, no la ideal del backtest.",
     "Ejemplo: si tu ventaja media es +0,3R por operación pero los costes te cuestan 0,2R, la esperanza "
     "neta es solo +0,1R: frágil. Operar menos veces pero de más calidad reduce el peso de los costes. "
     "En binarias, el 'coste' estructural es el payout inferior al 100%: exige una ventaja clara por "
     "encima del punto de equilibrio. Ignorar los costes es el error que hace fracasar sistemas que "
     "'parecían' ganadores. Sé honesto con los números."),
]

# ---- LOTE 11: casos históricos (crisis/burbujas) como lecciones + glosario ----
_BATCH11: list[tuple[str, str, str]] = [
    ("Anatomía de una burbuja",
     "Charles Kindleberger ('Manias, Panics, and Crashes') describió las fases de toda burbuja: "
     "DESPLAZAMIENTO (algo nuevo entusiasma), AUGE (sube el crédito y la participación), EUFORIA "
     "(precios irracionales, 'esta vez es diferente'), toma de beneficios de los listos, y PÁNICO/"
     "colapso cuando la multitud huye a la vez.",
     "El patrón se repite en siglos y mercados: apalancamiento creciente, historias que justifican "
     "cualquier precio, entrada masiva de novatos en el pico y crac brutal. Señales de alerta: "
     "valoraciones extremas, FOMO generalizado, apalancamiento récord y desprecio del riesgo. Para el "
     "trader: la euforia es peligrosa aunque el precio suba; protege ganancias, reduce apalancamiento "
     "y desconfía del 'esta vez es diferente'. Las burbujas terminan siempre."),

    ("Tulipomanía y la burbuja de los Mares del Sur",
     "La tulipomanía (Holanda, 1637) y la burbuja de los Mares del Sur (1720) son las manías "
     "especulativas clásicas: precios que se dispararon por pura especulación y crédito, hasta "
     "colapsar y arruinar a multitudes. Hasta Isaac Newton perdió una fortuna en los Mares del Sur.",
     "Lección atemporal: la naturaleza humana (codicia, manada, FOMO) no cambia; solo cambian los "
     "activos de moda. Cuando un precio sube 'porque va a subir' y todos hablan de ello, el riesgo es "
     "máximo. Newton dijo poder calcular el movimiento de los astros, pero no la locura de la gente. "
     "Estos episodios recuerdan mantener la cabeza fría, gestionar el riesgo y no confundir una "
     "manía con una inversión."),

    ("Crash de 1929 y la Gran Depresión",
     "El crac de octubre de 1929 puso fin a los 'felices años 20': la especulación masiva COMPRANDO "
     "A MARGEN (con dinero prestado) infló la bolsa; cuando cayó, las llamadas de margen forzaron "
     "ventas en cascada. Siguió la Gran Depresión, con caídas de ~89% desde el pico y años de ruina.",
     "Lección principal: el APALANCAMIENTO amplifica el desastre. Comprar a crédito multiplica las "
     "ganancias en el auge y aniquila el capital en la caída (margin calls forzando ventas que hunden "
     "más el precio). También muestra que las recuperaciones pueden tardar AÑOS. Gestión de riesgo, "
     "apalancamiento prudente y no 'apostar la casa' son lecciones nacidas de 1929, válidas hoy en "
     "cualquier mercado."),

    ("Lunes Negro de 1987",
     "El 19 de octubre de 1987 el Dow Jones cayó ~22,6% EN UN SOLO DÍA (el peor porcentaje diario de "
     "la historia), sin una noticia clara que lo justificara. Lo amplificaron el 'program trading' y "
     "los 'seguros de cartera' (ventas automáticas que se retroalimentaron en cascada).",
     "Lección: los sistemas automáticos y el apalancamiento pueden crear cascadas de venta que se "
     "autoalimentan (feedback negativo). Un mercado puede desplomarse sin motivo fundamental evidente, "
     "solo por dinámica de flujos y pánico. De aquí nacieron los 'circuit breakers'. Para el trader: "
     "los movimientos extremos ocurren (colas gruesas), los stops pueden ejecutarse muy lejos, y no "
     "conviene estar sobreapalancado ante lo imprevisible."),

    ("LTCM 1998: apalancamiento y riesgo de cola",
     "Long-Term Capital Management, un fondo con premios Nobel (Merton, Scholes), usó un "
     "APALANCAMIENTO enorme confiando en modelos. En 1998, el impago de Rusia disparó correlaciones y "
     "pérdidas que sus modelos creían 'imposibles'; casi provocó una crisis sistémica y la Fed "
     "organizó su rescate.",
     "Lección: la genialidad y los modelos NO salvan del riesgo de cola ni del apalancamiento "
     "excesivo. En crisis, las correlaciones se van a 1 y lo 'imposible' ocurre. Un edge real puede "
     "arruinarte si el tamaño/apalancamiento te expone a la ruina en el evento raro. Sobrevivir "
     "primero: tamaño prudente, sin apalancamiento extremo, y respeto por las colas. La humildad ante "
     "la incertidumbre es gestión de riesgo."),

    ("Burbuja punto-com (2000)",
     "A finales de los 90, cualquier empresa 'punto-com' se disparaba sin beneficios ni modelo de "
     "negocio ('ojos' en vez de ingresos). El Nasdaq alcanzó su pico en marzo de 2000 y luego se "
     "desplomó ~78% en los años siguientes, arruinando a quienes compraron la euforia en el techo.",
     "Lección: en la euforia se ignoran los fundamentales y se paga cualquier precio por una historia. "
     "Muchas empresas quebraron; algunas (Amazon) sobrevivieron tras caer >90%. La tecnología era real, "
     "pero las VALORACIONES eran insostenibles. Distingue la innovación (buena) de la burbuja de "
     "precios (peligrosa). Para el trader: la fuerza relativa y la tendencia importan, pero el riesgo "
     "de comprar en la cima de una manía es de ruina."),

    ("Crisis financiera global de 2008",
     "La burbuja inmobiliaria de EE. UU. y las hipotecas 'subprime' empaquetadas en productos "
     "complejos y apalancados provocaron, con la quiebra de Lehman Brothers (septiembre 2008), una "
     "crisis sistémica: congelación del crédito, caídas de ~50% en bolsa y recesión global.",
     "Lecciones: el riesgo oculto y el apalancamiento del sistema pueden estallar de golpe; la "
     "confianza (liquidez) desaparece en un instante; y lo 'seguro' (hipotecas AAA) puede no serlo. "
     "Los bancos centrales respondieron con rescates y QE. Para el trader: vigila el riesgo "
     "sistémico y de crédito, no te fíes de la calma aparente, y recuerda que en el pánico casi todo "
     "cae junto. La gestión de riesgo y la liquidez son la diferencia entre sobrevivir o no."),

    ("Flash Crash de 2010",
     "El 6 de mayo de 2010, el Dow cayó cerca de 1.000 puntos en MINUTOS y se recuperó casi igual de "
     "rápido. La liquidez desapareció de golpe (algoritmos retirándose), algunas acciones se operaron "
     "a céntimos o miles de dólares por instantes. Fue un colapso de MICROESTRUCTURA, no de fundamentales.",
     "Lección: en momentos de estrés, la liquidez puede evaporarse y los precios saltar de forma "
     "absurda; los STOPS de mercado se ejecutan a precios terribles (slippage brutal). Por eso, en "
     "activos o momentos ilíquidos, cuidado con confiar solo en stops de mercado y no colocarlos en "
     "niveles obvios. Los flash crashes se repiten (mini-versiones en cripto y otros). Prepárate para "
     "lo extremo con tamaño y órdenes adecuadas."),

    ("Crisis del euro y 'whatever it takes' (2010-2012)",
     "La crisis de deuda europea (Grecia y periféricos) amenazó la existencia del euro. Los "
     "rendimientos de la deuda se dispararon y el pánico se extendió. En julio de 2012, Mario Draghi "
     "(BCE) prometió hacer 'lo que sea necesario' ('whatever it takes') y calmó los mercados casi de inmediato.",
     "Lección: los BANCOS CENTRALES son actores decisivos; una sola frase creíble puede cambiar la "
     "tendencia de mercados enteros. Operar contra una intervención masiva de un banco central es "
     "peligroso ('don't fight the central bank'). La política monetaria y la credibilidad mueven bonos, "
     "divisas y bolsa. Para el trader: entiende quién tiene el poder de cambiar el juego y no te "
     "posiciones ciegamente contra él."),

    ("El franco suizo de 2015 (cisne negro de forex)",
     "El 15 de enero de 2015, el Banco Nacional Suizo ELIMINÓ por sorpresa el suelo de 1,20 en EUR/CHF. "
     "El franco se disparó ~30% en minutos, con gaps enormes. Muchos traders y varios brokers "
     "quebraron (saldos negativos imposibles de cubrir): un cisne negro de manual en forex.",
     "Lecciones: los 'pegs' y suelos ROMPEN, y cuando lo hacen el movimiento es instantáneo y sin "
     "liquidez (los stops no protegen, hay gaps). El apalancamiento convirtió posiciones normales en "
     "ruinas y saldos negativos. Reafirma: cuidado con el apalancamiento, con la falsa seguridad de "
     "niveles 'defendidos', y con el riesgo de contraparte (broker). Lo 'imposible' ocurre; el tamaño "
     "prudente es tu única defensa real."),

    ("Brexit 2016",
     "El 23 de junio de 2016, el referéndum del Brexit sorprendió con la victoria del 'Leave'. La "
     "libra (GBP) se desplomó durante la noche a mínimos de décadas con volatilidad extrema, mientras "
     "las encuestas y los mercados habían descontado lo contrario. Un evento binario de alto impacto.",
     "Lección: los eventos políticos BINARIOS (referéndums, elecciones) crean riesgo de gap enorme e "
     "impredecible; el mercado puede descontar un resultado y equivocarse. Mantener posiciones "
     "apalancadas de corto plazo sobre estos eventos es una lotería. Lo prudente suele ser reducir "
     "exposición antes y operar la tendencia YA formada después. La incertidumbre política se traduce "
     "en volatilidad y saltos; gestiónala con tamaño y prudencia."),

    ("Volmageddon 2018 (colapso del short-vol)",
     "El 5 de febrero de 2018, un repunte del VIX hizo colapsar los productos que APOSTABAN CONTRA la "
     "volatilidad (como el ETN 'XIV', que cayó ~96% y se liquidó). Muchos habían vendido volatilidad "
     "durante años cobrando primas pequeñas... hasta que un día el riesgo de cola los borró.",
     "Lección clásica de asimetría: vender volatilidad (o cualquier estrategia de 'recoger centavos "
     "delante de una apisonadora') gana poco y constante hasta la catástrofe. La distribución de "
     "resultados con cola izquierda gorda arruina. Desconfía de estrategias con muchas ganancias "
     "pequeñas y una pérdida potencial enorme (como la martingala). Prefiere payoffs convexos y protege "
     "siempre la cola. La volatilidad reprimida explota."),

    ("Crash del COVID (marzo 2020)",
     "En febrero-marzo de 2020, la pandemia provocó el desplome más RÁPIDO de la historia: el S&P 500 "
     "cayó ~34% en unas cinco semanas, con circuit breakers activados varios días. Luego, ante el "
     "estímulo masivo de la Fed y los gobiernos, el mercado se recuperó con igual velocidad.",
     "Lecciones: los cracks pueden ser vertiginosos y globales (todo cae junto, la correlación va a 1); "
     "pero la respuesta de los bancos centrales (liquidez, tipos) puede girar el mercado de golpe. El "
     "pánico extremo (VIX >80) coincidió con el suelo. Para el trader: gestiona el riesgo antes del "
     "shock, no vendas en el pánico máximo, y respeta el poder de la liquidez de los bancos centrales "
     "para cambiar la tendencia. La velocidad de 2020 redefinió lo posible."),

    ("GameStop y las meme stocks (2021)",
     "En enero de 2021, operadores minoristas coordinados (foros como WallStreetBets) provocaron un "
     "'short squeeze' en GameStop (GME) y otras acciones muy cortas: el precio se multiplicó, fondos "
     "cortos sufrieron pérdidas enormes y algunos brokers RESTRINGIERON la compra en pleno frenesí.",
     "Lecciones: una posición corta muy MASIFICADA es combustible para un squeeze (los cortos "
     "atrapados compran y disparan el precio); el 'gamma squeeze' de opciones amplifica. El sentimiento "
     "social y la coordinación minorista pueden mover mercados a corto plazo, pero la mayoría que "
     "entró tarde perdió cuando reventó. Cuidado con perseguir manías parabólicas y con el "
     "posicionamiento extremo (contrarian). La liquidez y las reglas del broker importan."),

    ("Colapso de Terra/LUNA y UST (2022)",
     "En mayo de 2022, la stablecoin ALGORÍTMICA UST (Terra) perdió su paridad con el dólar y su token "
     "LUNA entró en una espiral de muerte: se hiperinfló hasta casi cero, borrando decenas de miles de "
     "millones en días. El mecanismo 'reflexivo' que la sostenía se volvió en su contra.",
     "Lecciones: las stablecoins ALGORÍTMICAS (sin respaldo real sólido) son frágiles y pueden colapsar "
     "en una espiral reflexiva; rendimientos 'garantizados' altísimos (Anchor pagaba ~20%) son una "
     "señal de alarma. El contagio arrastró a todo el sector cripto. Verifica el RESPALDO de cualquier "
     "stablecoin y desconfía de lo que promete rentabilidad imposible. En cripto, el riesgo de "
     "protocolo/token es tan real como el de mercado."),

    ("Caída de FTX (2022)",
     "En noviembre de 2022, FTX —el segundo mayor exchange de cripto— quebró en días al descubrirse "
     "que había USADO los fondos de sus clientes. Millones de usuarios perdieron acceso a su dinero. "
     "Fue un caso de FRAUDE y mala gestión, no de mercado, con enorme contagio de confianza.",
     "Lección capital: el riesgo de CONTRAPARTE/custodia es real; 'not your keys, not your coins'. Un "
     "exchange grande y 'respetable' puede ser insolvente o fraudulento. Mitigación: usa plataformas "
     "reguladas y solventes, no dejes más fondos de los necesarios, y para el largo plazo considera la "
     "autocustodia. Ninguna estrategia te protege si pierdes los fondos por el colapso del custodio. "
     "La seguridad de dónde guardas el dinero es parte de la gestión de riesgo."),

    ("Reflexividad (George Soros)",
     "George Soros formuló la REFLEXIVIDAD: los precios no solo reflejan los fundamentales, también los "
     "INFLUYEN, en un bucle de retroalimentación. Precios al alza mejoran el sentimiento y el acceso a "
     "crédito, que suben más los precios... hasta que el bucle se invierte y crea el crac. Explica auges y burbujas.",
     "La reflexividad rompe la idea de mercados perfectamente eficientes: las percepciones cambian la "
     "realidad, que cambia las percepciones. Para el trader: en tendencias fuertes, el bucle "
     "reflexivo puede llevar los precios más lejos y más tiempo de lo 'razonable' (no luches contra "
     "la tendencia solo por valoración); pero cuando el bucle se agota, el giro es violento. Reconocer "
     "en qué fase del bucle estamos ayuda a operar auges y colapsos con respeto."),

    ("Lecciones transversales de las crisis",
     "Todas las crisis comparten patrones: APALANCAMIENTO excesivo, exceso de confianza, liquidez que "
     "desaparece justo cuando se necesita, correlaciones que se van a 1, y la multitud entrando en el "
     "pico y huyendo en el suelo. 'La historia no se repite, pero rima' (atribuido a Mark Twain).",
     "Conclusiones para operar: (1) el apalancamiento es la causa número uno de ruina; (2) gestiona "
     "SIEMPRE el riesgo, la calma engaña; (3) la diversificación falla en el pánico, ten refugios/"
     "efectivo; (4) los stops pueden fallar por gaps: el tamaño prudente es la defensa real; (5) no "
     "sigas a la manada en los extremos. Estudiar las crisis pasadas prepara para las futuras, aunque "
     "cambien de disfraz. Sobrevivir es ganar."),

    ("Glosario esencial: posiciones y órdenes",
     "Términos base: LARGO (compras esperando que suba), CORTO (vendes en descubierto esperando que "
     "baje), STOP-LOSS (orden que cierra para limitar pérdidas), TAKE-PROFIT (cierra en ganancia), "
     "SPREAD (diferencia compra/venta), SLIPPAGE (ejecución a peor precio), DRAWDOWN (caída desde un máximo).",
     "Más términos: 'liquidar' (cerrar una posición), 'apalancamiento' (operar con más de tu capital), "
     "'margen' (garantía requerida), 'exposición' (cuánto riesgo tienes abierto), 'volatilidad' "
     "(magnitud de las oscilaciones). Dominar el vocabulario evita errores costosos por malentendidos. "
     "Un largo gana si sube; un corto gana si baja. El stop-loss es imprescindible en toda operación. "
     "Estos conceptos son la base común de todos los mercados."),

    ("Glosario esencial: forex y apalancamiento",
     "En forex: un PIP es el menor movimiento estándar de un par (habitualmente el 4º decimal, o el 2º "
     "en pares con yen). Un LOTE estándar son 100.000 unidades (mini 10.000, micro 1.000). El "
     "APALANCAMIENTO (p.ej. 1:30, 1:100) permite controlar una posición grande con poco MARGEN (garantía).",
     "El valor de un pip depende del tamaño de la posición: en un lote estándar, ~10 unidades de la "
     "divisa cotizada por pip. El apalancamiento amplifica ganancias y pérdidas por igual: 1:100 "
     "significa que un 1% en contra puede borrar tu margen. Calcula el tamaño por el RIESGO (distancia "
     "al stop y 1-2% del capital), no por el margen disponible. Entender pips, lotes y margen es "
     "imprescindible para dimensionar y gestionar el riesgo en forex."),

    ("Mercado alcista vs bajista (definiciones)",
     "Un mercado ALCISTA ('bull') es una tendencia sostenida al alza (suele definirse por una subida "
     ">20% desde mínimos); uno BAJISTA ('bear') es una caída sostenida (>20% desde máximos). Hay "
     "tendencias SECULARES (años/décadas) y CÍCLICAS (meses/pocos años) dentro de ellas.",
     "En mercado alcista, las estrategias al alza (comprar retrocesos, seguir tendencia) funcionan "
     "mejor; en bajista, los rebotes son para vender y las caídas más rápidas. Reconocer el RÉGIMEN "
     "(alcista/bajista/lateral) con medias largas y estructura evita aplicar la táctica equivocada. "
     "Los 'rallies de mercado bajista' (rebotes fuertes dentro de una tendencia bajista) engañan a "
     "muchos. Alinear la operativa con el mercado mayor es de las decisiones más rentables."),

    ("Liquidez y profundidad: por qué importan",
     "La LIQUIDEZ es la facilidad de comprar/vender sin mover el precio; la PROFUNDIDAD es cuánto "
     "volumen aguanta cada nivel del libro. Un activo líquido (majors de forex, grandes índices, BTC) "
     "tiene spreads estrechos y ejecución fiable; uno ilíquido (small caps, altcoins) da spreads "
     "amplios, slippage y saltos.",
     "Operar en activos y horas líquidas reduce costes y sorpresas; en ilíquidos, una orden grande "
     "mueve el precio en tu contra y los stops se ejecutan lejos. La liquidez DESAPARECE en crisis "
     "(flash crashes). Prefiere mercados profundos para operar con tamaño; en ilíquidos, reduce tamaño "
     "y usa límites. La liquidez es un factor de riesgo tan importante como la dirección: sin ella, "
     "incluso una buena señal se ejecuta mal."),
]

# Todos los lotes y el conjunto completo (para count() y recuperación)
_BATCHES: dict[int, list[tuple[str, str, str]]] = {
    1: _BATCH1, 2: _BATCH2, 3: _BATCH3, 4: _BATCH4, 5: _BATCH5, 6: _BATCH6,
    7: _BATCH7, 8: _BATCH8, 9: _BATCH9, 10: _BATCH10, 11: _BATCH11}
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
