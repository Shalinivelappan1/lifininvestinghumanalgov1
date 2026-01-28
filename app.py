import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Human vs Algo Market Lab", layout="wide")

# ======================================
# INITIALIZE STATE
# ======================================
if "market" not in st.session_state:
    st.session_state.market = {
        "round": 1,
        "assets": {
            "ABC": {"price": 100.0, "history": []},
            "XYZ": {"price": 200.0, "history": []},
        },
        "news_shock": {"ABC": 0.0, "XYZ": 0.0},
        "humans": {},
        "bots": {},
    }

    # Create 10 human traders
    for i in range(1, 11):
        st.session_state.market["humans"][f"Human_{i}"] = {
            "cash": 100000.0,
            "positions": {"ABC": 50, "XYZ": 25}
        }

    # Create bots
    bot_names = [
        "Momentum Bot",
        "MeanReversion Bot",
        "Panic Bot",
        "Random Bot",
        "Trend Bot"
    ]

    for b in bot_names:
        st.session_state.market["bots"][b] = {
            "cash": 200000.0,
            "positions": {"ABC": 100, "XYZ": 50}
        }

# ======================================
# TITLE
# ======================================
st.title("🤖📈 Human vs Algorithm Market Simulator (Instructor Controlled)")
st.caption("10 Human Traders vs Algo Bots | 2 Assets | Live Classroom Experiment")

# ======================================
# SIDEBAR: NEWS CONTROLS
# ======================================
st.sidebar.header("📰 News Shocks")

asset_for_news = st.sidebar.selectbox("Select Asset for News", ["ABC", "XYZ"])

if st.sidebar.button("🚨 Bad News (-10%)"):
    st.session_state.market["news_shock"][asset_for_news] = -0.10

if st.sidebar.button("✅ Good News (+10%)"):
    st.session_state.market["news_shock"][asset_for_news] = +0.10

if st.sidebar.button("💣 Flash Crash (-25%)"):
    st.session_state.market["news_shock"][asset_for_news] = -0.25

