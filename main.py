from openai import OpenAI
import streamlit as st
import yfinance as yf
import pandas as pd


# Set up OpenAI API key
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

POPULAR_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NFLX", "META", "NVDA"]

def get_stock_data(ticker, start_date='2024-01-01', end_date='2024-02-01'):
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    return stock_data

def get_ticker_data(ticker, data):
    return data.xs(ticker, level=1, axis=1)

def get_summary(tickers_data):
    SYSTEM_MSG = """
                You are a financial assistant that will retrieve multiple tables of financial market data and will summarize 
                the comparative performance in text, in full detail with highlights for each stock and also a conclusion 
                with a markdown output. BE VERY STRICT ON YOUR OUTPUT
            """
    CONTENT_MSG = ""
    tickers = tickers_data.columns.get_level_values(1).unique()
    if len(tickers) == 1:
        return "Please select at least two stock tickers for comparison."
    else: 
        for ticker in tickers:
            stock_data = tickers_data.xs(ticker, level=1, axis=1)
            CONTENT_MSG += f"This is the {ticker} stock data : {stock_data}."
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_MSG},
                    {"role": "user", "content": CONTENT_MSG}
                ] 
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error getting summary from OpenAI: {e}"

# Streamlit app setup
st.title("📊 Financial Market Analysis")

# Sidebar options
st.sidebar.header("Options")

# Set tickers
st.sidebar.subheader("Stock Tickers")
tickers = st.sidebar.multiselect("Select Stock Tickers", POPULAR_TICKERS, default=POPULAR_TICKERS[:2], max_selections=4)
if len(tickers) < 4:
    input_ticker = st.sidebar.text_input("Or enter custom stock ticker (comma-separated)").upper()
    if input_ticker:
        tickers += [ticker.strip() for ticker in input_ticker.split(",") if ticker.strip() not in tickers]
        if len(tickers) > 4:
            st.sidebar.warning("You can only select up to 4 tickers.")
        tickers = tickers[:4]  # Limit to 4 tickers
if len(tickers) == 0:
    st.sidebar.error("Please select at least one stock ticker.")
    
# Set date range
st.sidebar.subheader("Date Range")
side_cols = st.sidebar.columns(2)
with side_cols[0]:
    start_date = side_cols[0].date_input("Start Date", value=pd.to_datetime('2025-01-01'))
    
with side_cols[1]:
    end_date = side_cols[1].date_input("End Date", value=pd.to_datetime('2025-02-01'))
if start_date > end_date:
    st.sidebar.error("Start date must be before end date.")

# Get stock data
st_data = pd.DataFrame()
if len(tickers) > 0 and start_date < end_date:
    st_data = get_stock_data(tickers, start_date=str(start_date), end_date=str(end_date))

st.sidebar.subheader("Chart Type")
chart_type = st.sidebar.selectbox("Select Chart Type for tickers", ["Line", "Bar"])

# Main content area
if not st_data.empty:
    tick_tabs = st.tabs(tickers)
    for i, ticker in zip(range(len(tickers)), tickers):
        with tick_tabs[i]:
            st.subheader(f"Displaying Data for {ticker}")
            ticker_data = get_ticker_data(ticker, st_data)
            st.write(ticker_data)

    st.subheader("Stock Price Chart")      
    if chart_type == "Line":
        st.line_chart(st_data['Close'])
    elif chart_type == "Bar":
        st.bar_chart(st_data['Close'], stack=False)
else:
    st.warning("Please select at least one stock ticker or make sure that the dates are correct.")
    
# Summary button
if st.button("Comparative Performance") and tickers:
    with st.spinner("Generating summary..."):
        summary = get_summary(st_data)
        st.markdown(summary)