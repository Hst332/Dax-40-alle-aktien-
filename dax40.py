import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from ta.momentum import RSIIndicator

# === DAX40 Yahoo-Ticker ===
dax40_tickers = {
    "Adidas": "ADS.DE",
    "Airbus": "AIR.DE",
    "Allianz": "ALV.DE",
    "BASF": "BAS.DE",
    "Bayer": "BAYN.DE",
    "Beiersdorf": "BEI.DE",
    "BMW": "BMW.DE",
    "Brenntag": "BNR.DE",
    "Commerzbank": "CBK.DE",
    "Continental": "CON.DE",
    "Daimler Truck": "DTG.DE",
    "Deutsche Bank": "DBK.DE",
    "Deutsche Börse": "DB1.DE",
    "Deutsche Post": "DPW.DE",
    "Deutsche Telekom": "DTE.DE",
    "E.ON": "EOAN.DE",
    "Fresenius": "FRE.DE",
    "Fresenius Medical Care": "FME.DE",
    "GEA": "G1A.DE",
    "Hannover Rück": "HNR1.DE",
    "Heidelberg Materials": "HEI.DE",
    "Henkel": "HEN3.DE",
    "Infineon": "IFX.DE",
    "Mercedes-Benz": "MBG.DE",
    "Merck": "MRK.DE",
    "MTU Aero Engines": "MTX.DE",
    "Münchener Rück": "MUV2.DE",
    "Porsche": "PAH3.DE",
    "Qiagen": "QIA.DE",
    "Rheinmetall": "RHM.DE",
    "RWE": "RWE.DE",
    "SAP": "SAP.DE",
    "Scout24": "S24.DE",
    "Siemens": "SIE.DE",
    "Siemens Energy": "ENR.DE",
    "Siemens Healthineers": "SHL.DE",
    "Symrise": "SY1.DE",
    "Volkswagen": "VOW3.DE",
    "Vonovia": "VNA.DE",
    "Zalando": "ZAL.DE"
}

# === Funktion zur Berechnung Wahrscheinlichkeiten ===
def calc_probabilities(df, short_days=5, mid_days=15):
    # 5-Tage und 15-Tage Veränderung
    df["5T_Change"] = df["Close"].pct_change(periods=short_days) * 100
    df["15T_Change"] = df["Close"].pct_change(periods=mid_days) * 100
    df["Volatility"] = df["Close"].pct_change().rolling(window=5).std() * 100
    
    # RSI
    rsi = RSIIndicator(df["Close"], window=14).rsi()
    last_rsi = rsi.iloc[-1] if not rsi.empty else 50
    
    last_5_change = df["5T_Change"].iloc[-1] if not df["5T_Change"].empty else 0
    last_15_change = df["15T_Change"].iloc[-1] if not df["15T_Change"].empty else 0
    vol = df["Volatility"].iloc[-1] if not df["Volatility"].empty else 0

    # Kurzfristig
    prob_steigt = np.clip(50 + last_rsi/2 + last_5_change, 0, 100)
    prob_faellt = np.clip(50 - last_rsi/2 - last_5_change, 0, 100)
    prob_bleibt = max(0, 100 - prob_steigt - prob_faellt)
    
    # Mittelfristig
    prob_2w_steigt = np.clip(50 + last_15_change, 0, 100)
    prob_2w_faellt = np.clip(50 - last_15_change, 0, 100)
    prob_2w_bleibt = max(0, 100 - prob_2w_steigt - prob_2w_faellt)
    
    return round(prob_steigt,1), round(prob_bleibt,1), round(prob_faellt,1), \
           round(prob_2w_steigt,1), round(prob_2w_bleibt,1), round(prob_2w_faellt,1), \
           round(last_rsi,1), round(last_5_change,2), round(last_15_change,2)

# === Ergebnisse sammeln ===
results = []

for name, ticker in dax40_tickers.items():
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if df.empty:
            print(f"⚠️ Keine Daten für {name}")
            continue
        s1, b1, f1, s2, b2, f2, rsi, c5, c15 = calc_probabilities(df)
        results.append([name, datetime.now().strftime("%Y-%m-%d"),
                        s1, b1, f1, "Kurzfristige Tendenz",
                        s2, b2, f2, "Mittelfristige Tendenz",
                        rsi, c5, c15, abs(s1-f1), abs(s2-f2)])
    except Exception as e:
        print(f"⚠️ Fehler bei {name}: {e}")

# === DataFrame & CSV ===
cols = ["Aktie","Datum",
        "1-5T_Steigt","1-5T_Bleibt","1-5T_Fällt","Einschätzung_1-5T",
        "2-3W_Steigt","2-3W_Bleibt","2-3W_Fällt","Einschätzung_2-3W",
        "RSI","5T_Change(%)","15T_Change(%)","Diff_1-5","Diff_2-3W"]

df_result = pd.DataFrame(results, columns=cols)

# Sortieren nach Diff_1-5 (höchste Entscheidungskraft zuerst)
df_result = df_result.sort_values(by="Diff_1-5", ascending=False)

# CSV speichern
csv_name = f"dax40_{datetime.now().strftime('%Y-%m-%d')}.csv"
df_result.to_csv(csv_name, index=False)
print(f"✅ Datei erstellt: {csv_name} mit {len(df_result)} Einträgen")