if st.sidebar.button("🔁 Reset Simulation"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# ======================================
# MARKET STATUS
# ======================================
st.subheader("📊 Market Status")

cols = st.columns(4)
cols[0].metric("Round", st.session_state.market["round"])
cols[1].metric("ABC Price", f"₹ {st.session_state.market['assets']['ABC']['price']:.2f}")
cols[2].metric("XYZ Price", f"₹ {st.session_state.market['assets']['XYZ']['price']:.2f}")
cols[3].metric("Total Agents", 10 + len(st.session_state.market["bots"]))

# ======================================
# HUMAN DECISIONS PANEL
# ======================================
st.subheader("👩‍🏫 Human Traders Decisions (Ask students & select)")

human_orders = {}

human_names = list(st.session_state.market["humans"].keys())
cols = st.columns(5)

for idx, name in enumerate(human_names):
    with cols[idx % 5]:
        st.markdown(f"**{name}**")

        asset = st.selectbox(
            "Asset",
            ["ABC", "XYZ"],
            key=f"{name}_asset"
        )

        action = st.radio(
            "Action",
            ["HOLD", "BUY", "SELL"],
            horizontal=True,
            key=f"{name}_action"
        )

        human_orders[name] = {
            "asset": asset,
            "action": action
        }

# ======================================
# RUN ONE ROUND
# ======================================
if st.button("▶️ Run Next Market Round"):

    market = st.session_state.market

    # ----------------------------
    # Apply News Shocks
    # ----------------------------
    for a in market["assets"]:
        shock = market["news_shock"][a]
        if shock != 0:
            market["assets"][a]["price"] *= (1 + shock)
            market["news_shock"][a] = 0.0

    # ----------------------------
    # Volume trackers
    # ----------------------------
    buy_volume = {"ABC": 0, "XYZ": 0}
    sell_volume = {"ABC": 0, "XYZ": 0}

    # ----------------------------
    # Execute Human Orders
    # ----------------------------
    qty = 10

    for hname, order in human_orders.items():
        human = market["humans"][hname]
        asset = order["asset"]
        action = order["action"]
        price = market["assets"][asset]["price"]

        if action == "BUY" and human["cash"] >= qty * price:
            human["cash"] -= qty * price
            human["positions"][asset] += qty
            buy_volume[asset] += qty

        elif action == "SELL" and human["positions"][asset] >= qty:
            human["positions"][asset] -= qty
            human["cash"] += qty * price
            sell_volume[asset] += qty

    # ----------------------------
    # BOT BEHAVIOUR
    # ----------------------------
    for bname, bot in market["bots"].items():
        for asset in ["ABC", "XYZ"]:
            price = market["assets"][asset]["price"]
            history = market["assets"][asset]["history"]

            # Momentum
            if "Momentum" in bname and len(history) > 0:
                if price > history[-1]:
                    buy_volume[asset] += 20
                else:
                    sell_volume[asset] += 20

            # Mean Reversion
            if "MeanReversion" in bname:
                if price > (120 if asset == "ABC" else 240):
                    sell_volume[asset] += 15
                elif price < (80 if asset == "ABC" else 160):
                    buy_volume[asset] += 15

            # Panic
            if "Panic" in bname and len(history) > 0:
                if price < 0.95 * history[-1]:
                    sell_volume[asset] += 40

            # Random
            if "Random" in bname:
                if np.random.rand() > 0.5:
                    buy_volume[asset] += 10
                else:
                    sell_volume[asset] += 10

            # Trend
            if "Trend" in bname and len(history) > 1:
                if history[-1] > history[-2]:
                    buy_volume[asset] += 20

    # ----------------------------
    # PRICE FORMATION
    # ----------------------------
    for asset in ["ABC", "XYZ"]:
        imbalance = buy_volume[asset] - sell_volume[asset]
        price_change = imbalance / 50.0
        new_price = max(1.0, market["assets"][asset]["price"] + price_change)

        market["assets"][asset]["history"].append(market["assets"][asset]["price"])
        market["assets"][asset]["price"] = new_price

    market["round"] += 1

# ======================================
# PRICE CHARTS
# ======================================
st.subheader("📈 Price Evolution")

col1, col2 = st.columns(2)

with col1:
    hist = st.session_state.market["assets"]["ABC"]["history"]
    if len(hist) > 0:
        df = pd.DataFrame({"Round": range(1, len(hist)+1), "Price": hist})
        st.line_chart(df.set_index("Round"))

with col2:
    hist = st.session_state.market["assets"]["XYZ"]["history"]
    if len(hist) > 0:
        df = pd.DataFrame({"Round": range(1, len(hist)+1), "Price": hist})
        st.line_chart(df.set_index("Round"))

# ======================================
# LEADERBOARD
# ======================================
st.subheader("🏆 Leaderboard (Humans + Bots)")

rows = []

# Humans
for name, h in st.session_state.market["humans"].items():
    net = h["cash"]
    for a in ["ABC", "XYZ"]:
        net += h["positions"][a] * st.session_state.market["assets"][a]["price"]

    rows.append({
        "Agent": name,
        "Type": "Human",
        "Net Worth": round(net, 0)
    })

# Bots
for name, b in st.session_state.market["bots"].items():
    net = b["cash"]
    for a in ["ABC", "XYZ"]:
        net += b["positions"][a] * st.session_state.market["assets"][a]["price"]

    rows.append({
        "Agent": name,
        "Type": "Bot",
        "Net Worth": round(net, 0)
    })

df = pd.DataFrame(rows).sort_values("Net Worth", ascending=False)
st.dataframe(df, use_container_width=True)

# ======================================
# TEACHING NOTES
# ======================================
st.info("""
🎓 How to use in class:

1. For each Human_1 ... Human_10, ask that student group:
   "What do you want to do? Buy / Sell / Hold? Which asset?"
2. Set their choices.
3. Click "Run Next Market Round".
4. Occasionally click:
   - 🚨 Bad News
   - 💣 Flash Crash
   - ✅ Good News
5. Show:
   - Who panics
   - Who follows momentum
   - Who survives volatility
   - Which bots dominate
""")
