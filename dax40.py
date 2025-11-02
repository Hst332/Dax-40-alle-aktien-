import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
import os

# === DAX40 Ticker-Liste (aktuell gültige Yahoo-Ticker) ===
dax_tickers = {
    "Adidas": "ADS.DE", "Airbus": "AIR.DE", "Allianz": "ALV.DE", "BASF": "BAS.DE",
    "Bayer": "BAYN.DE", "Beiersdorf": "BEI.DE", "BMW": "BMW.DE", "Brenntag": "BNR.DE",
    "Commerzbank": "CBK.DE", "Continental": "CON.DE", "Daimler Truck": "DTX.DE",
    "Deutsche Bank": "DBK.DE", "Deutsche Börse": "DB1.DE", "Deutsche Post": "DPW.DE",
    "Deutsche Telekom": "DTE.DE", "E.ON": "EOAN.DE", "Fresenius": "FRE.DE",
    "Fresenius Medical Care": "FME.DE", "GEA": "G1A.DE", "Hannover Rück": "HNR1.DE",
    "Heidelberg Materials": "HEI.DE", "Henkel": "HEN3.DE", "Infineon": "IFX.DE",
    "Mercedes-Benz": "MBG.DE", "Merck": "MRK.DE", "MTU Aero Engines": "MTX.DE",
    "Münchener Rück": "MUV2.DE", "Porsche": "PAH3.DE", "Qiagen": "QIA.DE",
    "Rheinmetall": "RHM.DE", "RWE": "RWE.DE", "SAP": "SAP.DE", "Scout24": "S24.DE",
    "Siemens": "SIE.DE", "Siemens Energy": "ENR.DE", "Siemens Healthineers": "SHL.DE",
    "Symrise": "SY1.DE", "Volkswagen": "VOW3.DE", "Vonovia": "VNA.DE", "Zalando": "ZAL.DE"
}

# === Helper-Funktion RSI ===
def compute_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# === Datenverarbeitung ===
rows = []
for name, ticker in dax_tickers.items():
    try:
        data = yf.download(ticker, period="1mo", interval="1d", progress=False, auto_adjust=True)
        if data.empty:
            print(f"⚠️ Keine Daten für {name}, überspringe")
            continue

        data["RSI"] = compute_rsi(data["Close"])

        # Kennzahlen
        pct_5d = data["Close"].pct_change(5).iloc[-1]
        pct_15d = data["Close"].pct_change(15).iloc[-1] if len(data) > 15 else np.nan
        rsi = data["RSI"].iloc[-1]
        vol = data["Close"].pct_change().std() * 100

        # NaN abfangen
        pct_5d = 0 if pd.isna(pct_5d) else pct_5d * 100
        pct_15d = 0 if pd.isna(pct_15d) else pct_15d * 100
        rsi = 50 if pd.isna(rsi) else rsi

        # Kurzfristige Einschätzung
        if rsi < 40 or pct_5d > 2:
            short_up, short_same, short_down = 50, 30, 20
            short_comment = "Bullish, Momentum positiv."
        elif rsi > 60 or pct_5d < -2:
            short_up, short_same, short_down = 25, 35, 40
            short_comment = "Bearish, überkauft oder schwach."
        else:
            short_up, short_same, short_down = 35, 45, 20
            short_comment = "Neutral, Seitwärtstendenz."

        # Mittelfristige Einschätzung
        if pct_15d > 3:
            mid_up, mid_same, mid_down = 50, 30, 20
            mid_comment = "Mittelfristig positiv."
        elif pct_15d < -3:
            mid_up, mid_same, mid_down = 30, 30, 40
            mid_comment = "Mittelfristig schwach."
        else:
            mid_up, mid_same, mid_down = 40, 40, 20
            mid_comment = "Stabiler Verlauf erwartet."

        rows.append([
            name, short_up, short_same, short_down, short_comment,
            mid_up, mid_same, mid_down, mid_comment,
            round(rsi,2), round(pct_5d,2), round(pct_15d,2), round(vol,2)
        ])
    except Exception as e:
        print(f"⚠️ Fehler bei {name}: {e}")

# === DataFrame erstellen ===
cols = [
    "Aktie",
    "1-5T_Steigt", "1-5T_Bleibt", "1-5T_Fällt", "Einschätzung_1-5T",
    "2-3W_Steigt", "2-3W_Bleibt", "2-3W_Fällt", "Einschätzung_2-3W",
    "RSI", "5T_Change(%)", "15T_Change(%)", "Volatilität(%)"
]
df = pd.DataFrame(rows, columns=cols)

# === Zusatzspalten für Sortierung ===
df["Diff_1-5"] = abs(df["1-5T_Steigt"] - df["1-5T_Fällt"])
df["Diff_2-3W"] = abs(df["2-3W_Steigt"] - df["2-3W_Fällt"])
df = df.sort_values(by="Diff_1-5", ascending=False)

# === Datum einfügen ===
datum = datetime.now().strftime("%Y-%m-%d")
df.insert(1, "Datum", datum)

# === Alte CSV löschen ===
for f in os.listdir("."):
    if f.startswith("dax40_probabilities_") and f.endswith(".csv"):
        os.remove(f)

# === Neue CSV speichern ===
csv_name = f"dax40_probabilities_{datum}.csv"
df.to_csv(csv_name, index=False)

print(f"✅ Neue Datei erstellt: {csv_name}")
