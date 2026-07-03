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

_SEED_VERSION = 5
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

# Todos los lotes y el conjunto completo (para count() y recuperación)
_BATCHES: dict[int, list[tuple[str, str, str]]] = {
    1: _BATCH1, 2: _BATCH2, 3: _BATCH3, 4: _BATCH4, 5: _BATCH5}
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
