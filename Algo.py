import requests
import pandas as pd
import matplotlib.pyplot as plt

# ===== Configuration =====
API_KEY = "demo"  # Replace with your actual API key from Alpha Vantage
CURRENCY_PAIR = "EUR/USD"
SHORT_WINDOW = 5
LONG_WINDOW = 20
INITIAL_BALANCE = 10000


# ===== Fetch Forex Data =====
def fetch_forex_data(symbol="EUR/USD", interval="60min", api_key="demo"):
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "FX_INTRADAY",
        "from_symbol": symbol.split('/')[0],
        "to_symbol": symbol.split('/')[1],
        "interval": interval,
        "apikey": api_key,
        "outputsize": "compact"
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if "Time Series FX" in data:
        key = list(data.keys())[1]
        df = pd.DataFrame.from_dict(data[key], orient="index")
        df.rename(columns={
            '1. open': 'open',
            '2. high': 'high',
            '3. low': 'low',
            '4. close': 'close'
        }, inplace=True)
        df = df.astype(float)
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        return df
    else:
        raise ValueError("Failed to fetch forex data. Please check API key or symbol.")


# ===== SMA Crossover Strategy =====
def apply_sma_strategy(df, short_window=5, long_window=20):
    df['SMA_Short'] = df['close'].rolling(window=short_window).mean()
    df['SMA_Long'] = df['close'].rolling(window=long_window).mean()
    df['Signal'] = 0
    df['Signal'][short_window:] = (df['SMA_Short'][short_window:] > df['SMA_Long'][short_window:]).astype(int)
    df['Position'] = df['Signal'].diff()
    return df


# ===== Backtesting the Strategy =====
def run_backtest(df, initial_balance=10000):
    balance = initial_balance
    position = 0
    trades = []

    for i in range(1, len(df)):
        if df['Position'].iloc[i] == 1:  # Buy Signal
            position = balance / df['close'].iloc[i]
            balance = 0
            trades.append(('BUY', df.index[i], df['close'].iloc[i]))

        elif df['Position'].iloc[i] == -1 and position > 0:  # Sell Signal
            balance = position * df['close'].iloc[i]
            position = 0
            trades.append(('SELL', df.index[i], df['close'].iloc[i]))

    # Final balance if still holding a position
    final_value = balance if position == 0 else position * df['close'].iloc[-1]
    profit = final_value - initial_balance

    print(f"\n🔄 Total Trades: {len(trades)}")
    print(f"💰 Final Balance: ${final_value:.2f}")
    print(f"📈 Net Profit: ${profit:.2f}")

    return trades, final_value


# ===== Plot Buy/Sell Signals =====
def plot_signals(df):
    plt.figure(figsize=(14, 7))
    plt.plot(df['close'], label='Price', color='gray')
    plt.plot(df['SMA_Short'], label=f'SMA {SHORT_WINDOW}', color='blue')
    plt.plot(df['SMA_Long'], label=f'SMA {LONG_WINDOW}', color='orange')

    buy_signals = df[df['Position'] == 1]
    sell_signals = df[df['Position'] == -1]

    plt.scatter(buy_signals.index, buy_signals['close'], marker='^', color='green', label='Buy', s=100)
    plt.scatter(sell_signals.index, sell_signals['close'], marker='v', color='red', label='Sell', s=100)

    plt.title("Forex Algo Trading – SMA Crossover Strategy", fontsize=14)
    plt.xlabel("Date/Time")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# ===== Main Function =====
def main():
    print("📡 Fetching forex data...")
    df = fetch_forex_data(symbol=CURRENCY_PAIR, api_key=API_KEY)

    print("🧠 Applying strategy...")
    df = apply_sma_strategy(df, SHORT_WINDOW, LONG_WINDOW)

    print("🧪 Running backtest...")
    trades, final_balance = run_backtest(df, INITIAL_BALANCE)

    print("📊 Plotting signals...")
    plot_signals(df)


if __name__ == "__main__":
    main()
