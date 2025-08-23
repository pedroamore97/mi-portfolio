import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px
import warnings
import re 
import numpy as np
import os
from supabase import create_client, Client

# --- Suppress FutureWarnings ---
warnings.simplefilter(action='ignore', category=FutureWarning)
# -----------------------------

# -----------------------------------------------
# CONFIGURATION
# -----------------------------------------------
# Elimina DB_NAME, ahora usamos Supabase
BASE_CURRENCY = "USD"

# List of all tickers including stocks, indices and commodities
TICKERS_INFO = {
    "^DJI": {"symbol": "^DJI", "currency": "USD", "market": "US"},
    "^GSPC": {"symbol": "^GSPC", "currency": "USD", "market": "US"},
    "^IXIC": {"symbol": "^IXIC", "currency": "USD", "market": "US"},
    "GC=F": {"symbol": "GC=F", "currency": "USD", "market": "COMMODITY"},
    "AAPL": {"symbol": "AAPL", "currency": "USD", "market": "US"},
    "NVDA": {"symbol": "NVDA", "currency": "USD", "market": "US"},
    "ASML": {"symbol": "ASML", "currency": "EUR", "market": "EU"},
    "GOOGL": {"symbol": "GOOGL", "currency": "USD", "market": "US"},
    "MSFT": {"symbol": "MSFT", "currency": "USD", "market": "US"},
    "AIR.PA": {"symbol": "AIR.PA", "currency": "EUR", "market": "EU"},
    "BNP.PA": {"symbol": "BNP.PA", "currency": "EUR", "market": "EU"},
    "SAN.MC": {"symbol": "SAN.MC", "currency": "EUR", "market": "EU"},
    "MBG.DE": {"symbol": "MBG.DE", "currency": "EUR", "market": "EU"},
    "NKE": {"symbol": "NKE", "currency": "USD", "market": "US"},
    "TRNS": {"symbol": "TRNS", "currency": "USD", "market": "US"},
    "AMZN": {"symbol": "AMZN", "currency": "USD", "market": "US"},
    "TSLA": {"symbol": "TSLA", "currency": "USD", "market": "US"},
    "V": {"symbol": "V", "currency": "USD", "market": "US"},
    "PYPL": {"symbol": "PYPL", "currency": "USD", "market": "US"},
    "FDX": {"symbol": "FDX", "currency": "USD", "market": "US"},
    "UPS": {"symbol": "UPS", "currency": "USD", "market": "US"},
    "UNH": {"symbol": "UNH", "currency": "USD", "market": "US"},
    "CMCO": {"symbol": "CMCO", "currency": "USD", "market": "US"},
    "MC.PA": {"symbol": "MC.PA", "currency": "EUR", "market": "EU"},
    "CAT": {"symbol": "CAT", "currency": "USD", "market": "US"},
    "BRK-B": {"symbol": "BRK-B", "currency": "USD", "market": "US"},
    "0HAU.IL": {"symbol": "0HAU.IL", "currency": "EUR", "market": "EU"},
    "CAT1.BE": {"symbol": "CAT1.BE", "currency": "EUR", "market": "EU"}, 
}

CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£"
}

CRYPTO_TICKERS_INFO = {
    "Bitcoin": {"symbol_usd": "BTC-USD", "name": "Bitcoin"},
    "Ethereum": {"symbol_usd": "ETH-USD", "name": "Ethereum"},
    "Tether": {"symbol_usd": "USDT-USD", "name": "Tether"},
    "BNB": {"symbol_usd": "BNB-USD", "name": "BNB"},
    "Solana": {"symbol_usd": "SOL-USD", "name": "Solana"},
    "USD Coin": {"symbol_usd": "USDC-USD", "name": "USD Coin"},
    "XRP": {"symbol_usd": "XRP-USD", "name": "XRP"},
    "Toncoin": {"symbol_usd": "TON-USD", "name": "Toncoin"},
    "Cardano": {"symbol_usd": "ADA-USD", "name": "Cardano"},
    "Avalanche": {"symbol_usd": "AVAX-USD", "name": "Avalanche"},
}

