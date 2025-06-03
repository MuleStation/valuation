import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import matplotlib.pyplot as plt


st.set_page_config(page_title="Valorisation d'entreprise", layout="wide")

st.title("MYFLR 📈 Dashboard de Valorisation d'Entreprise (DCF & Comparables)")

# Onglets
onglet = st.tabs(["📘 DCF Classique", "🎲 DCF Monte Carlo"])
#onglet 1
with onglet[0]:
    st.header("📘 DCF Classique")

ticker = st.text_input("Entrez le ticker de l’entreprise (ex: AAPL, MSFT, TSLA)", "AAPL") #U ask

if ticker:
    stock = yf.Ticker(ticker)

    st.header("🧾 Données financières de base")
    info = stock.info

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cours actuel", f"{info.get('currentPrice', 'N/A')} $")
        st.write(f"PER : {info.get('trailingPE', 'N/A')}")
    with col2:
        st.metric("Chiffre d'affaires", f"{info.get('totalRevenue', 'N/A'):,} $")
        st.write(f"Résultat net : {info.get('netIncomeToCommon', 'N/A'):,} $")
    with col3:
        st.metric("Capitalisation", f"{info.get('marketCap', 'N/A'):,} $")
        st.write(f"EBITDA : {info.get('ebitda', 'N/A'):,} $")

    st.header("💰 Hypothèses DCF ajustables")

    st.markdown("### 🔧 Paramètres financiers")

    fcf = st.number_input(
        "💵 Free Cash Flow de départ ($)",
        min_value=0.0,
        value=float(info.get("netIncomeToCommon", 1_000_000_000)),
        step=1_000_000.0,
        format="%.0f"
    )

    growth_rate = st.number_input(
        "📈 Croissance FCF (%)",
        min_value=0.00,
        max_value=0.20,
        value=0.05,
        step=0.001,
        format="%.3f"
    )

    discount_rate = st.number_input(
        "🏦 Taux d’actualisation (WACC) (%)",
        min_value=0.01,
        max_value=0.20,
        value=0.10,
        step=0.001,
        format="%.3f"
    )

    terminal_growth = st.number_input(
        "📉 Taux de croissance terminale (%)",
        min_value=0.00,
        max_value=0.05,
        value=0.02,
        step=0.001,
        format="%.3f"
    )

    years = st.number_input(
        "📅 Nombre d'années de projection",
        min_value=3,
        max_value=10,
        value=5,
        step=1
    )
