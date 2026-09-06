"""CSV-based simulation records. CSV keeps the project lightweight and portable."""
import csv
import os

RES_DIR = "res"


def _append(filename, header, row):
    os.makedirs(RES_DIR, exist_ok=True)
    path = os.path.join(RES_DIR, filename)
    exists = os.path.isfile(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(header)
        writer.writerow(row)


def create_trade_record(date, session, stock, buyer, seller, amount, price):
    _append(
        "trades.csv",
        ["day", "session", "stock", "buyer", "seller", "quantity", "price"],
        [date, session, stock, buyer, seller, amount, price],
    )


def create_stock_record(date, session, stock_a_price, stock_b_price):
    _append(
        "stocks.csv",
        ["day", "session", "stock_A_price", "stock_B_price"],
        [date, session, stock_a_price, stock_b_price],
    )


def create_agent_session_record(agent, date, session, equity, cash, stock_a_value, stock_b_value, action):
    _append(
        "agent_sessions.csv",
        ["agent", "day", "session", "equity", "cash", "stock_A_value", "stock_B_value",
         "action_type", "stock", "quantity", "price"],
        [
            agent, date, session, equity, cash, stock_a_value, stock_b_value,
            action.get("action_type", "no"), action.get("stock", "-"),
            action.get("amount", 0), action.get("price", 0),
        ],
    )


def create_agent_daily_record(agent, date, loan, estimate):
    _append(
        "agent_daily.csv",
        ["agent", "day", "loan", "loan_type", "loan_amount",
         "tomorrow_buy_A", "tomorrow_buy_B", "tomorrow_sell_A", "tomorrow_sell_B",
         "tomorrow_loan"],
        [
            agent, date, loan.get("loan"), loan.get("loan_type", ""),
            loan.get("amount", 0), estimate.get("buy_A", "no"),
            estimate.get("buy_B", "no"), estimate.get("sell_A", "no"),
            estimate.get("sell_B", "no"), estimate.get("loan", "no"),
        ],
    )
