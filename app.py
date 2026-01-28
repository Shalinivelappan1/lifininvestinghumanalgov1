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
            "ABC": {"price": 100.0, "history": [], "halted": False},
            "XYZ": {"price": 200.0, "history": [], "halted": False},
        },
        "news_shock": {"ABC": 0.0, "XYZ": 0.0},
        "liquidity_freeze": False,
        "humans": {},
        "bots": {},
        "last_prices": {"ABC": 100.0, "XYZ": 200.0}
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
st.title("🤖📈 Human vs Algorithm Market Simulator — Policy & Panic Edition")
st.caption("Instructor-controlled | 10 Humans | 2 Assets | Circuit Breakers | Central Bank")

market = st.session_state.market

# ======================================
# SIDEBAR: POLICY CONTROLS
# ======================================
st.sidebar.header("📰 Shocks & Policy Tools")

asset_for_action = st.sidebar.selectbox("Select Asset", ["ABC", "XYZ"])

if st.sidebar.button("🚨 Bad News (-10%)"):
    market["news_shock"][asset_for_action] = -0.10

if st.sidebar.button("✅ Good News (+10%)"):
    market["news_shock"][asset_for_action] = +0.10

if st.sidebar.button("💣 Flash Crash (-25%)"):
    market["news_shock"][asset_for_action] = -0.25

st.sidebar.divider()

if st.sidebar.button("🧊 Toggle Liquidity Freeze (All Assets)"):
    market["liquidity_freeze"] = not market["liquidity_freeze"]

if st.sidebar.button("🏦 Central Bank Intervention (+15%)"):
    for a in market["assets"]:
        market["assets"][a]["price"] *= 1.15

st.sidebar.divider()

