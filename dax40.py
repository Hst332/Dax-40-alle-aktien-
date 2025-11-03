import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ta
import os

# === DAX40 Symbole ===
dax40 = {
    "Adidas": "ADS.DE", "Airbus": "AIR.DE", "Allianz": "ALV.DE", "BASF": "BAS.DE",
    "Bayer": "BAYN.DE", "Beiersdorf": "BEI.DE", "BMW": "BMW.DE", "Brenntag": "BNR.DE",
    "Commerzbank": "CBK.DE", "Continental": "CON.DE", "Covestro": "1COV.DE",
    "Daimler Truck": "DTG.DE", "Deutsche Bank": "DBK.DE", "Deutsche Börse": "DB1.DE",
    "Deutsche Post": "DPW.DE", "Deutsche Telekom": "DTE.DE", "E.ON": "EOAN.DE",
    "Fresenius": "FRE.DE", "Fresenius Medical Care": "FME.DE", "Hannover Rück": "HNR1.DE",
    "Heidelberg Materials": "HEI.DE", "Henkel": "HEN3.DE", "Infineon": "IFX.DE",
    "Mercedes-Benz": "MBG.DE", "Merck": "MRK.DE", "Münchener Rück": "MUV2.DE",
    "Porsche": "P911.DE", "Qiagen": "QIA.DE", "Rheinmetall": "RHM.DE",
    "RWE": "RWE.DE", "SAP": "SAP.DE", "Sartorius": "SRT.DE", "Siemens": "SIE.DE",
    "Siemens Energy": "ENR.DE", "Siemens Healthineers": "SHL.DE", "Symrise": "SY1.DE",
    "Volkswagen": "VOW3.DE", "Vonovia": "VNA.DE", "Zalando": "ZAL.DE",
    "MTU Aero Engines": "MTX.DE", "Scout24": "G24.DE"
}

# === DataFrame vorbereiten ===
rows = []
datum = datetime.now().strftime("%Y-%m-%d")

for name, ticker in dax40.items():
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)

        if df.empty or len(df) < 5:
            print(f"⚠️ Keine Daten für {name}")
            continue

        df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
        df["Volatility"] = (df["High"] - df["Low"]) / df["Close"] * 100

        # letzte Werte
        rsi = df["RSI"].iloc[-1]
        vol = df["Volatility"].tail(5).mean()
        change_5 = (df["Close"].iloc[-1] / df["Close"].iloc[-6] - 1) * 100 if len(df) > 6 else np.nan
        change_15 = (df["Close"].iloc[-1] / df["Close"].iloc[-16] - 1) * 100 if len(df) > 16 else np.nan

        # einfache Einschätzungen
        if rsi < 35:
            tendenz = "Überverkauft"
            steigt = 60
            fällt = 20
        elif rsi > 65:
            tendenz = "Überkauft"
            steigt = 20
            fällt = 60
        else:
            tendenz = "Neutral"
            steigt = 40
            fällt = 30

        bleibt = 100 - (steigt + fällt) // 2
        diff_1_5 = abs(steigt - fällt)
        diff_2_3w = abs(change_5 - change_15) if not np.isnan(change_5) and not np.isnan(change_15) else diff_1_5

        rows.append([
            name, datum, round(steigt, 1), round(bleibt, 1), round(fällt, 1), tendenz,
            round(steigt + 5, 1), round(bleibt - 5, 1), round(fällt, 1), f"RSI {rsi:.1f}, {tendenz}",
            round(rsi, 1), round(change_5, 2), round(change_15, 2), round(vol, 2), round(diff_1_5, 1), round(diff_2_3w, 1)
        ])

    except Exception as e:
        print(f"⚠️ Fehler bei {name}: {e}")
        continue

# === CSV erzeugen ===
df_final = pd.DataFrame(rows, columns=[
    "Aktie", "Datum", "1-5T_Steigt", "1-5T_Bleibt", "1-5T_Fällt", "Einschätzung_1-5T",
    "2-3W_Steigt", "2-3W_Bleibt", "2-3W_Fällt", "Einschätzung_2-3W",
    "RSI", "5T_Change(%)", "15T_Change(%)", "Volatilität(%)", "Diff_1-5", "Diff_2-3W"
])

df_final = df_final.sort_values(by="Diff_1-5", ascending=False)

# alte CSV löschen
for f in os.listdir("."):
    if f.startswith("dax40_analysis_") and f.endswith(".csv"):
        os.remove(f)

csv_name = f"dax40_analysis_{datum}.csv"
df_final.to_csv(csv_name, index=False)
print(f"✅ Neue Datei erstellt: {csv_name} mit {len(df_final)} Einträgen.")
