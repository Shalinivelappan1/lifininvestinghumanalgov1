import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Market as a Machine: Humans vs Algorithms-Designed by Prof.Shalini Velappan", layout="wide")

# ====================================
# INITIALIZE STATE
# ====================================
if "price" not in st.session_state:
    st.session_state.price = 100.0
    st.session_state.round = 1
    st.session_state.history = []
    st.session_state.news_shock = 0.0

    # Agents: Human + Bots
    st.session_state.agents = {
        "👩‍🎓 Class (Humans)": {"cash": 100000, "shares": 100},
        "🤖 Momentum Bot": {"cash": 100000, "shares": 100},
        "🤖 MeanReversion Bot": {"cash": 100000, "shares": 100},
        "🤖 Panic Bot": {"cash": 100000, "shares": 100},
        "🤖 Random Bot": {"cash": 100000, "shares": 100},
        "🤖 Trend Follower": {"cash": 100000, "shares": 100},
    }

# ====================================
# TITLE
# ====================================
st.title("🤖📈 Market as a Machine: Humans vs Algorithms")
st.caption("Instructor-controlled live classroom market simulator")

# ====================================
# CONTROL PANEL
# ====================================
st.sidebar.header("📰 News & Shocks")

if st.sidebar.button("🚨 Bad News"):
    st.session_state.news_shock = -0.05

if st.sidebar.button("✅ Good News"):
    st.session_state.news_shock = +0.05

if st.sidebar.button("💣 Flash Crash"):
    st.session_state.news_shock = -0.15

if st.sidebar.button("🔁 Reset Simulation"):
    for k in st.session_state.keys():
        del st.session_state[k]
    st.rerun()

# ====================================
# MARKET STATUS
# ====================================
col1, col2, col3 = st.columns(3)
col1.metric("Current Price", f"₹ {st.session_state.price:.2f}")
col2.metric("Round", st.session_state.round)
col3.metric("Agents", len(st.session_state.agents))

# ====================================
# HUMAN DECISION
# ====================================
st.subheader("👩‍🏫 Class Decision (Ask students & click)")

human_action = st.radio(
    "What should WE do this round?",
    ["BUY", "SELL", "HOLD"],
    horizontal=True
)

# ====================================
# RUN ROUND
# ====================================
if st.button("▶️ Run Next Round"):

    buy_volume = 0
    sell_volume = 0
    last_price = st.session_state.price

    # --------------------------
    # Apply News Shock
    # --------------------------
    st.session_state.price *= (1 + st.session_state.news_shock)
    st.session_state.news_shock = 0.0

    # --------------------------
    # Human action
    # --------------------------
    human = st.session_state.agents["👩‍🎓 Class (Humans)"]
    qty = 20

    if human_action == "BUY" and human["cash"] >= qty * st.session_state.price:
        human["cash"] -= qty * st.session_state.price
        human["shares"] += qty
        buy_volume += qty

    elif human_action == "SELL" and human["shares"] >= qty:
        human["shares"] -= qty
        human["cash"] += qty * st.session_state.price
        sell_volume += qty

    # --------------------------
    # BOT ACTIONS
    # --------------------------
    for name, agent in st.session_state.agents.items():
        if "Bot" not in name:
            continue

        # Momentum Bot
        if "Momentum" in name and len(st.session_state.history) > 0:
            if st.session_state.price > st.session_state.history[-1]["price"]:
                buy_volume += 15
                agent["shares"] += 15
                agent["cash"] -= 15 * st.session_state.price
            else:
                sell_volume += 15
                agent["shares"] -= 15
                agent["cash"] += 15 * st.session_state.price

        # Mean Reversion
        if "MeanReversion" in name:
            if st.session_state.price > 105:
                sell_volume += 15
                agent["shares"] -= 15
                agent["cash"] += 15 * st.session_state.price
            elif st.session_state.price < 95:
                buy_volume += 15
                agent["shares"] += 15
                agent["cash"] -= 15 * st.session_state.price

        # Panic Bot
        if "Panic" in name and len(st.session_state.history) > 0:
            if st.session_state.price < 0.97 * st.session_state.history[-1]["price"]:
                sell_volume += 40
                agent["shares"] -= 40
                agent["cash"] += 40 * st.session_state.price

        # Random Bot
        if "Random" in name:
            if np.random.rand() > 0.5:
                buy_volume += 10
                agent["shares"] += 10
                agent["cash"] -= 10 * st.session_state.price
            else:
                sell_volume += 10
                agent["shares"] -= 10
                agent["cash"] += 10 * st.session_state.price

        # Trend Follower
        if "Trend" in name and len(st.session_state.history) > 1:
            if st.session_state.history[-1]["price"] > st.session_state.history[-2]["price"]:
                buy_volume += 20
                agent["shares"] += 20
                agent["cash"] -= 20 * st.session_state.price

    # --------------------------
    # PRICE FORMATION
    # --------------------------
    imbalance = buy_volume - sell_volume
    price_change = imbalance / 50.0
    st.session_state.price = max(1, st.session_state.price + price_change)

    # --------------------------
    # SAVE HISTORY
    # --------------------------
    st.session_state.history.append({
        "round": st.session_state.round,
        "price": st.session_state.price,
        "buy": buy_volume,
        "sell": sell_volume
    })

    st.session_state.round += 1

# ====================================
# PRICE CHART
# ====================================
if len(st.session_state.history) > 0:
    st.subheader("📈 Price Evolution")
    df = pd.DataFrame(st.session_state.history)
    st.line_chart(df.set_index("round")["price"])

# ====================================
# LEADERBOARD
# ====================================
st.subheader("🏆 Performance Leaderboard")

rows = []
for name, a in st.session_state.agents.items():
    net = a["cash"] + a["shares"] * st.session_state.price
    rows.append({
        "Agent": name,
        "Cash": round(a["cash"], 0),
        "Shares": a["shares"],
        "Net Worth": round(net, 0)
    })

df = pd.DataFrame(rows).sort_values("Net Worth", ascending=False)
st.dataframe(df, use_container_width=True)

# ====================================
# TEACHING NOTES
# ====================================
st.info("""
🎓 How to run this in class:

1. Ask students: BUY / SELL / HOLD?
2. Click the decision.
3. Click 'Run Next Round'.
4. Occasionally click:
   - 🚨 Bad News
   - 💣 Flash Crash
   - ✅ Good News
5. Watch:
   - Momentum amplify moves
   - Panic bot create crashes
   - Humans overreact or underreact
6. Show leaderboard and ask:
   "Why is this bot winning?"
""")
