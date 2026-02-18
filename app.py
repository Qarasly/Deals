import streamlit as st
import pandas as pd
import io

# --- Page Config ---
st.set_page_config(page_title="Noon Deal Generator", layout="wide")
st.title("🛒 Noon Deal Sheet Generator")
st.markdown("""
This tool converts raw seller data into formatted deal upload sheets.
It automatically calculates discounted prices and adjusts stock levels based on your input.
""")

# --- Sidebar / Inputs ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # --- NEW: Stock Logic Input ---
    st.subheader("Stock Rules")
    fallback_stock = st.number_input(
        "If Stock is 0, change it to:", 
        min_value=1, 
        value=10, 
        step=1,
        help="If 'Psku Live Express Stock' is 0 or empty, this value will be used."
    )
    st.divider()

    st.subheader("Deal Codes")
    
    # Initialize session state for deal types if not present
    if 'deal_types' not in st.session_state:
        st.session_state.deal_types = [
            {'col_name': 'Spotlight', 'deal_code': ''},
            {'col_name': 'Mega', 'deal_code': ''},
            {'col_name': 'Flashsale', 'deal_code': ''}
        ]

    # Dynamic Deal Inputs
    for i, dt in enumerate(st.session_state.deal_types):
        col1, col2 = st.columns([1, 1.5])
        
        # Determine label for the column name input
        if i < 3:
            # Fixed names for the first 3, but we just display them
            with col1:
                st.markdown(f"**{dt['col_name']}**")
        else:
            # Editable names for custom added deals
            with col1:
                new_col_name = st.text_input(f"Col Name {i+1}", value=dt['col_name'], key=f"col_name_{i}")
                st.session_state.deal_types[i]['col_name'] = new_col_name
        
        with col2:
            new_code = st.text_input(f"Code", value=dt['deal_code'], key=f"deal_code_{i}", placeholder="e.g. SPOT-2024")
            st.session_state.deal_types[i]['deal_code'] = new_code
            
    # Button to add more deal types
    if st.button("➕ Add Deal Type"):
        st.session_state.deal_types.append({'col_name': 'NewColumn', 'deal_code': ''})
        st.rerun()

    st.info("Ensure your Excel file has columns matching the names above containing the discount %.")

# --- Main Logic ---

uploaded_file = st.file_uploader("Upload Seller Data (Excel)", type=['xlsx', 'xls'])

if uploaded_file:
    # Button to trigger processing
    if st.button("Generate Deal Sheets"):
        try:
            # Read Data
            df = pd.read_excel(uploaded_file)
            
            # Standardize column names (strip whitespace)
            df.columns = df.columns.str.strip()
            
            # Output buffer for the Excel file
            output = io.BytesIO()
            
            # Filter for active deals (where user typed a code)
            active_deals = [d for d in st.session_state.deal_types if d['deal_code'].strip() != '']
            
            if not active_deals:
                st.warning("⚠️ Please enter at least one Deal Code in the sidebar.")
            elif 'ID Partner' not in df.columns:
                st.error("❌ Column 'ID Partner' not found in uploaded sheet.")
            else:
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    partners = df['ID Partner'].unique()
                    sheets_created = 0
                    
                    # Progress Bar
                    progress_bar = st.progress(0)
                    
                    for idx, partner_id in enumerate(partners):
                        # Filter data for this partner
                        partner_df = df[df['ID Partner'] == partner_id].copy()
                        
                        for deal in active_deals:
                            col_name = deal['col_name']
                            deal_code = deal['deal_code']
                            
                            # Check if the deal column exists in the Excel file
                            if col_name in partner_df.columns:
                                # Convert to numeric, forcing errors to NaN
                                partner_df[col_name] = pd.to_numeric(partner_df[col_name], errors='coerce')
                                
                                # Filter: Only rows where discount > 0
                                mask = partner_df[col_name].notna() & (partner_df[col_name] > 0)
                                deal_data = partner_df[mask].copy()
                                
                                if not deal_data.empty:
                                    # --- TRANSFORMATIONS ---
                                    
                                    # 1. Price Calculation
                                    # Handle % formats (e.g., 10 vs 0.10)
                                    if deal_data[col_name].max() > 1:
                                        discount_factor = deal_data[col_name] / 100
                                    else:
                                        discount_factor = deal_data[col_name]
                                    
                                    deal_data['deal_price'] = deal_data['Offer Price'] * (1 - discount_factor)
                                    deal_data['deal_price'] = deal_data['deal_price'].round(2)
                                    
                                    # 2. Stock Logic (Using the variable 'fallback_stock')
                                    deal_data['Psku Live Express Stock'] = deal_data['Psku Live Express Stock'].fillna(0)
                                    deal_data['deal_stock'] = deal_data['Psku Live Express Stock'].apply(
                                        lambda x: fallback_stock if x == 0 else x
                                    )
                                    
                                    # 3. Static Columns
                                    deal_data['deal_code'] = deal_code
                                    deal_data['business_model'] = 'noon'
                                    
                                    # 4. Final Layout
                                    output_df = pd.DataFrame()
                                    output_df['deal_code'] = deal_data['deal_code']
                                    output_df['id_partner'] = deal_data['ID Partner']
                                    output_df['partner_sku'] = deal_data['Psku']
                                    output_df['deal_price'] = deal_data['deal_price']
                                    output_df['deal_stock'] = deal_data['deal_stock']
                                    output_df['business_model'] = deal_data['business_model']
                                    
                                    # --- TAB CREATION ---
                                    # Tab Name: PartnerID_DealType (Cleaned)
                                    clean_deal_name = "".join(x for x in col_name if x.isalnum())[:10]
                                    clean_partner_id = str(partner_id)[:15]
                                    sheet_name = f"{clean_partner_id}_{clean_deal_name}"
                                    
                                    output_df.to_excel(writer, sheet_name=sheet_name, index=False)
                                    sheets_created += 1
                        
                        # Update progress
                        progress_bar.progress((idx + 1) / len(partners))
                    
                    if sheets_created > 0:
                        st.success(f"✅ Success! Created {sheets_created} tabs.")
                        output.seek(0)
                        st.download_button(
                            label="📥 Download Result File",
                            data=output,
                            file_name="noon_deal_sheets_generated.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.warning("No matching deals found for the provided codes and columns.")

        except Exception as e:
            st.error(f"An error occurred: {e}")