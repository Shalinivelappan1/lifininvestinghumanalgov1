import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Human vs Algo Market Lab", layout="wide")

# ======================================
# INIT STATE
# ======================================
if "market" not in st.session_state:

    market = {
        "round": 1,
        "liquidity_freeze": False,

        "assets": {
            "ABC": {"price": 100.0, "history": [], "halted": False, "pending_shock": 0.0, "cb_ref": 100.0},
            "XYZ": {"price": 200.0, "history": [], "halted": False, "pending_shock": 0.0, "cb_ref": 200.0},
        },

        "humans": {},
        "bots": {}
    }

    # 10 humans
    for i in range(1, 11):
        market["humans"][f"Human_{i}"] = {
            "cash": 100000.0,
            "pos": {"ABC": 50, "XYZ": 25}
        }

    # Bots
    bot_names = ["Momentum Bot", "MeanReversion Bot", "Panic Bot", "Random Bot", "Trend Bot"]
    for b in bot_names:
        market["bots"][b] = {
            "cash": 200000.0,
            "pos": {"ABC": 100, "XYZ": 50}
        }

    st.session_state.market = market

market = st.session_state.market

# ======================================
# TITLE
# ======================================
st.title("🤖📈 Human vs Algorithm Market Lab (Instructor Controlled)")
st.caption("10 Humans vs Algo Bots | 2 Assets | Quantity Matters")

# ======================================
# SIDEBAR CONTROLS
# ======================================
st.sidebar.header("🛠️ Market & Policy Controls")

selected_asset = st.sidebar.selectbox("Select Asset", ["ABC", "XYZ"])

if st.sidebar.button("🚨 Bad News (-10%)"):
    market["assets"][selected_asset]["pending_shock"] += -0.10

if st.sidebar.button("✅ Good News (+10%)"):
    market["assets"][selected_asset]["pending_shock"] += 0.10

if st.sidebar.button("💣 Flash Crash (-25%)"):
    market["assets"][selected_asset]["pending_shock"] += -0.25

st.sidebar.divider()

if st.sidebar.button("🧊 Toggle Liquidity Freeze"):
    market["liquidity_freeze"] = not market["liquidity_freeze"]

if st.sidebar.button("🏦 Central Bank Intervention (+15% ALL)"):
    for a in market["assets"]:
        market["assets"][a]["price"] *= 1.15
        market["assets"][a]["halted"] = False
        market["assets"][a]["cb_ref"] = market["assets"][a]["price"]

st.sidebar.divider()

if st.sidebar.button("🟢 Resume All Trading"):
    for a in market["assets"]:
        market["assets"][a]["halted"] = False
        market["assets"][a]["cb_ref"] = market["assets"][a]["price"]

st.sidebar.divider()

