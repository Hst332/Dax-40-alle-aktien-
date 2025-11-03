import pandas as pd
import tradingeconomics as te
import os
from datetime import datetime

# === API-Key ===
# 👉 Setze deinen API-Key als Umgebungsvariable (lokal oder in GitHub Actions):
# export TE_API_KEY="dein_api_key"
API_KEY = os.getenv("TE_API_KEY", "YOUR_API_KEY_HERE")
te.login(API_KEY)

# === DAX40 Symbole (TradingEconomics Kürzel) ===
# Format: Firmenname : Kürzel (Yahoo/TE-Format)
symbols = {
    "Adidas": "ADS:GR",
    "Airbus": "AIR:GR",
    "Allianz": "ALV:GR",
    "BASF": "BAS:GR",
    "Bayer": "BAYN:GR",
    "Beiersdorf": "BEI:GR",
    "BMW": "BMW:GR",
    "Brenntag": "BNR:GR",
    "Commerzbank": "CBK:GR",
    "Continental": "CON:GR",
    "Daimler Truck": "DTG:GR",
    "Deutsche Bank": "DBK:GR",
    "Deutsche Börse": "DB1:GR",
    "Deutsche Post": "DPW:GR",
    "Deutsche Telekom": "DTE:GR",
    "E.ON": "EOAN:GR",
    "Fresenius": "FRE:GR",
    "Fresenius Medical Care": "FME:GR",
    "GEA": "G1A:GR",
    "Hannover Rück": "HNR1:GR",
    "Heidelberg Materials": "HEI:GR",
    "Henkel": "HEN3:GR",
    "Infineon": "IFX:GR",
    "Mercedes-Benz": "MBG:GR",
    "Merck": "MRK:GR",
    "MTU Aero Engines": "MTX:GR",
    "Münchener Rück": "MUV2:GR",
    "Porsche": "P911:GR",
    "Qiagen": "QIA:GR",
    "Rheinmetall": "RHM:GR",
    "RWE": "RWE:GR",
    "SAP": "SAP:GR",
    "Scout24": "G24:GR",
    "Siemens": "SIE:GR",
    "Siemens Energy": "ENR:GR",
    "Siemens Healthineers": "SHL:GR",
    "Symrise": "SY1:GR",
    "Volkswagen": "VOW3:GR",
    "Vonovia": "VNA:GR",
    "Zalando": "ZAL:GR"
}

# === Analyse + CSV-Erstellung ===
rows = []
datum = datetime.now().strftime("%Y-%m-%d")

for name, symbol in symbols.items():
    try:
        df = te.getMarketsBySymbol(symbols=symbol, output_type='df')
        if df is None or df.empty:
            print(f"⚠️ Keine Daten für {name}")
            continue

        price = df.loc[0, "Last"]
        change = df.loc[0, "DailyChangePercent"]

        # Beispiel: Wahrscheinlichkeitsschätzung (simple heuristische Logik)
        steigt = max(0, min(100, 50 + change * 1.5))
        fällt = max(0, min(100, 50 - change * 1.5))
        bleibt = max(0, 100 - (steigt + fällt))

        diff = abs(steigt - fällt)

        rows.append([
            name, datum,
            round(steigt, 1), round(bleibt, 1), round(fällt, 1),
            "Positiver Trend" if change > 0 else "Negativer Trend" if change < 0 else "Seitwärts",
            round(change, 2),
            round(price, 2),
            round(diff, 1)
        ])

    except Exception as e:
        print(f"⚠️ Fehler bei {name}: {e}")

# === DataFrame & Speicherung ===
cols = [
    "Aktie", "Datum", "1-5T_Steigt", "1-5T_Bleibt", "1-5T_Fällt",
    "Einschätzung", "Tagesänderung(%)", "Kurs", "Diff_1-5"
]

df_out = pd.DataFrame(rows, columns=cols)
df_out = df_out.sort_values(by="Diff_1-5", ascending=False)

csv_name = f"dax40_tradingeconomics_{datum}.csv"
df_out.to_csv(csv_name, index=False)

print(f"✅ Datei erstellt: {csv_name} mit {len(df_out)} Einträgen.")
