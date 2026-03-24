import streamlit as st
import pandas as pd
import io

# --- Page Config ---
st.set_page_config(page_title="Noon Deal Generator", layout="wide")
st.title("🛒 Noon Deal Sheet Generator")

# --- Session State Management ---
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'deal_types' not in st.session_state:
    st.session_state.deal_types = [
        {'col_name': 'Spotlight', 'deal_code': ''},
        {'col_name': 'Mega', 'deal_code': ''},
        {'col_name': 'Flashsale', 'deal_code': ''}
    ]

# --- Sidebar / Inputs ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("Stock Rules")
    fallback_stock = st.number_input(
        "If Stock is 0, change it to:", 
        min_value=1, 
        value=10, 
        step=1
    )
    st.divider()

    st.subheader("Deal Codes")
    for i, dt in enumerate(st.session_state.deal_types):
        col1, col2 = st.columns([1, 1.5])
        
        if i < 3:
            with col1:
                st.markdown(f"**{dt['col_name']}**")
        else:
            with col1:
                new_col_name = st.text_input(f"Col {i+1}", value=dt['col_name'], key=f"col_name_{i}")
                st.session_state.deal_types[i]['col_name'] = new_col_name
        
        with col2:
            new_code = st.text_input(f"Code", value=dt['deal_code'], key=f"deal_code_{i}", placeholder="e.g. SPOT-2024")
            st.session_state.deal_types[i]['deal_code'] = new_code
            
    if st.button("➕ Add Deal Type"):
        st.session_state.deal_types.append({'col_name': 'NewColumn', 'deal_
