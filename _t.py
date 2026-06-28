import compileall, re
print("compile:", compileall.compile_dir(".", quiet=1, force=True, rx=re.compile(r"\.venv")))
from analysis import social
from data.calendar import economic_events, major_event_soon, earnings_soon
from config import SYMBOLS_BY_KEY
# Fear&Greed mapea a -1..1; sin red devuelve None (sandbox)
s=social.market_sentiment(SYMBOLS_BY_KEY["BTCUSDT"])
print("social cripto (sandbox sin red -> None):", s)
print("económicos (sandbox -> []):", economic_events()[:1])
print("imports OK")
