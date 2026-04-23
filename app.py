import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="TIA Quality Control", page_icon="🛡️", layout="wide")
EXCEL_FILE = "quality_tracking.xlsx"

# --- DATA STRUCTURE (Dependency Dictionary) ---
SITES_DATA = {
    "Lyon Plant": ["MERU", "ABC Parts", "SteelCo"],
    "Madrid Plant": ["Iberia Components", "MERU", "Madrid Logistics"],
    "Tangier Plant": ["Atlas Tech", "North Supply", "Maghreb Parts", "Tangier Fab"]
}

# --- DATA LOGIC ---
@st.cache_data(ttl=60)
def load_data():
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except Exception:
            return create_empty_df()
    return create_empty_df()

def create_empty_df():
    return pd.DataFrame(columns=[
        "Date", "Main Company", "Site", "Supplier", 
        "Job Number", "Passage", "Part Number", "Failure Type", "Quantity"
    ])

def save_data(new_row_df):
    df_existing = load_data()
    df_final = pd.concat([df_existing, new_row_df], ignore_index=True)
    df_final.to_excel(EXCEL_FILE, index=False)
    st.cache_data.clear()

# --- INTERFACE ---
st.title("🛡️ TIA - Quality Tracking System")

with st.expander("➕ Register a New Failure", expanded=True):
    # Dynamic selection outside the form for instant reactivity
    col1, col2 = st.columns(2)
    with col1:
        site = st.selectbox("Select Site (Factory)", list(SITES_DATA.keys()))
    with col2:
        supplier = st.selectbox("Select Supplier", SITES_DATA[site])

    with st.form("entry_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            job = st.text_input("Job Number")
            passage = st.selectbox("Passage Number", ["Passage 1", "Passage 2", "Passage 3", "Rework"])
            date_s = st.date_input("Detection Date", datetime.now())
            
        with c2:
            part_number = st.text_input("Part Number")
            failures = st.multiselect("Failure Types", ["Wrong Colour", "Wrong Size", "Damage", "Missing Part", "Surface Defect"])
            qty = st.number_input("Quantity", 1, 500, 1)
        
        submit = st.form_submit_button("Confirm Registration")
        
        if submit:
            if job and part_number and failures:
                new_row = pd.DataFrame({
                    "Date": [pd.to_datetime(date_s)], 
                    "Main Company": ["TIA"],
                    "Site": [site], 
                    "Supplier": [supplier], 
                    "Job Number": [job],
                    "Passage": [passage], 
                    "Part Number": [part_number],
                    "Failure Type": [", ".join(failures)], 
                    "Quantity": [qty]
                })
                save_data(new_row)
                st.success(f"Success! Entry recorded for {supplier} ({site}).")
                st.rerun()
            else:
                st.error("⚠️ Mandatory fields: Job Number, Part Number, and Failure Type.")

# --- STATISTICS ---
df_global = load_data()

if not df_global.empty:
    st.divider()
    st.header("📊 Dashboard & Analytics")
    
    # Sidebar Filters
    st.sidebar.header("🔍 Filters")
    unique_sites = df_global['Site'].unique().tolist()
    selected_sites = st.sidebar.multiselect("Filter by Site", unique_sites, default=unique_sites)
    
    df_filt = df_global[df_global['Site'].isin(selected_sites)]

    # Key Performance Indicators (KPIs)
    k1, k2, k3 = st.columns(3)
    total_qty = df_filt['Quantity'].sum()
    unique_parts = df_filt['Part Number'].nunique()
    
    k1.metric("Total Rejections", f"{total_qty} units")
    k2.metric("Impacted Part Numbers", unique_parts)
    k3.metric("Active Sites", df_filt['Site'].nunique())

    # Visuals
    chart_left, chart_right = st.columns(2)
    with chart_left:
        fig_bar = px.bar(df_filt, x="Supplier", y="Quantity", color="Site", 
                         title="Rejection Volume by Supplier",
                         labels={"Quantity": "Qty Rejected"})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with chart_right:
        # Explode failures for accurate pie chart representation
        df_pie = df_filt.assign(Failure=df_filt['Failure Type'].str.split(', ')).explode('Failure')
        fig_pie = px.pie(df_pie, values="Quantity", names="Failure", 
                         title="Distribution of Failure Types",
                         hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Data Table
    st.subheader("📋 Recent Entries")
    st.dataframe(df_filt.sort_values(by="Date", ascending=False), use_container_width=True)
else:
    st.info("💡 No data recorded yet. Use the form above to start tracking quality issues.")
