import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Classroom Trading Lab-Designed by Prof.Shalini Velappan", layout="wide")

# =========================================================
# GLOBAL MARKET STATE (shared)
# =========================================================
if "market" not in st.session_state:
    st.session_state.market = {
        "assets": {
            "ABC": {"price": 100.0, "halted": False},
            "XYZ": {"price": 200.0, "halted": False},
        },
        "order_books": {
            "ABC": {"buy": [], "sell": []},
            "XYZ": {"buy": [], "sell": []},
        },
        "traders": {},
        "history": [],
        "round": 1,
        "circuit_limit": 0.1,  # 10%
        "news_impact": 0.0
    }

# =========================================================
# SIDEBAR LOGIN
# =========================================================
st.sidebar.title("🔐 Login")

role = st.sidebar.selectbox("Role", ["Trader", "Instructor"])
username = st.sidebar.text_input("Your Name")

if st.sidebar.button("Login") and username != "":
    if username not in st.session_state.market["traders"]:
        st.session_state.market["traders"][username] = {
            "cash": 100000.0,
            "positions": {"ABC": 0, "XYZ": 0},
            "team": "A",
        }
    st.session_state.user = username
    st.session_state.role = role

if "user" not in st.session_state:
    st.warning("Please login from sidebar.")
    st.stop()

# =========================================================
# HELPERS
# =========================================================
def place_order(user, asset, side, qty, price, order_type):
    book = st.session_state.market["order_books"][asset][side]
    book.append({
        "user": user,
        "qty": qty,
        "price": price,
        "type": order_type,
        "time": datetime.now()
    })

def match_orders(asset):
    book = st.session_state.market["order_books"][asset]
    buys = sorted(book["buy"], key=lambda x: (-x["price"], x["time"]))
    sells = sorted(book["sell"], key=lambda x: (x["price"], x["time"]))

    trades = []

    while buys and sells and buys[0]["price"] >= sells[0]["price"]:
        buy = buys[0]
        sell = sells[0]

        traded_qty = min(buy["qty"], sell["qty"])
        trade_price = (buy["price"] + sell["price"]) / 2

        trades.append((buy["user"], sell["user"], traded_qty, trade_price))

        buy["qty"] -= traded_qty
        sell["qty"] -= traded_qty

        if buy["qty"] == 0:
            buys.pop(0)
        if sell["qty"] == 0:
            sells.pop(0)

    book["buy"] = [b for b in buys if b["qty"] > 0]
    book["sell"] = [s for s in sells if s["qty"] > 0]

    # Apply trades
    for buyer, seller, qty, price in trades:
        m = st.session_state.market
        m["traders"][buyer]["cash"] -= qty * price
        m["traders"][buyer]["positions"][asset] += qty

        m["traders"][seller]["cash"] += qty * price
        m["traders"][seller]["positions"][asset] -= qty

        m["assets"][asset]["price"] = price

# =========================================================
# INSTRUCTOR PANEL
# =========================================================
if st.session_state.role == "Instructor":
    st.title("🏛️ Instructor Control Panel")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📰 News Shocks")
        if st.button("🚨 Bad News (-10%)"):
            for a in st.session_state.market["assets"]:
                st.session_state.market["assets"][a]["price"] *= 0.9

        if st.button("✅ Good News (+10%)"):
            for a in st.session_state.market["assets"]:
                st.session_state.market["assets"][a]["price"] *= 1.1

    with col2:
        st.subheader("🛑 Circuit Breakers")
        for a in st.session_state.market["assets"]:
            if st.button(f"Toggle Halt {a}"):
                st.session_state.market["assets"][a]["halted"] = not st.session_state.market["assets"][a]["halted"]

    with col3:
        st.subheader("📤 Export")
        if st.button("Export to Excel"):
            rows = []
            for name, t in st.session_state.market["traders"].items():
                rows.append({
                    "Trader": name,
                    "Cash": t["cash"],
                    "ABC": t["positions"]["ABC"],
                    "XYZ": t["positions"]["XYZ"]
                })
            df = pd.DataFrame(rows)
            df.to_excel("results.xlsx", index=False)
            st.success("Exported to results.xlsx")

    st.subheader("📊 Live Leaderboard")

    rows = []
    for name, t in st.session_state.market["traders"].items():
        total = t["cash"]
        for a in t["positions"]:
            total += t["positions"][a] * st.session_state.market["assets"][a]["price"]
        rows.append({"Trader": name, "Net Worth": round(total, 2)})

    df = pd.DataFrame(rows).sort_values("Net Worth", ascending=False)
    st.dataframe(df, use_container_width=True)

# =========================================================
# TRADER PANEL
# =========================================================
else:
    st.title(f"📱 Trader Terminal — {st.session_state.user}")

    trader = st.session_state.market["traders"][st.session_state.user]

    col1, col2, col3 = st.columns(3)
    col1.metric("Cash", f"₹ {trader['cash']:.2f}")
    col2.metric("ABC Position", trader["positions"]["ABC"])
    col3.metric("XYZ Position", trader["positions"]["XYZ"])

    st.subheader("📈 Market Prices")

    for a, info in st.session_state.market["assets"].items():
        st.metric(a, f"₹ {info['price']:.2f}", "HALTED" if info["halted"] else "LIVE")

    st.subheader("📝 Place Order")

    asset = st.selectbox("Asset", list(st.session_state.market["assets"].keys()))
    side = st.selectbox("Side", ["buy", "sell"])
    order_type = st.selectbox("Order Type", ["market", "limit"])
    qty = st.number_input("Quantity", 1, 1000, 1)

    if order_type == "limit":
        price = st.number_input("Limit Price", 1.0, 100000.0, st.session_state.market["assets"][asset]["price"])
    else:
        price = st.session_state.market["assets"][asset]["price"]

    if st.button("Submit Order"):
        if not st.session_state.market["assets"][asset]["halted"]:
            place_order(st.session_state.user, asset, side, qty, price, order_type)
            match_orders(asset)
            st.success("Order sent!")
        else:
            st.error("Trading halted in this asset!")

    # -----------------------------
    # ORDER BOOK VIEW
    # -----------------------------
    st.subheader("📚 Order Book")

    book = st.session_state.market["order_books"][asset]

    colb, cols = st.columns(2)
    colb.write("### BUY")
    if book["buy"]:
        colb.dataframe(pd.DataFrame(book["buy"]))
    else:
        colb.write("Empty")

    cols.write("### SELL")
    if book["sell"]:
        cols.dataframe(pd.DataFrame(book["sell"]))
    else:
        cols.write("Empty")

# =========================================================
# FOOTER
# =========================================================
st.caption("🎓 Classroom Trading Lab — Human vs Algo vs AI | Prof. Shalini Velappan")
