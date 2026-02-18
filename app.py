import streamlit as st
import pandas as pd
import io

# --- Page Config ---
st.set_page_config(page_title="Noon Deal Generator", layout="wide")
st.title("🛒 Noon Deal Sheet Generator")

# --- Session State Management ---
# We use this to "remember" the file and settings across re-runs
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
    # Dynamic Deal Inputs
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
    # We use a form or simply a button, but we MUST save the result to session_state
    if st.button("🚀 Generate Deal Sheets"):
        try:
            # 1. Read Data
            df = pd.read_excel(uploaded_file)
            df.columns = df.columns.str.strip() # Clean column names
            
            # 2. Setup Output Buffer
            output = io.BytesIO()
            
            # 3. Filter Active Deals
            active_deals = [d for d in st.session_state.deal_types if d['deal_code'].strip() != '']
            
            if not active_deals:
                st.warning("⚠️ Please enter at least one Deal Code in the sidebar.")
            elif 'ID Partner' not in df.columns:
                st.error("❌ Column 'ID Partner' not found. Check your file.")
            else:
                # 4. Processing Loop
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    partners = df['ID Partner'].unique()
                    sheets_created = 0
                    
                    progress_bar = st.progress(0)
                    
                    for idx, partner_id in enumerate(partners):
                        partner_df = df[df['ID Partner'] == partner_id].copy()
                        
                        for deal in active_deals:
                            col_name = deal['col_name']
                            deal_code = deal['deal_code']
                            
                            if col_name in partner_df.columns:
                                # Convert to numeric
                                partner_df[col_name] = pd.to_numeric(partner_df[col_name], errors='coerce')
                                
                                # Filter rows with valid discount
                                mask = partner_df[col_name].notna() & (partner_df[col_name] > 0)
                                deal_data = partner_df[mask].copy()
                                
                                if not deal_data.empty:
                                    # -- Calculations --
                                    # Price
                                    if deal_data[col_name].max() > 1:
                                        discount_factor = deal_data[col_name] / 100
                                    else:
                                        discount_factor = deal_data[col_name]
                                    
                                    deal_data['deal_price'] = deal_data['Offer Price'] * (1 - discount_factor)
                                    deal_data['deal_price'] = deal_data['deal_price'].round(2)
                                    
                                    # Stock
                                    deal_data['Psku Live Express Stock'] = deal_data['Psku Live Express Stock'].fillna(0)
                                    deal_data['deal_stock'] = deal_data['Psku Live Express Stock'].apply(
                                        lambda x: fallback_stock if x == 0 else x
                                    )
                                    
                                    # Static
                                    deal_data['deal_code'] = deal_code
                                    deal_data['business_model'] = 'noon'
                                    
                                    # Final Columns
                                    output_df = pd.DataFrame()
                                    output_df['deal_code'] = deal_data['deal_code']
                                    output_df['id_partner'] = deal_data['ID Partner']
                                    output_df['partner_sku'] = deal_data['Psku']
                                    output_df['deal_price'] = deal_data['deal_price']
                                    output_df['deal_stock'] = deal_data['deal_stock']
                                    output_df['business_model'] = deal_data['business_model']
                                    
                                    # Tab Naming
                                    clean_deal = "".join(x for x in col_name if x.isalnum())[:10]
                                    clean_id = str(partner_id)[:15]
                                    output_df.to_excel(writer, sheet_name=f"{clean_id}_{clean_deal}", index=False)
                                    sheets_created += 1
                        
                        progress_bar.progress((idx + 1) / len(partners))
                
                # 5. Save the buffer content to Session State
                if sheets_created > 0:
                    # Reset buffer pointer to beginning
                    output.seek(0)
                    # Store the actual bytes in session state
                    st.session_state.processed_data = output.getvalue()
                    st.success(f"✅ Success! Generated {sheets_created} tabs.")
                else:
                    st.warning("No matching deals found.")
                    st.session_state.processed_data = None

        except Exception as e:
            st.error(f"Error: {e}")

    # --- Download Button (Outside the Generate block) ---
    # This checks if we have data in memory and shows the button constantly
    if st.session_state.processed_data is not None:
        st.divider()
        st.download_button(
            label="📥 Download Result File",
            data=st.session_state.processed_data,
            file_name="noon_deal_sheets_generated.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