SUPPORTED_CURRENCIES = ["EUR", "USD", "GBP"]
GLOBAL_TICKERS = list(TICKERS_INFO.keys())
CRYPTO_TICKERS = [info["symbol_usd"] for info in CRYPTO_TICKERS_INFO.values()]

# -----------------------------------------------
# STYLING (CSS Injection)
# -----------------------------------------------
st.markdown(
    """
    <style>
    section.main .block-container {
        max-width: 100% !important;
        padding-top: 1rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 1rem;
    }
    
    section.main .block-container > div {
        display: flex;
        flex-direction: row;
    }
    
    .st-emotion-cache-18j2v2n {
        flex: 3;
    }

    .st-emotion-cache-1y4y1h6 {
        flex: 2;
    }
    
    .st-emotion-cache-6q9sum {
        width: 100% !important;
        background-color: #f0f2f6; 
        border-right: 1px solid #e0e0e0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------
# DATA HELPER FUNCTIONS
# -----------------------------------------------
@st.cache_resource 
def get_ticker_details(tickers):
    """Gets full names and currency of tickers using yfinance."""
    details_map = {}
    for ticker_symbol in tickers:
        try:
            ticker_yf = yf.Ticker(ticker_symbol)
            info = ticker_yf.info
            name = info.get('longName') or info.get('shortName') or ticker_symbol
            currency = info.get('currency') or TICKERS_INFO.get(ticker_symbol, {}).get('currency') or BASE_CURRENCY
            details_map[ticker_symbol] = {'name': name, 'currency': currency}
        except Exception:
            details_map[ticker_symbol] = {'name': ticker_symbol, 'currency': None}
    return details_map

@st.cache_data(ttl=3600) # Cache the exchange rate for 1 hour
def get_usd_to_eur_exchange_rate_from_yf():
    """
    Obtiene el tipo de cambio actual de USD a EUR de Yahoo Finance (ticker EUR=X).
    """
    try:
        # Get data for the last few days to ensure we get a recent close price
        today = datetime.now().date()
        df = yf.download("EURUSD=X", start=today - timedelta(days=7), end=today + timedelta(days=1))

        if not df.empty:
            # We want the USD/EUR rate, but the ticker is EUR/USD, so we need to invert it.
            exchange_rate = 1 / df['Close'].iloc[-1]
            if isinstance(exchange_rate, pd.Series): 
                return exchange_rate.iloc[0]
            return float(exchange_rate)
        else:
            st.warning("⚠️ El ticker EURUSD=X no devolvió datos. No se podrá realizar la conversión a EUR.")
            return None
    except Exception as e:
        st.error(f"❌ Error al obtener el tipo de cambio USD/EUR de Yahoo Finance: {e}")
        return None

@st.cache_data(ttl=3600)
def get_exchange_rates():
    """
    Fetches real-time exchange rates to the BASE_CURRENCY.
    This version now uses the specific yfinance function for EUR.
    """
    rates = {BASE_CURRENCY: 1.0}
    
    for currency in SUPPORTED_CURRENCIES:
        if currency == BASE_CURRENCY:
            continue
        try:
            if currency == "EUR":
                # Use the specific function requested by the user for EUR
                rate_eur = get_usd_to_eur_exchange_rate_from_yf()
                if rate_eur is not None:
                    rates[currency] = rate_eur
                else:
                    st.warning(f"⚠️ No se pudo obtener la tasa de cambio para {currency}. Usando 1.0 por defecto.")
                    rates[currency] = 1.0
            else:
                # For other currencies, continue with the standard robust method
                ticker_symbol = f"{currency}{BASE_CURRENCY}=X"
                data = yf.download(ticker_symbol, period="1d", interval="1m")
                
                if not data.empty:
                    rates[currency] = data['Close'].iloc[-1]
                else:
                    st.warning(f"⚠️ No se pudo obtener la tasa de cambio para {currency} usando el ticker {ticker_symbol}. Usando 1.0 por defecto.")
                    rates[currency] = 1.0
        except Exception as e:
            st.error(f"❌ Error al obtener la tasa de cambio para {currency}: {e}. Usando 1.0 por defecto.")
            rates[currency] = 1.0
            
    return rates

TICKER_DETAILS = get_ticker_details(GLOBAL_TICKERS + CRYPTO_TICKERS)
GLOBAL_DISPLAY_NAMES = [f"{TICKER_DETAILS[t]['name']} ({t})" for t in GLOBAL_TICKERS if TICKER_DETAILS.get(t) and TICKER_DETAILS[t]['name']]
CRYPTO_DISPLAY_NAMES = [f"{info['name']} ({info['symbol_usd']})" for info in CRYPTO_TICKERS_INFO.values()]

# -----------------------------------------------
# DATABASE FUNCTIONS
# -----------------------------------------------
# CONFIGURACIÓN Y FUNCIONES PARA SUPABASE
# --- Configuración de Supabase ---
# --- Configuración de Supabase ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# ---------------------------------

def save_portfolio_item(ticker, cantidad, precio_compra, precio_compra_currency, nombre_personalizado, user_id):
    """Adds a new purchase entry for a stock or crypto in the user's portfolio."""
    data = {
        "user_id": user_id,
        "ticker": ticker.upper(),
        "cantidad": cantidad,
        "precio_compra": precio_compra,
        "precio_compra_currency": precio_compra_currency,
        "nombre_personalizado": nombre_personalizado
    }
    supabase.table("portfolio").insert(data).execute()

def delete_portfolio_item(ticker, user_id):
    """Deletes all entries for a given stock or crypto from the user's portfolio."""
    supabase.table("portfolio").delete().eq("ticker", ticker).eq("user_id", user_id).execute()

def load_portfolio(user_id):
    """Loads all items from the user's portfolio."""
    if not user_id:
        return pd.DataFrame() # Devuelve un dataframe vacío si no hay ID de usuario
    
    # Filtra por el user_id para cargar solo los datos de ese usuario
    response = supabase.table("portfolio").select("*").eq("user_id", user_id).execute()
    return pd.DataFrame(response.data)

# -----------------------------------------------
# DATA FETCHING & CALCULATION FUNCTIONS
# -----------------------------------------------
def calculate_portfolio_summary(user_id):
    """
    Loads portfolio data, fetches current prices and exchange rates,
    and calculates summary metrics in BASE_CURRENCY.
    """
    df_portfolio = load_portfolio(user_id) # Pasa el user_id
    if df_portfolio.empty:
        return 0.0, 0.0, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    rates = get_exchange_rates()
    
    total_invested_base = 0.0
    total_market_value_base = 0.0
    portfolio_details = []

    tickers = df_portfolio['ticker'].unique().tolist()
    data = yf.download(tickers, period="1d", interval="1m")

    for ticker in tickers:
        df_ticker_purchases = df_portfolio[df_portfolio['ticker'] == ticker]
        
        cantidad_total = df_ticker_purchases['cantidad'].sum()
        
        total_cost_per_ticker = (df_ticker_purchases['cantidad'] * df_ticker_purchases['precio_compra']).sum()
        precio_compra_promedio = total_cost_per_ticker / cantidad_total if cantidad_total > 0 else 0
        
        compra_currency = df_ticker_purchases['precio_compra_currency'].iloc[0]
        nombre_personalizado = df_ticker_purchases['nombre_personalizado'].iloc[0] or TICKER_DETAILS.get(ticker, {}).get('name')
        
        stock_currency = TICKER_DETAILS.get(ticker, {}).get('currency')

        current_price = None
        if not data.empty and ('Close', ticker) in data.columns:
            ticker_close_data = data['Close'][ticker].dropna()
            if not ticker_close_data.empty:
                current_price = ticker_close_data.iloc[-1]
        
        # --- LÓGICA DE CONVERSIÓN MEJORADA ---
        # Se obtiene la tasa de cambio de manera segura, con 1.0 como valor por defecto.
        rate_compra_to_base = rates.get(compra_currency, 1.0)
        rate_stock_to_base = rates.get(stock_currency, 1.0)
        
        invested_original = cantidad_total * precio_compra_promedio
        invested_base = invested_original * rate_compra_to_base
        
        if pd.isna(current_price) or current_price is None or current_price == 0:
            market_value_original = 0.0
            market_value_base = 0.0
            rentabilidad_porcentaje = 0.0
            rentabilidad_valor_original = 0.0
        else:
            market_value_original = cantidad_total * current_price
            market_value_base = market_value_original * rate_stock_to_base
            
            if float(invested_original) != 0:
                rentabilidad_porcentaje = ((market_value_original - invested_original) / invested_original) * 100
                rentabilidad_valor_original = market_value_original - invested_original
            else:
                rentabilidad_porcentaje = 0.0
                rentabilidad_valor_original = 0.0
        
        total_invested_base += invested_base
        total_market_value_base += market_value_base

        portfolio_details.append({
            "Ticker": ticker,
            "Nombre": nombre_personalizado,
            "Cantidad": cantidad_total,
            "Divisa de Compra": compra_currency,
            "Divisa de Activo": stock_currency,
            f"Precio de Compra Promedio ({compra_currency})": precio_compra_promedio,
            f"Precio Actual ({stock_currency})": current_price,
            f"Valor de Mercado ({BASE_CURRENCY})": market_value_base,
            f"Valor de Mercado Original ({stock_currency})": market_value_original,
            f"Rentabilidad ({stock_currency})": rentabilidad_valor_original,
            "Rentabilidad (%)": rentabilidad_porcentaje,
            f"Inversión Inicial ({BASE_CURRENCY})": invested_base,
            f"Inversión Inicial Original ({compra_currency})": invested_original,
            "Tipo": "Criptoactivo" if ticker in CRYPTO_TICKERS else "Acción"
        })
    
    df_details = pd.DataFrame(portfolio_details)
    
    numeric_cols = [
        f'Valor de Mercado ({BASE_CURRENCY})',
        'Rentabilidad (%)',
        f'Inversión Inicial ({BASE_CURRENCY})'
    ]
    for col in numeric_cols:
        if col in df_details.columns:
            df_details[col] = pd.to_numeric(df_details[col], errors='coerce')
    
    df_acciones = df_details[df_details['Tipo'] == 'Acción'].copy()
    df_cryptos = df_details[df_details['Tipo'] == 'Criptoactivo'].copy()

    total_market_value_from_df = df_details[f'Valor de Mercado ({BASE_CURRENCY})'].sum()
    if total_market_value_from_df > 0:
        df_details['Peso en el Portfolio (%)'] = (df_details[f'Valor de Mercado ({BASE_CURRENCY})'] / total_market_value_from_df) * 100
    else:
        df_details['Peso en el Portfolio (%)'] = 0.0

    if not df_acciones.empty:
        total_market_value_acciones = df_acciones[f'Valor de Mercado ({BASE_CURRENCY})'].sum()
        if total_market_value_acciones > 0:
            df_acciones['Peso en el Portfolio (%)'] = (df_acciones[f'Valor de Mercado ({BASE_CURRENCY})'] / total_market_value_acciones) * 100
        else:
            df_acciones['Peso en el Portfolio (%)'] = 0.0
    
    if not df_cryptos.empty:
        total_market_value_cryptos = df_cryptos[f'Valor de Mercado ({BASE_CURRENCY})'].sum()
        if total_market_value_cryptos > 0:
            df_cryptos['Peso en el Portfolio (%)'] = (df_cryptos[f'Valor de Mercado ({BASE_CURRENCY})'] / total_market_value_cryptos) * 100
        else:
            df_cryptos['Peso en el Portfolio (%)'] = 0.0
    
    return total_invested_base, total_market_value_base, df_details, df_acciones, df_cryptos

# -----------------------------------------------
# STREAMLIT APP LAYOUT
# -----------------------------------------------
st.set_page_config(page_title="Gestor de Portfolio de Inversión", layout="wide")

# Eliminamos la llamada a create_tables_if_not_exists()
# ya que la tabla se crea en Supabase

st.sidebar.header("Gestión del Portfolio")

# --- Formulario de ID de Usuario ---
user_id = st.sidebar.text_input(
    "Ingresa tu ID de Usuario:", 
    placeholder="ej. 'pedro97' o 'hermano'", 
    key="user_id_input"
)

if not user_id:
    st.info("⚠️ Ingresa un ID de Usuario en la barra lateral para ver y gestionar tu portfolio personal.")
    st.stop()

df_portfolio = load_portfolio(user_id)
portfolio_tickers = df_portfolio['ticker'].unique().tolist()
stock_tickers_in_portfolio = [t for t in portfolio_tickers if t in GLOBAL_TICKERS]
crypto_tickers_in_portfolio = [t for t in portfolio_tickers if t in CRYPTO_TICKERS]

# --- Formulario para Añadir Acciones ---
with st.sidebar.form("acciones_form"):
    st.subheader("Añadir Acciones")
    ticker_choice = st.selectbox(
        "Selecciona un Ticker de Acción:",
        options=["-- Selecciona uno --", "Otro"] + sorted(GLOBAL_DISPLAY_NAMES),
        key="ticker_selector"
    )
    ticker_manual = st.text_input("Escribe el Ticker de la Acción:", value="", key="ticker_manual_input_key").upper()

    ticker_to_add_accion = ""
    if ticker_choice == "Otro":
        ticker_to_add_accion = ticker_manual
    elif ticker_choice != "-- Selecciona uno --":
        match = re.search(r'\((.*?)\)', ticker_choice)
        ticker_to_add_accion = match.group(1) if match else ""
    
    cantidad_input_accion = st.number_input("Cantidad", min_value=0.00000001, value=1.0, step=0.00000001, format="%.8f", key="cantidad_add_input_accion")
    precio_compra_input_accion = st.number_input("Precio de Compra", min_value=0.01, value=100.0, format="%.2f", key="precio_add_input_accion")
    compra_currency_accion = st.selectbox("Divisa de Compra", options=SUPPORTED_CURRENCIES, key="currency_select_accion")
    nombre_personalizado_accion = st.text_input("Nombre Personalizado (Opcional)", key="nombre_add_input_accion")
    
    submitted_accion = st.form_submit_button("Añadir Acción")
    if submitted_accion:
        if ticker_to_add_accion:
            save_portfolio_item(ticker_to_add_accion, cantidad_input_accion, precio_compra_input_accion, compra_currency_accion, nombre_personalizado_accion, user_id)
            st.success(f"✔️ Activo '{ticker_to_add_accion}' añadido con éxito.")
            st.rerun()  
        else:
            st.error("❌ Debes seleccionar o escribir un ticker de acción válido.")

st.sidebar.markdown("---")

# --- Formulario para Añadir Criptomonedas ---
with st.sidebar.form("cripto_form"):
    st.subheader("Añadir Criptomonedas")
    ticker_choice_cripto = st.selectbox(
        "Selecciona una Criptomoneda:",
        options=["-- Selecciona uno --"] + sorted(CRYPTO_DISPLAY_NAMES),
        key="crypto_selector"
    )
    
    ticker_to_add_cripto = ""
    if ticker_choice_cripto != "-- Selecciona uno --":
        match = re.search(r'\((.*?)\)', ticker_choice_cripto)
        ticker_to_add_cripto = match.group(1) if match else ""
    
    cantidad_input_cripto = st.number_input("Cantidad", min_value=0.00000001, value=1.0, step=0.00000001, format="%.8f", key="cantidad_add_input_cripto")
    precio_compra_input_cripto = st.number_input("Precio de Compra", min_value=0.01, value=100.0, format="%.2f", key="precio_add_input_cripto")
    compra_currency_cripto = st.selectbox("Divisa de Compra", options=["USD"], key="currency_select_cripto")
    nombre_personalizado_cripto = st.text_input("Nombre Personalizado (Opcional)", key="nombre_add_input_cripto")
    
    submitted_cripto = st.form_submit_button("Añadir Criptomoneda")
    if submitted_cripto:
        if ticker_to_add_cripto:
            save_portfolio_item(ticker_to_add_cripto, cantidad_input_cripto, precio_compra_input_cripto, compra_currency_cripto, nombre_personalizado_cripto, user_id)
            st.success(f"✔️ Activo '{ticker_to_add_cripto}' añadido con éxito.")
            st.rerun()  
        else:
            st.error("❌ Debes seleccionar un ticker de criptomoneda válido.")

st.sidebar.markdown("---")

# --- Formulario para Eliminar Activos ---
with st.sidebar.form("eliminar_form"):
    st.subheader("Eliminar Activo")
    tickers_in_portfolio = sorted(load_portfolio(user_id)['ticker'].unique().tolist())
    ticker_to_delete = st.selectbox("Selecciona un ticker para eliminar:", options=["-- Selecciona uno --"] + tickers_in_portfolio, key="delete_ticker_select")
    submitted_delete = st.form_submit_button("Eliminar")

    if submitted_delete:
        if ticker_to_delete and ticker_to_delete != "-- Selecciona uno --":
            delete_portfolio_item(ticker_to_delete, user_id)
            st.success(f"✔️ Todas las compras del activo '{ticker_to_delete}' eliminadas.")
            st.rerun()  
        else:
            st.warning("⚠️ Debes seleccionar un ticker para eliminar.")

st.sidebar.markdown("---")
st.sidebar.info("✨ Utiliza `yf.download` para obtener los precios más recientes.")
st.sidebar.info(f"💾 Los datos se guardan en `precios_portfolio.db`. El valor total se calcula en {BASE_CURRENCY}.")

# --- MAIN CONTENT: Dashboard ---
st.title("💰 Dashboard de Portfolio de Inversión")
st.markdown("Revisa el rendimiento de tu portfolio en tiempo real y gestiona tus inversiones.")

total_invested_base, total_market_value_base, df_details, df_acciones, df_cryptos = calculate_portfolio_summary(user_id)

if not df_details.empty:
    st.markdown("### Resumen del Portfolio")
    total_invested_base_float = float(total_invested_base)
    total_market_value_base_float = float(total_market_value_base)
    rentabilidad_total = total_market_value_base_float - total_invested_base_float
    rentabilidad_porcentaje = (rentabilidad_total / total_invested_base_float) * 100 if total_invested_base_float != 0 else 0

    col1, col2, col3 = st.columns(3)
    
    col1.metric(f"Valor Total del Portfolio ({BASE_CURRENCY})", f"${total_market_value_base_float:,.2f}")
    col2.metric(f"Inversión Inicial ({BASE_CURRENCY})", f"${total_invested_base_float:,.2f}")
    
    delta_color = "inverse" if rentabilidad_total < 0 else "normal"
    col3.metric(
        "Rentabilidad Total",
        f"${rentabilidad_total:,.2f}",
        f"{rentabilidad_porcentaje:,.2f}%",
        delta_color=delta_color
    )

    st.markdown("---")
    
    st.markdown("### Distribución del Portfolio")
    col_pies_1, col_pies_2 = st.columns(2)
    
    # --- LÓGICA DE COLORES CENTRALIZADA Y ROBUSTA ---
    red = (255, 0, 0)
    yellow = (255, 255, 128)
    green = (0, 128, 0)

    def interpolate_color_bipolar_robust(val, min_neg, max_pos):
        def interpolate_two_colors(color1, color2, ratio):
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            return f'rgb({r}, {g}, {b})'
        
        if val is None or pd.isna(val):
            return 'rgb(192, 192, 192)'

        if val < 0:
            if min_neg is None or min_neg == 0:
                return f'rgb({yellow[0]}, {yellow[1]}, {yellow[2]})'
            ratio = min(1.0, abs(val) / abs(min_neg))
            return interpolate_two_colors(yellow, red, ratio)
        else:
            if max_pos is None or max_pos == 0:
                return f'rgb({yellow[0]}, {yellow[1]}, {yellow[2]})'
            ratio = min(1.0, val / max_pos)
            return interpolate_two_colors(yellow, green, ratio)
    
    # --- GRÁFICO DE ACCIONES ---
    with col_pies_1:
        df_acciones_positivas = df_acciones[df_acciones[f'Valor de Mercado ({BASE_CURRENCY})'] > 0].copy()
        if not df_acciones_positivas.empty:
            df_acciones_sorted = df_acciones_positivas.sort_values(by='Rentabilidad (%)')
            min_neg_rent_acciones = df_acciones_sorted['Rentabilidad (%)'][df_acciones_sorted['Rentabilidad (%)'] < 0].min()
            max_pos_rent_acciones = df_acciones_sorted['Rentabilidad (%)'][df_acciones_sorted['Rentabilidad (%)'] > 0].max()
            
            custom_colors_acciones = [
                interpolate_color_bipolar_robust(val, min_neg_rent_acciones, max_pos_rent_acciones) 
                for val in df_acciones_sorted['Rentabilidad (%)']
            ]
            
            fig_acciones = px.pie(
                df_acciones_sorted,
                values=f'Valor de Mercado ({BASE_CURRENCY})',
                names='Nombre',
                title='Distribución de Acciones',
                hole=0.4,
                color='Nombre',
                color_discrete_map={name: color for name, color in zip(df_acciones_sorted['Nombre'], custom_colors_acciones)}
            )
            fig_acciones.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_acciones, use_container_width=True)
        else:
            st.info("ℹ️ No hay acciones con valor de mercado positivo.")

    # --- GRÁFICO DE CRIPTOMONEDAS ---
    with col_pies_2:
        df_cryptos_positivas = df_cryptos[df_cryptos[f'Valor de Mercado ({BASE_CURRENCY})'] > 0].copy()
        if not df_cryptos_positivas.empty:
            df_cryptos_sorted = df_cryptos_positivas.sort_values(by='Rentabilidad (%)')
            min_neg_rent_cryptos = df_cryptos_sorted['Rentabilidad (%)'][df_cryptos_sorted['Rentabilidad (%)'] < 0].min()
            max_pos_rent_cryptos = df_cryptos_sorted['Rentabilidad (%)'][df_cryptos_sorted['Rentabilidad (%)'] > 0].max()

            custom_colors_cryptos = [
                interpolate_color_bipolar_robust(val, min_neg_rent_cryptos, max_pos_rent_cryptos) 
                for val in df_cryptos_sorted['Rentabilidad (%)']
            ]

            fig_cryptos = px.pie(
                df_cryptos_sorted,
                values=f'Valor de Mercado ({BASE_CURRENCY})',
                names='Nombre',
                title='Distribución de Criptomonedas',
                hole=0.4,
                color='Nombre',
                color_discrete_map={name: color for name, color in zip(df_cryptos_sorted['Nombre'], custom_colors_cryptos)}
            )
            fig_cryptos.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_cryptos, use_container_width=True)
        else:
            st.info("ℹ️ No hay criptomonedas con valor de mercado positivo.")
    
    # --- GRÁFICO TOTAL DEL PORTFOLIO ---
    df_details_positivos = df_details[df_details[f'Valor de Mercado ({BASE_CURRENCY})'] > 0].copy()
    if not df_details_positivos.empty:
        df_sorted = df_details_positivos.sort_values(by='Rentabilidad (%)')
        
        min_neg_rent_total = df_sorted['Rentabilidad (%)'][df_sorted['Rentabilidad (%)'] < 0].min()
        max_pos_rent_total = df_sorted['Rentabilidad (%)'][df_sorted['Rentabilidad (%)'] > 0].max()

        custom_colors = [
            interpolate_color_bipolar_robust(val, min_neg_rent_total, max_pos_rent_total) 
            for val in df_sorted['Rentabilidad (%)']
        ]
        
        fig_total = px.pie(
            df_sorted,
            values=f'Valor de Mercado ({BASE_CURRENCY})',
            names='Nombre',
            title='Distribución Total del Portfolio',
            hole=0.4,
            color='Nombre',
            color_discrete_map={name: color for name, color in zip(df_sorted['Nombre'], custom_colors)}
        )

        fig_total.update_layout(height=600, width=800)
        fig_total.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_total, use_container_width=False)
    else:
        st.warning("⚠️ No hay activos con un valor de mercado positivo para mostrar en el gráfico.")
    
    st.markdown("---")
    
    st.markdown("### Detalles de los Activos")
    
    df_display = df_details.copy()

    def format_currency_symbol(currency_code):
        return CURRENCY_SYMBOLS.get(currency_code, "")

    def format_rentabilidad(row):
        currency_code = TICKER_DETAILS.get(row['Ticker'], {}).get('currency')
        value = row[f'Rentabilidad ({currency_code})']
        symbol = format_currency_symbol(currency_code)
        if pd.isna(value) or value is None:
            return "N/A"
        return f"{symbol}{value:,.2f}"

    def format_valor_mercado(row):
        currency_code = TICKER_DETAILS.get(row['Ticker'], {}).get('currency')
        value = row[f'Valor de Mercado Original ({currency_code})']
        symbol = format_currency_symbol(currency_code)
        if pd.isna(value) or value is None:
            return "N/A"
        return f"{symbol}{value:,.2f}"

    def format_price(value, currency_code):
        symbol = format_currency_symbol(currency_code)
        if pd.isna(value) or value is None:
            return "N/A"
        return f"{symbol}{value:,.2f}"
    
    def format_inversion_inicial(row):
        currency_code = row['Divisa de Compra']
        value = row[f'Inversión Inicial Original ({currency_code})']
        symbol = format_currency_symbol(currency_code)
        if pd.isna(value) or value is None:
            return "N/A"
        return f"{symbol}{value:,.2f}"

    df_display['Valor de Mercado'] = df_display.apply(format_valor_mercado, axis=1)
    df_display['Rentabilidad'] = df_display.apply(format_rentabilidad, axis=1)
    df_display['Rentabilidad (%)'] = df_display['Rentabilidad (%)'].apply(lambda x: f'{x:.2f}%' if pd.notna(x) else 'N/A')
    df_display['Inversión Inicial'] = df_display.apply(format_inversion_inicial, axis=1)
    df_display['Peso en el Portfolio (%)'] = df_display['Peso en el Portfolio (%)'].apply(lambda x: f'{x:.2f}%' if pd.notna(x) else '0.00%')
    df_display['Precio de Compra Promedio'] = df_display.apply(
        lambda row: format_price(row[f'Precio de Compra Promedio ({row["Divisa de Compra"]})'], row["Divisa de Compra"]), axis=1
    )
    df_display['Precio Actual'] = df_display.apply(
        lambda row: format_price(row[f'Precio Actual ({TICKER_DETAILS.get(row["Ticker"], {}).get("currency")})'], TICKER_DETAILS.get(row["Ticker"], {}).get("currency")), axis=1
    )
    
    display_cols = [
        'Nombre', 'Ticker', 'Tipo', 'Divisa de Activo', 'Cantidad', 'Precio de Compra Promedio', 'Precio Actual',
        'Valor de Mercado', 'Rentabilidad', 'Rentabilidad (%)',
        'Inversión Inicial', 'Peso en el Portfolio (%)'
    ]
    st.dataframe(df_display[display_cols], use_container_width=True)

else:
    st.info("ℹ️ Tu portfolio está vacío. Usa la barra lateral para añadir tus primeros activos.")