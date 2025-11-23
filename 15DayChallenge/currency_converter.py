import streamlit as st
import requests
from datetime import datetime
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Currency Converter",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-title {
        color: white;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-align: center;
    }
    .main-subtitle {
        color: #e0e7ff;
        font-size: 1.1rem;
        text-align: center;
        margin-top: 0.5rem;
    }
    .result-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .result-amount {
        font-size: 3rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    .rate-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .history-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .currency-flag {
        font-size: 2rem;
        margin-right: 0.5rem;
    }
    .divider {
        height: 2px;
        background: linear-gradient(to right, transparent, #667eea, transparent);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversion_history' not in st.session_state:
    st.session_state.conversion_history = []

# Currency data with flags
CURRENCIES = {
    'USD': {'name': 'US Dollar', 'flag': '🇺🇸'},
    'EUR': {'name': 'Euro', 'flag': '🇪🇺'},
    'GBP': {'name': 'British Pound', 'flag': '🇬🇧'},
    'JPY': {'name': 'Japanese Yen', 'flag': '🇯🇵'},
    'AUD': {'name': 'Australian Dollar', 'flag': '🇦🇺'},
    'CAD': {'name': 'Canadian Dollar', 'flag': '🇨🇦'},
    'CHF': {'name': 'Swiss Franc', 'flag': '🇨🇭'},
    'CNY': {'name': 'Chinese Yuan', 'flag': '🇨🇳'},
    'INR': {'name': 'Indian Rupee', 'flag': '🇮🇳'},
    'MXN': {'name': 'Mexican Peso', 'flag': '🇲🇽'},
    'BRL': {'name': 'Brazilian Real', 'flag': '🇧🇷'},
    'ZAR': {'name': 'South African Rand', 'flag': '🇿🇦'},
    'SGD': {'name': 'Singapore Dollar', 'flag': '🇸🇬'},
    'HKD': {'name': 'Hong Kong Dollar', 'flag': '🇭🇰'},
    'NZD': {'name': 'New Zealand Dollar', 'flag': '🇳🇿'},
    'KRW': {'name': 'South Korean Won', 'flag': '🇰🇷'},
    'SEK': {'name': 'Swedish Krona', 'flag': '🇸🇪'},
    'NOK': {'name': 'Norwegian Krone', 'flag': '🇳🇴'},
    'RUB': {'name': 'Russian Ruble', 'flag': '🇷🇺'},
    'AED': {'name': 'UAE Dirham', 'flag': '🇦🇪'},
}

def get_exchange_rate(from_currency, to_currency):
    """Fetch real-time exchange rate from API"""
    try:
        # Using exchangerate-api.com (free tier)
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if 'rates' in data and to_currency in data['rates']:
            return data['rates'][to_currency], data.get('date', 'Unknown')
        else:
            return None, None
    except Exception as e:
        st.error(f"Error fetching exchange rate: {str(e)}")
        return None, None

def convert_currency(amount, from_currency, to_currency):
    """Convert currency and return result"""
    if from_currency == to_currency:
        return amount, 1.0, datetime.now().strftime("%Y-%m-%d")
    
    rate, date = get_exchange_rate(from_currency, to_currency)
    
    if rate is not None:
        converted_amount = amount * rate
        return converted_amount, rate, date
    else:
        return None, None, None

def add_to_history(amount, from_curr, to_curr, result, rate):
    """Add conversion to history"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.conversion_history.insert(0, {
        'timestamp': timestamp,
        'from_amount': amount,
        'from_currency': from_curr,
        'to_amount': result,
        'to_currency': to_curr,
        'rate': rate
    })
    # Keep only last 10 conversions
    if len(st.session_state.conversion_history) > 10:
        st.session_state.conversion_history = st.session_state.conversion_history[:10]

# Header
st.markdown("""
<div class='main-header'>
    <h1 class='main-title'>💱 Currency Converter</h1>
    <p class='main-subtitle'>Real-time Exchange Rates | Fast & Accurate</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    st.info("""
    **Features:**
    - ✅ Real-time exchange rates
    - ✅ 20+ currencies supported
    - ✅ Conversion history
    - ✅ Quick swap
    """)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    st.markdown("### 📊 Popular Conversions")
    popular_pairs = [
        ("USD", "EUR"),
        ("USD", "GBP"),
        ("EUR", "GBP"),
        ("USD", "INR"),
        ("USD", "JPY")
    ]
    
    for from_c, to_c in popular_pairs:
        rate, _ = get_exchange_rate(from_c, to_c)
        if rate:
            st.text(f"{from_c} → {to_c}: {rate:.4f}")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    st.markdown("### ℹ️ About")
    st.caption("Currency Converter v1.0")
    st.caption("Data: ExchangeRate-API")
    st.caption("Updated: Real-time")
    
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.conversion_history = []
        st.rerun()

# Main Content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 💰 Convert Currency")
    
    # Amount input
    amount = st.number_input(
        "Amount",
        min_value=0.01,
        value=100.0,
        step=0.01,
        format="%.2f",
        help="Enter the amount you want to convert"
    )
    
    # Currency selection
    col_from, col_swap, col_to = st.columns([5, 1, 5])
    
    with col_from:
        from_currency = st.selectbox(
            "From Currency",
            options=list(CURRENCIES.keys()),
            format_func=lambda x: f"{CURRENCIES[x]['flag']} {x} - {CURRENCIES[x]['name']}",
            index=0
        )
    
    with col_swap:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄", help="Swap currencies"):
            # Swap currencies
            temp = st.session_state.get('temp_to', 'EUR')
            st.session_state['temp_from'] = from_currency
            st.session_state['temp_to'] = from_currency
    
    with col_to:
        to_currency = st.selectbox(
            "To Currency",
            options=list(CURRENCIES.keys()),
            format_func=lambda x: f"{CURRENCIES[x]['flag']} {x} - {CURRENCIES[x]['name']}",
            index=1
        )
    
    # Convert button
    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 2])
    
    with col_btn1:
        convert_button = st.button("🔄 Convert", type="primary", use_container_width=True)
    
    with col_btn2:
        if st.button("↩️ Reset", use_container_width=True):
            st.rerun()
    
    # Perform conversion
    if convert_button:
        if amount <= 0:
            st.error("⚠️ Please enter a valid amount greater than 0")
        else:
            with st.spinner("Converting..."):
                result, rate, date = convert_currency(amount, from_currency, to_currency)
                
                if result is not None:
                    # Display result
                    st.markdown(f"""
                    <div class='result-box'>
                        <div style='font-size: 1.2rem;'>{CURRENCIES[from_currency]['flag']} {amount:,.2f} {from_currency}</div>
                        <div style='font-size: 1.5rem; margin: 0.5rem 0;'>⬇️</div>
                        <div class='result-amount'>{CURRENCIES[to_currency]['flag']} {result:,.2f} {to_currency}</div>
                        <div style='font-size: 0.9rem; opacity: 0.9;'>Exchange Rate: 1 {from_currency} = {rate:.6f} {to_currency}</div>
                        <div style='font-size: 0.8rem; opacity: 0.8; margin-top: 0.5rem;'>Last Updated: {date}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Additional information
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.metric(
                            "Exchange Rate",
                            f"{rate:.6f}",
                            help=f"1 {from_currency} = {rate:.6f} {to_currency}"
                        )
                    
                    with col_b:
                        reverse_rate = 1 / rate if rate != 0 else 0
                        st.metric(
                            "Reverse Rate",
                            f"{reverse_rate:.6f}",
                            help=f"1 {to_currency} = {reverse_rate:.6f} {from_currency}"
                        )
                    
                    with col_c:
                        percentage_diff = ((result - amount) / amount) * 100 if amount != 0 else 0
                        st.metric(
                            "Difference",
                            f"{percentage_diff:+.2f}%",
                            help="Percentage difference from original amount"
                        )
                    
                    # Add to history
                    add_to_history(amount, from_currency, to_currency, result, rate)
                    
                else:
                    st.error("❌ Unable to fetch exchange rate. Please try again.")

with col2:
    st.markdown("### 📜 Conversion History")
    
    if st.session_state.conversion_history:
        for idx, item in enumerate(st.session_state.conversion_history):
            with st.container():
                st.markdown(f"""
                <div class='history-card'>
                    <div style='font-size: 0.8rem; color: #64748b; margin-bottom: 0.5rem;'>{item['timestamp']}</div>
                    <div style='font-weight: bold;'>
                        {CURRENCIES[item['from_currency']]['flag']} {item['from_amount']:,.2f} {item['from_currency']}
                    </div>
                    <div style='text-align: center; margin: 0.3rem 0;'>⬇️</div>
                    <div style='font-weight: bold; color: #667eea;'>
                        {CURRENCIES[item['to_currency']]['flag']} {item['to_amount']:,.2f} {item['to_currency']}
                    </div>
                    <div style='font-size: 0.75rem; color: #64748b; margin-top: 0.5rem;'>
                        Rate: {item['rate']:.6f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No conversion history yet. Start converting!")

# Footer
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Quick conversion table
st.markdown("### 📊 Quick Reference Table")

reference_amount = st.slider("Reference Amount", 1, 1000, 100, 10)
reference_currency = st.selectbox(
    "Base Currency for Table",
    options=list(CURRENCIES.keys()),
    format_func=lambda x: f"{CURRENCIES[x]['flag']} {x}",
    index=0,
    key="reference_currency"
)

with st.spinner("Loading conversion table..."):
    table_data = []
    for curr in list(CURRENCIES.keys())[:10]:  # Show top 10 currencies
        if curr != reference_currency:
            rate, _ = get_exchange_rate(reference_currency, curr)
            if rate:
                converted = reference_amount * rate
                table_data.append({
                    'Currency': f"{CURRENCIES[curr]['flag']} {curr}",
                    'Name': CURRENCIES[curr]['name'],
                    'Exchange Rate': f"{rate:.6f}",
                    'Converted Amount': f"{converted:,.2f}"
                })
    
    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

# Footer info
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 2rem; margin-top: 2rem;'>
    <p><strong>💱 Currency Converter</strong></p>
    <p style='font-size: 0.9rem;'>Real-time exchange rates powered by ExchangeRate-API</p>
    <p style='font-size: 0.8rem; margin-top: 1rem;'>⚠️ Rates are for reference only. Actual rates may vary.</p>
</div>
""", unsafe_allow_html=True)