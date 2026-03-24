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
        st.session_state.deal_types.append({'col_name': 'NewColumn', 'deal_code': ''})
        st.rerun()

# --- Main Logic ---
uploaded_file = st.file_uploader("Upload Seller Data (Excel)", type=['xlsx', 'xls'])

if uploaded_file:
    if st.button("🚀 Generate Deal Sheets"):
        try:
            # 1. Read Data
            df = pd.read_excel(uploaded_file)
            df.columns = df.columns.str.strip() 
            
            # 2. Setup Output Buffer
            output = io.BytesIO()
            
            # 3. Filter Active Deals
            active_deals = [d for d in st.session_state.deal_types if d['deal_code'].strip() != '']
            
            # Required columns check
            required_cols = ['ID Partner', 'Offer Code', 'SKU', 'Psku', 'Offer Price']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if not active_deals:
                st.warning("⚠️ Please enter at least one Deal Code in the sidebar.")
            elif missing_cols:
                st.error(f"❌ Missing required columns in your Excel file: {', '.join(missing_cols)}")
            else:
                # 4. Processing Loop
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    partners = df['ID Partner'].unique()
                    sheets_created = 0
                    
                    # --- Dictionary to store DataFrames for each deal summary ---
                    deal_summaries = {deal['deal_code']: [] for deal in active_deals}
                    
                    progress_bar = st.progress(0)
                    
                    # Process individual partner sheets
                    for idx, partner_id in enumerate(partners):
                        partner_df = df[df['ID Partner'] == partner_id].copy()
                        
                        for deal in active_deals:
                            col_name = deal['col_name']
                            deal_code =