if st.sidebar.button("🔁 Reset Simulation"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# ======================================
# MARKET STATUS
# ======================================
st.subheader("📊 Market Status")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Round", market["round"])
c2.metric("ABC", f"₹ {market['assets']['ABC']['price']:.2f}", "HALTED" if market["assets"]["ABC"]["halted"] else "LIVE")
c3.metric("XYZ", f"₹ {market['assets']['XYZ']['price']:.2f}", "HALTED" if market["assets"]["XYZ"]["halted"] else "LIVE")
c4.metric("Liquidity", "FROZEN" if market["liquidity_freeze"] else "NORMAL")

# ======================================
# HUMAN DECISIONS
# ======================================
st.subheader("👩‍🏫 Human Traders Decisions (Exact Quantities)")

human_orders = {}

cols = st.columns(5)
for i, name in enumerate(market["humans"].keys()):
    with cols[i % 5]:
        st.markdown(f"**{name}**")

        asset = st.selectbox("Asset", ["ABC", "XYZ"], key=f"{name}_asset")
        action = st.radio("Action", ["HOLD", "BUY", "SELL"], horizontal=True, key=f"{name}_action")
        qty = st.number_input("Qty", min_value=0, max_value=500, value=0, step=10, key=f"{name}_qty")

        human_orders[name] = {"asset": asset, "action": action, "qty": qty}

# ======================================
# RUN ROUND
# ======================================
if st.button("▶️ Run Next Market Round"):

    # 1. Apply news shocks
    for a in market["assets"]:
        shock = market["assets"][a]["pending_shock"]
        if shock != 0:
            market["assets"][a]["price"] *= (1 + shock)
            market["assets"][a]["pending_shock"] = 0.0

    # 2. Collect volumes
    buy_vol = {"ABC": 0, "XYZ": 0}
    sell_vol = {"ABC": 0, "XYZ": 0}

    if not market["liquidity_freeze"]:

        # Humans
        for hname, order in human_orders.items():
            asset = order["asset"]
            action = order["action"]
            qty = order["qty"]

            if qty <= 0 or market["assets"][asset]["halted"]:
                continue

            if action == "BUY":
                buy_vol[asset] += qty
            elif action == "SELL":
                sell_vol[asset] += qty

        # Bots
        for bname in market["bots"]:
            for asset in ["ABC", "XYZ"]:
                if market["assets"][asset]["halted"]:
                    continue

                price = market["assets"][asset]["price"]
                hist = market["assets"][asset]["history"]

                if "Momentum" in bname and len(hist) > 0:
                    if price > hist[-1]:
                        buy_vol[asset] += 20
                    else:
                        sell_vol[asset] += 20

                if "MeanReversion" in bname:
                    ref = 100 if asset == "ABC" else 200
                    if price > 1.2 * ref:
                        sell_vol[asset] += 15
                    elif price < 0.8 * ref:
                        buy_vol[asset] += 15

                if "Panic" in bname and len(hist) > 0:
                    if price < 0.95 * hist[-1]:
                        sell_vol[asset] += 40

                if "Random" in bname:
                    if np.random.rand() > 0.5:
                        buy_vol[asset] += 10
                    else:
                        sell_vol[asset] += 10

                if "Trend" in bname and len(hist) > 1:
                    if hist[-1] > hist[-2]:
                        buy_vol[asset] += 20

    # 3. Price formation + circuit breaker
    for asset in ["ABC", "XYZ"]:
        old_price = market["assets"][asset]["price"]
        market["assets"][asset]["history"].append(old_price)

        if market["assets"][asset]["halted"]:
            continue

        imbalance = buy_vol[asset] - sell_vol[asset]
        new_price = max(1.0, old_price + imbalance / 50.0)

        ref = market["assets"][asset]["cb_ref"]
        if abs(new_price - ref) / ref > 0.10:
            market["assets"][asset]["halted"] = True
        else:
            market["assets"][asset]["price"] = new_price
            market["assets"][asset]["cb_ref"] = new_price

    market["round"] += 1

# ======================================
# CHARTS
# ======================================
st.subheader("📈 Price Evolution")

c1, c2 = st.columns(2)
with c1:
    if len(market["assets"]["ABC"]["history"]) > 0:
        st.line_chart(pd.DataFrame({"ABC": market["assets"]["ABC"]["history"]}))
with c2:
    if len(market["assets"]["XYZ"]["history"]) > 0:
        st.line_chart(pd.DataFrame({"XYZ": market["assets"]["XYZ"]["history"]}))

# ======================================
# LEADERBOARD
# ======================================
st.subheader("🏆 Leaderboard (Real Portfolios)")

rows = []

for name, h in market["humans"].items():
    net = h["cash"] + h["pos"]["ABC"] * market["assets"]["ABC"]["price"] + h["pos"]["XYZ"] * market["assets"]["XYZ"]["price"]
    rows.append({"Agent": name, "Type": "Human", "NetWorth": round(net, 0)})

for name, b in market["bots"].items():
    net = b["cash"] + b["pos"]["ABC"] * market["assets"]["ABC"]["price"] + b["pos"]["XYZ"] * market["assets"]["XYZ"]["price"]
    rows.append({"Agent": name, "Type": "Bot", "NetWorth": round(net, 0)})

df = pd.DataFrame(rows).sort_values("NetWorth", ascending=False)
st.dataframe(df, use_container_width=True)

# ======================================
# TEACHING NOTE
# ======================================
st.info("""
Each team’s quantity is used exactly as entered.
Leaderboard shows real portfolio values vs algorithmic strategies.
This lets you teach:
• Position sizing
• Impact vs opinion
• Who actually moved the market
• Why small traders don’t crash markets, big ones do
""")
