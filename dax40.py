import yfinance as yf
import pandas as pd
from datetime import datetime
import os

# === Gültige Yahoo Finance Ticker für DAX40 ===
dax40_tickers = {
    "Adidas": "ADS.DE", "Airbus": "AIR.DE", "Allianz": "ALV.DE", "BASF": "BAS.DE",
    "Bayer": "BAYN.DE", "Beiersdorf": "BEI.DE", "BMW": "BMW.DE", "Brenntag": "BNR.DE",
    "Commerzbank": "CBK.DE", "Continental": "CON.DE", "Covestro": "1COV.DE", "Daimler Truck": "DTG.DE",
    "Deutsche Bank": "DBK.DE", "Deutsche Börse": "DB1.DE", "Deutsche Post": "DHL.DE",
    "Deutsche Telekom": "DTE.DE", "E.ON": "EOAN.DE", "Fresenius": "FRE.DE",
    "Fresenius Medical Care": "FME.DE", "Hannover Rück": "HNR1.DE", "Heidelberg Materials": "HEI.DE",
    "Henkel": "HEN3.DE", "Infineon": "IFX.DE", "Mercedes-Benz": "MBG.DE",
    "Merck": "MRK.DE", "Münchener Rück": "MUV2.DE", "Porsche": "P911.DE",
    "Qiagen": "QIA.DE", "Rheinmetall": "RHM.DE", "RWE": "RWE.DE",
    "SAP": "SAP.DE", "Sartorius": "SRT3.DE", "Siemens": "SIE.DE",
    "Siemens Energy": "ENR.DE", "Siemens Healthineers": "SHL.DE",
    "Symrise": "SY1.DE", "Volkswagen": "VOW3.DE", "Vonovia": "VNA.DE",
    "Zalando": "ZAL.DE", "MTU Aero Engines": "MTX.DE", "Scout24": "G24.DE"
}

# === Daten abrufen und berechnen ===
rows = []
today = datetime.now().strftime("%Y-%m-%d")

for name, ticker in dax40_tickers.items():
    try:
        data = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if data.empty:
            print(f"⚠️ Keine Daten für {name} ({ticker}) – übersprungen.")
            continue

        # Berechnungen
        close = data["Close"]
        change_5 = (close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) > 5 else 0
        change_15 = (close.iloc[-1] / close.iloc[-16] - 1) * 100 if len(close) > 15 else 0
        volatility = close.pct_change().std() * 100

        # Einfache Einschätzung basierend auf Veränderung
        steigt = round(max(0, min(100, 50 + change_5 / 2)), 1)
        fällt = round(max(0, min(100, 50 - change_5 / 2)), 1)
        bleibt = round(100 - (steigt + fällt) / 2, 1)

        einschätzung_1_5 = "Positiv" if change_5 > 0 else "Negativ"
        einschätzung_2_3W = "Positiv" if change_15 > 0 else "Negativ"

        diff_1_5 = abs(steigt - fällt)
        diff_2_3w = abs(change_15)

        rows.append([
            name, today, steigt, bleibt, fällt, einschätzung_1_5,
            steigt + 2, bleibt - 1, fällt - 1, einschätzung_2_3W,
            round(change_5, 2), round(change_15, 2), round(volatility, 2),
            round(diff_1_5, 2), round(diff_2_3w, 2)
        ])
    except Exception as e:
        print(f"⚠️ Fehler bei {name}: {e}")
        continue

# === DataFrame erzeugen ===
cols = [
    "Aktie", "Datum",
    "1-5T_Steigt", "1-5T_Bleibt", "1-5T_Fällt", "Einschätzung_1-5T",
    "2-3W_Steigt", "2-3W_Bleibt", "2-3W_Fällt", "Einschätzung_2-3W",
    "5T_Change(%)", "15T_Change(%)", "Volatilität(%)", "Diff_1-5", "Diff_2-3W"
]

df = pd.DataFrame(rows, columns=cols)

# === Sortieren nach größter Differenz (stärkste Bewegung zuerst) ===
df = df.sort_values(by="Diff_1-5", ascending=False)

# === Alte Dateien löschen ===
for f in os.listdir("."):
    if f.startswith("dax40_") and f.endswith(".csv"):
        os.remove(f)

# === Neue CSV speichern ===
filename = f"dax40_{today}.csv"
df.to_csv(filename, index=False)
print(f"✅ Datei erstellt: {filename} mit {len(df)} Einträgen.")