if st.sidebar.button("🔁 Reset Simulation"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# ======================================
# EXPORT
# ======================================
if st.sidebar.button("📤 Export Results to Excel"):
    rows = []
    for name, h in market["humans"].items():
        net = h["cash"]
        for a in ["ABC", "XYZ"]:
            net += h["positions"][a] * market["assets"][a]["price"]
        rows.append({
            "Agent": name,
            "Type": "Human",
            "Cash": h["cash"],
            "ABC": h["positions"]["ABC"],
            "XYZ": h["positions"]["XYZ"],
            "NetWorth": net
        })

    for name, b in market["bots"].items():
        net = b["cash"]
        for a in ["ABC", "XYZ"]:
            net += b["positions"][a] * market["assets"][a]["price"]
        rows.append({
            "Agent": name,
            "Type": "Bot",
            "Cash": b["cash"],
            "ABC": b["positions"]["ABC"],
            "XYZ": b["positions"]["XYZ"],
            "NetWorth": net
        })

    df = pd.DataFrame(rows)
    df.to_excel("market_results.xlsx", index=False)
    st.sidebar.success("Exported to market_results.xlsx")

# ======================================
# MARKET STATUS
# ======================================
st.subheader("📊 Market Status")

cols = st.columns(5)
cols[0].metric("Round", market["round"])
cols[1].metric("ABC Price", f"₹ {market['assets']['ABC']['price']:.2f}", "HALTED" if market["assets"]["ABC"]["halted"] else "LIVE")
cols[2].metric("XYZ Price", f"₹ {market['assets']['XYZ']['price']:.2f}", "HALTED" if market["assets"]["XYZ"]["halted"] else "LIVE")
cols[3].metric("Liquidity", "FROZEN" if market["liquidity_freeze"] else "NORMAL")
cols[4].metric("Agents", 10 + len(market["bots"]))

# ======================================
# CONFIDENCE SLIDER
# ======================================
st.subheader("🧠 Committee Confidence")

confidence = st.slider(
    "How confident is the class in its decision?",
    min_value=0.2,
    max_value=2.0,
    value=1.0,
    step=0.1
)

base_qty = 10
human_qty = int(base_qty * confidence)

st.info(f"📏 This round, each human trades **{human_qty} shares** if they Buy/Sell.")

# ======================================
# HUMAN DECISIONS
# ======================================
st.subheader("👩‍🏫 Human Traders Decisions")

human_orders = {}

cols = st.columns(5)
for idx, name in enumerate(market["humans"].keys()):
    with cols[idx % 5]:
        st.markdown(f"**{name}**")

        asset = st.selectbox("Asset", ["ABC", "XYZ"], key=f"{name}_asset")

        action = st.radio(
            "Action",
            ["HOLD", "BUY", "SELL"],
            horizontal=True,
            key=f"{name}_action"
        )

        human_orders[name] = {"asset": asset, "action": action}

# ======================================
# RUN ONE ROUND
# ======================================
if st.button("▶️ Run Next Market Round"):

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
    if not market["liquidity_freeze"]:
        for hname, order in human_orders.items():
            human = market["humans"][hname]
            asset = order["asset"]
            action = order["action"]

            if market["assets"][asset]["halted"]:
                continue

            price = market["assets"][asset]["price"]
            qty = human_qty

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
    if not market["liquidity_freeze"]:
        for bname in market["bots"]:
            for asset in ["ABC", "XYZ"]:
                if market["assets"][asset]["halted"]:
                    continue

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
    # PRICE FORMATION + CIRCUIT BREAKER
    # ----------------------------
    for asset in ["ABC", "XYZ"]:
        old_price = market["assets"][asset]["price"]

        imbalance = buy_volume[asset] - sell_volume[asset]
        price_change = imbalance / 50.0
        new_price = max(1.0, old_price + price_change)

        # Save history
        market["assets"][asset]["history"].append(old_price)

        # Circuit breaker: 10% move limit
        if abs(new_price - market["last_prices"][asset]) / market["last_prices"][asset] > 0.10:
            market["assets"][asset]["halted"] = True
        else:
            market["assets"][asset]["price"] = new_price
            market["last_prices"][asset] = new_price

    market["round"] += 1

# ======================================
# PRICE CHARTS
# ======================================
st.subheader("📈 Price Evolution")

col1, col2 = st.columns(2)

with col1:
    hist = market["assets"]["ABC"]["history"]
    if len(hist) > 0:
        df = pd.DataFrame({"Round": range(1, len(hist)+1), "Price": hist})
        st.line_chart(df.set_index("Round"))

with col2:
    hist = market["assets"]["XYZ"]["history"]
    if len(hist) > 0:
        df = pd.DataFrame({"Round": range(1, len(hist)+1), "Price": hist})
        st.line_chart(df.set_index("Round"))

# ======================================
# LEADERBOARD
# ======================================
st.subheader("🏆 Leaderboard")

rows = []

# Humans
for name, h in market["humans"].items():
    net = h["cash"]
    for a in ["ABC", "XYZ"]:
        net += h["positions"][a] * market["assets"][a]["price"]
    rows.append({"Agent": name, "Type": "Human", "NetWorth": round(net, 0)})

# Bots
for name, b in market["bots"].items():
    net = b["cash"]
    for a in ["ABC", "XYZ"]:
        net += b["positions"][a] * market["assets"][a]["price"]
    rows.append({"Agent": name, "Type": "Bot", "NetWorth": round(net, 0)})

df = pd.DataFrame(rows).sort_values("NetWorth", ascending=False)
st.dataframe(df, use_container_width=True)

# ======================================
# TEACHING NOTES
# ======================================
st.info("""
🎓 Teaching moves you can do live:

• Increase confidence slider → show overtrading
• Hit Liquidity Freeze → show 'no bid, no offer'
• Trigger Flash Crash → see Panic Bot dominate
• Trigger Central Bank → show moral hazard & reversals
• Let Circuit Breaker halt one stock → discuss regulation vs discovery
• Export Excel → analyze who traded too much, who survived
""")
