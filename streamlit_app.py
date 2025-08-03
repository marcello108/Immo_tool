import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import numpy_financial as npf

st.set_page_config(page_title="Immobilieninvestitionsrechner", layout="wide")
st.title("🏠 Immobilieninvestitionsrechner")

# 1. Objektdaten
st.header("1. Objektdaten")
bezeichnung = st.text_input("Bezeichnung", "Meine Immobilie")
wohnflaeche = st.slider("Wohnfläche (m²)", 20, 500, 100, step=5)
kaufpreis = st.slider("Kaufpreis (€)", 50000, 1000000, 300000, step=10000)
lageklasse = st.selectbox("Lageklasse", ["A", "B", "C"], index=1)

# 2. Kaufnebenkosten
st.header("2. Kaufnebenkosten")
bundesland = st.selectbox("Bundesland", ['Bayern (3.5%)', 'Hamburg (4.5%)', 'Baden-Württemberg (5.0%)', 'Hessen (6.0%)', 'Berlin (6.0%)', 'NRW (6.5%)', 'Andere (6.5%)'])
grunderwerbsteuer = float(bundesland.split("(")[1].replace("%)", ""))
makler = st.slider("Maklerprovision (%)", 0.0, 10.0, 3.57, step=0.1)
notar = st.slider("Notar & Grundbuch (%)", 0.0, 5.0, 2.0, step=0.1)
sonstige = st.slider("Sonstige Kosten (€)", 0, 50000, 15000, step=1000)

nebenkosten_gesamt = kaufpreis * (grunderwerbsteuer + makler + notar) / 100 + sonstige
gesamtinvest = kaufpreis + nebenkosten_gesamt
st.success(f"Gesamtnebenkosten: {nebenkosten_gesamt:,.0f} € | Gesamtinvestition: {gesamtinvest:,.0f} €")

# 3. Finanzierung & Steuern
st.header("3. Finanzierung & Steuern")
ek = st.slider("Eigenkapital (€)", 0, int(gesamtinvest), 60000, step=5000)
sollzins = st.slider("Sollzins (% p.a.)", 0.1, 10.0, 4.0, step=0.1)
tilgung = st.slider("Grundtilgung (% p.a.)", 0.1, 10.0, 2.0, step=0.1)
zinsbindung = st.slider("Zinsbindung (Jahre)", 1, 30, 10)
sondertilgung = st.slider("Sondertilgung (€/Jahr)", 0, 20000, 0, step=500)
steuersatz = st.slider("Pers. Steuersatz (%)", 0, 50, 42)
afa_satz = st.slider("AfA-Satz (%)", 1.0, 3.0, 2.0, step=0.1)

darlehen = max(0, gesamtinvest - ek)
monatliche_rate = darlehen * ((sollzins + tilgung) / 100) / 12
afa_jaehrlich = kaufpreis * 0.8 * afa_satz / 100
st.info(f"Fremdkapital: {darlehen:,.0f} € | Monatliche Rate: {monatliche_rate:,.2f} € | Jährliche AfA: {afa_jaehrlich:,.0f} €")

# 4. Einnahmen & Ausgaben
st.header("4. Einnahmen & Ausgaben")
kaltmiete = st.slider("Kaltmiete (€/Monat)", 0, 5000, 1200, step=100)
stellplaetze = st.slider("Stellplätze (€/Monat)", 0, 1000, 0, step=50)
nebenkosten_nicht_umlagefaehig = st.slider("Nicht umlagefähige Nebenkosten (€/Monat)", 0, 1000, 200, step=50)
ruecklagen = st.slider("Rücklagen (€/m²/Jahr)", 0.0, 20.0, 8.0, step=0.5)
hausgeld = st.slider("Hausgeld (€/Monat)", 0, 500, 0, step=10)

ruecklagen_monat = (ruecklagen * wohnflaeche) / 12
ausgaben_monat = nebenkosten_nicht_umlagefaehig + ruecklagen_monat + hausgeld
gesamtmiete = kaltmiete + stellplaetze

# 5. Analyse
st.header("5. Analyse")
jahre = st.slider("Prognosezeitraum (Jahre)", 1, 30, 30)
zinssteigerung = st.slider("Zinssteigerung nach Bindung (% absolut)", 0.0, 5.0, 2.0, step=0.5)
etf_rendite = st.slider("ETF Vergleichsrendite (%)", 0.0, 15.0, 8.0, step=0.5)

restschuld = darlehen
jahreszinsen, jahrestilgung, restschulden = [], [], [darlehen]
cashflows_vor_steuer, steuerersparnisse, cashflows_nach_steuer = [], [], []

for jahr in range(1, jahre + 1):
    zins_satz = sollzins if jahr <= zinsbindung else sollzins + zinssteigerung
    zinsen = restschuld * zins_satz / 100
    tilgung_val = max(0, monatliche_rate * 12 - zinsen + (sondertilgung if jahr <= zinsbindung else 0))
    tilgung_val = min(tilgung_val, restschuld)
    restschuld -= tilgung_val
    restschulden.append(restschuld)
    jahreszinsen.append(zinsen)
    jahrestilgung.append(tilgung_val)

    cf_vor = (gesamtmiete * 12) - (ausgaben_monat * 12) - zinsen
    steuer = ((gesamtmiete * 12) - (ausgaben_monat * 12) - zinsen - afa_jaehrlich) * (steuersatz / 100)
    steuerersparnis = -steuer if steuer < 0 else 0
    steuerbelastung = max(0, steuer)
    cf_nach = cf_vor - steuerbelastung + steuerersparnis

    cashflows_vor_steuer.append(cf_vor)
    steuerersparnisse.append(steuerersparnis)
    cashflows_nach_steuer.append(cf_nach)

verkaufspreis = gesamtinvest * (1.02 ** jahre)
verkaufsnebenkosten = verkaufspreis * 0.05
netto_verkauf = verkaufspreis - verkaufsnebenkosten - restschuld
cashflows = [-ek] + cashflows_nach_steuer
cashflows[-1] += netto_verkauf

try:
    irr = npf.irr(cashflows) * 100
except:
    irr = float('nan')

endvermoegen_etf = ek * (1 + etf_rendite / 100) ** jahre
endvermoegen_immo = ek + sum(cashflows_nach_steuer) + netto_verkauf

st.subheader("Kennzahlen")
st.metric("Break-even-Miete (€/Monat)", f"{(darlehen * (sollzins/100)/12 + ausgaben_monat - stellplaetze):.2f}")
st.metric("IRR (%)", f"{irr:.2f}")
st.metric("Endvermögen Immobilie", f"{endvermoegen_immo:,.0f} €")
st.metric("Endvermögen ETF", f"{endvermoegen_etf:,.0f} €")

fig, ax = plt.subplots(1, 2, figsize=(14, 5))
ax[0].plot(restschulden, label='Restschuld')
ax[0].axvline(zinsbindung, color='red', linestyle='--', label='Zinsbindung')
ax[0].legend()
ax[0].set_title("Darlehensverlauf")

ax[1].bar(['Immobilie', f'ETF ({etf_rendite:.1f}%)'], [endvermoegen_immo, endvermoegen_etf], color=['blue', 'green'])
ax[1].set_title("Endvermögen Vergleich")

st.pyplot(fig)
st.caption("© Dein Immobilienrechner – Streamlit-Version")