# calculs
    fcfs = [fcf * (1 + growth_rate) ** i for i in range(1, years + 1)]
    discounted_fcfs = [fcf / ((1 + discount_rate) ** i) for i, fcf in enumerate(fcfs, start=1)]
    terminal_value = fcfs[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
    discounted_terminal = terminal_value / ((1 + discount_rate) ** years)

    dcf_value = sum(discounted_fcfs) + discounted_terminal

    st.subheader(f"📌 Valeur d’entreprise estimée : {dcf_value:,.0f} $")

    ebitda_ratio = 0.7  # hypothèse indicative
    ebitdas = [fcf / ebitda_ratio for fcf in fcfs]
    cum_values = np.cumsum(discounted_fcfs).tolist()

#tableau
    columns = [f"Année {i}" for i in range(1, years + 1)] + [f"Valeur terminale (Année {years})"]

    df_dcf = pd.DataFrame({
        "FCF projeté ($)": fcfs + [None],
        "FCF actualisé ($)": discounted_fcfs + [discounted_terminal],
        "Cumul actualisé ($)": cum_values + [dcf_value],
        "EBITDA estimé ($)": ebitdas + [None]
    }, index=columns).T  # <-- TRANSPOSE pour inverser axes

    st.subheader("📋 Détail des flux (valeurs en lignes, années en colonnes)")
    st.dataframe(df_dcf.style.format("{:,.0f}"))

    # Bloc comparables (à développer)
    st.header("📊 Comparables personnalisés (jusqu’à 5 tickers)")

    with st.expander("🔧 Ajouter des tickers comparables manuellement"):
        user_inputs = []
        for i in range(1, 6):
            t = st.text_input(f"Ticker {i} :", key=f"ticker_{i}")
            if t:
                user_inputs.append(t.upper())

    if user_inputs:
        st.subheader("📋 Résultat des comparables")

        comparables_data = []


        comparables_data.append({
            "Ticker": ticker.upper(),
            "Entreprise": info.get("shortName", ""),
            "PER": info.get("trailingPE", None),
            "EV/EBITDA": info.get("enterpriseToEbitda", None),
            "P/B": info.get("priceToBook", None),
            "Capitalisation ($)": info.get("marketCap", None)
        })

        for comp in user_inputs:
            try:
                comp_info = yf.Ticker(comp).info
                comparables_data.append({
                    "Ticker": comp,
                    "Entreprise": comp_info.get("shortName", ""),
                    "PER": comp_info.get("trailingPE", None),
                    "EV/EBITDA": comp_info.get("enterpriseToEbitda", None),
                    "P/B": comp_info.get("priceToBook", None),
                    "Capitalisation ($)": comp_info.get("marketCap", None)
                })
            except Exception as e:
                st.warning(f"⚠️ Impossible de charger les données pour {comp} : {e}")

        df_comparables = pd.DataFrame(comparables_data)
        st.dataframe(df_comparables.style.format({
            "PER": "{:.2f}",
            "EV/EBITDA": "{:.2f}",
            "P/B": "{:.2f}",
            "Capitalisation ($)": "{:,.0f}"
        }))
    else:
        st.info("🔎 Renseigne des tickers pour comparer avec l’entreprise analysée.")

    shares_outstanding = info.get("sharesOutstanding", None)

    st.markdown("---")
    st.subheader("📌 Résumé de la valorisation DCF")

    if shares_outstanding:
        valeur_par_action = dcf_value / shares_outstanding
        st.write(f"🔢 Nombre d'actions en circulation : **{shares_outstanding:,.0f}**")
        st.write(f"🏷️ Valorisation totale estimée (DCF) : **{dcf_value:,.0f} $**")
        st.write(f"💵 Valorisation **par action** : **{valeur_par_action:.2f} $**")
    else:
        st.warning("❗ Nombre d'actions non disponible, impossible de calculer la valorisation par action.")
        st.write(f"🏷️ Valorisation totale estimée (DCF) : **{dcf_value:,.0f} $**")

with onglet[1]:
    st.header("🎲 DCF Monte Carlo Simulation")

    ticker = st.text_input("Entrez le ticker de l’entreprise", "AAPL")

    if ticker:
        stock = yf.Ticker(ticker)
        info = stock.info

        # 🧾 Extraction des données de base
        try:
            initial_cashflow = info.get('freeCashflow', 100000000)  # $ par défaut si non dispo
            st.success(f"Cash Flow initial détecté : ${initial_cashflow:,.0f}")
        except:
            initial_cashflow = 1_000_000
            st.warning("Cash Flow non trouvé, valeur par défaut utilisée.")

        # 🔧 Paramètres ajustables
        st.subheader("⚙️ Hypothèses personnalisées")

        mean_growth = st.slider("Croissance moyenne estimée (%)", -10.0, 20.0, 5.0, 0.1)
        std_dev_growth = st.slider("Volatilité de croissance (%)", 0.1, 10.0, 2.0, 0.1)
        discount_rate = st.slider("Taux d'actualisation (%)", 2.0, 15.0, 8.0, 0.1)
        periods = st.slider("Durée de projection (années)", 3, 15, 5)
        n_simulations = 5000

        # 🎲 Monte Carlo Simulation
        final_vals = []

        for _ in range(n_simulations):
            cf = initial_cashflow
            npv = 0
            for year in range(1, periods + 1):
                growth = np.random.normal(loc=mean_growth / 100, scale=std_dev_growth / 100)
                cf *= (1 + growth)
                npv += cf / ((1 + discount_rate / 100) ** year)
            final_vals.append(npv)

        # 📈 Résultat
        st.subheader("📈 Distribution simulée des valorisations")
        fig, ax = plt.subplots()
        ax.hist(final_vals, bins=50, edgecolor='black')
        ax.set_title(f"Monte Carlo DCF – {ticker}")
        ax.set_xlabel("Valeur actuelle nette ($)")
        ax.set_ylabel("Fréquence")
        st.pyplot(fig)

        st.success(f"💰 Valeur moyenne simulée : ${np.mean(final_vals):,.2f}")
# bas de page

st.markdown("""
<hr style="margin-top: 3rem; margin-bottom: 1rem; border: none; border-top: 1px solid #ccc;" />

<div style="text-align: center; font-size: 0.85rem; color: #666;">
    © 2025 <strong>May Flower</strong> by <a href="https://www.linkedin.com/in/enzo-willcox-2b44112b3/" target="_blank" style="color:#8c2118; text-decoration:none;"><strong>Enzo Willcox</strong></a><br>
    🌐 <a href="https://www.mayflower.website/" target="_blank" style="color:#8c2118; text-decoration:none;">www.mayflower.website</a>
</div>
""", unsafe_allow_html=True)
