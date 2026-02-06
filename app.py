import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="TIA Quality Control",
    page_icon="🛡️",
    layout="wide"
)

# --- GESTION DU FICHIER DE DONNÉES ---
EXCEL_FILE = "suivi_qualite.xlsx"

def charger_donnees():
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    else:
        # Création d'un DataFrame vide avec les bonnes colonnes
        return pd.DataFrame(columns=["Date", "Main Company", "Site", "Supplier", "Job", "Failures", "Quantity"])

def sauvegarder_donnees(new_df):
    if os.path.exists(EXCEL_FILE):
        df_existing = pd.read_excel(EXCEL_FILE)
        df_final = pd.concat([df_existing, new_df], ignore_index=True)
    else:
        df_final = new_df
    df_final.to_excel(EXCEL_FILE, index=False)

# --- CHARGEMENT INITIAL ---
df_global = charger_donnees()

# --- INTERFACE UTILISATEUR ---
st.title("🛡️ TIA - Système de Suivi Qualité")
st.markdown(f"**Main Company:** TIA | **Fichier :** `{EXCEL_FILE}`")

# --- SECTION 1 : SAISIE DES DONNÉES ---
with st.expander("➕ Enregistrer une nouvelle défaillance (Failure)", expanded=True):
    with st.form("form_saisie", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            site = st.selectbox("Site (Factory)", ["Site A", "Site B", "Site C"])
            # Simulation dynamique des fournisseurs par site
            fournisseurs = {
                "Site A": ["MERU", "ABC Parts"],
                "Site B": ["SteelCo", "MERU"],
                "Site C": ["Atlas Tech", "North Supply"]
            }
            supplier = st.selectbox("Fournisseur (Supplier)", fournisseurs[site])
            job = st.text_input("Numéro de Job (ex: Job N° 01)")

        with col2:
            failures = st.multiselect("Types de Failure", ["Wrong Colour", "Wrong Size", "Damage", "Missing Part"])
            qty = st.number_input("Nombre de pièces impactées (1-50)", min_value=1, max_value=50, value=1)
            date_saisie = st.date_input("Date du constat", datetime.now())

        submit_button = st.form_submit_button("Valider l'enregistrement")

        if submit_button:
            if job:
                new_data = pd.DataFrame({
                    "Date": [pd.to_datetime(date_saisie)],
                    "Main Company": ["TIA"],
                    "Site": [site],
                    "Supplier": [supplier],
                    "Job": [job],
                    "Failures": [", ".join(failures)],
                    "Quantity": [qty]
                })
                sauvegarder_donnees(new_data)
                st.success(f"✅ Job {job} enregistré avec succès !")
                st.rerun() # Rafraîchir pour voir les stats
            else:
                st.error("⚠️ Le numéro de Job est obligatoire.")

# --- SECTION 2 : ANALYSE ET FILTRES ---
if not df_global.empty:
    st.divider()
    st.header("📊 Tableau de Bord & Statistiques")

    # Barre latérale pour les filtres
    st.sidebar.header("🔍 Filtres")
    selected_site = st.sidebar.multiselect("Filtrer par Site", df_global['Site'].unique(), default=df_global['Site'].unique())
    
    # Filtrage des données
    df_filtered = df_global[df_global['Site'].isin(selected_site)]

    # Indicateurs (KPI)
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Pièces Rejetées", f"{df_filtered['Quantity'].sum()} pcs")
    kpi2.metric("Nombre de Jobs", df_filtered['Job'].nunique())
    kpi3.metric("Sites Actifs", df_filtered['Site'].nunique())

    # Graphiques
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        fig_bar = px.bar(df_filtered, x="Supplier", y="Quantity", color="Site", title="Défauts par Fournisseur")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        fig_pie = px.pie(df_filtered, values="Quantity", names="Failures", title="Répartition des types de défauts")
        st.plotly_chart(fig_pie, use_container_width=True)

    # Affichage du tableau brut
    st.subheader("📋 Historique des données")
    st.dataframe(df_filtered.sort_values(by="Date", ascending=False), use_container_width=True)

    # Bouton de téléchargement
    with open(EXCEL_FILE, "rb") as f:
        st.download_button(
            label="⬇️ Télécharger le rapport Excel",
            data=f,
            file_name=f"Rapport_Qualite_TIA_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("ℹ️ Aucune donnée enregistrée pour le moment. Utilisez le formulaire ci-dessus.")
