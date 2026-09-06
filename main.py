"""Command-line entry point for the Stockagent simulation."""
import argparse
import json
import os
import random

import util
from agent import Agent
from secretary import Secretary
from stock import Stock
from log.custom_logger import log
from record import (
    create_agent_daily_record,
    create_agent_session_record,
    create_stock_record,
    create_trade_record,
)


def get_agent(agents, order):
    return next((agent for agent in agents if agent.order == order), None)


def handle_action(action, order_book, agents, stock, session, date):
    """Match an incoming order against opposite orders at the same price."""
    if action.get("action_type") not in {"buy", "sell"}:
        return

    remaining = int(action["amount"])
    side = action["action_type"]
    opposite = "sell" if side == "buy" else "buy"
    matches = order_book[opposite][:]

    for resting in matches:
        if remaining <= 0:
            break
        if resting["price"] != action["price"]:
            continue

        buyer_id = action["agent"] if side == "buy" else resting["agent"]
        seller_id = resting["agent"] if side == "buy" else action["agent"]
        buyer = get_agent(agents, buyer_id)
        seller = get_agent(agents, seller_id)
        if buyer is None or seller is None:
            continue

        quantity = min(remaining, int(resting["amount"]))

        # Validate again at execution time because an agent may have placed
        # multiple orders in the same session.
        if buyer.cash < quantity * action["price"] or (
            stock.name == "A" and seller.stock_a_amount < quantity
        ) or (
            stock.name == "B" and seller.stock_b_amount < quantity
        ):
            continue

        if not buyer.buy_stock(stock.name, quantity, action["price"]):
            continue
        if not seller.sell_stock(stock.name, quantity, action["price"]):
            # Roll back the buyer if the seller unexpectedly failed.
            buyer.sell_stock(stock.name, quantity, action["price"])
            continue

        stock.add_session_deal({"price": action["price"], "amount": quantity})
        create_trade_record(
            date, session, stock.name, buyer_id, seller_id, quantity, action["price"]
        )

        remaining -= quantity
        resting["amount"] -= quantity
        if resting["amount"] <= 0:
            order_book[opposite].remove(resting)

        log.logger.info(
            "TRADE day=%s session=%s stock=%s buyer=%s seller=%s qty=%s price=%s",
            date, session, stock.name, buyer_id, seller_id, quantity, action["price"],
        )

    if remaining > 0:
        pending = dict(action)
        pending["amount"] = remaining
        order_book[side].append(pending)


def simulation(model, agents_count, days, sessions, seed):
    rng = random.Random(seed)
    util.reset_rates()

    stock_a = Stock("A", util.STOCK_A_INITIAL_PRICE)
    stock_b = Stock("B", util.STOCK_B_INITIAL_PRICE)

    secretary = Secretary(model)
    agents = [
        Agent(i, stock_a.get_price(), stock_b.get_price(), secretary, model, rng)
        for i in range(agents_count)
    ]

    forum = []
    total_trades = 0
    order_books = {
        "A": {"buy": [], "sell": []},
        "B": {"buy": [], "sell": []},
    }

    log.logger.info(
        "Simulation started: model=%s agents=%s days=%s sessions=%s seed=%s",
        model, agents_count, days, sessions, seed,
    )

    for date in range(1, days + 1):
        for book in order_books.values():
            book["buy"].clear()
            book["sell"].clear()

        for agent in agents[:]:
            agent.loan_repayment(date)

        if date in util.REPAYMENT_DAYS:
            for agent in agents[:]:
                agent.interest_payment()

        for agent in agents[:]:
            if agent.is_bankrupt and agent.bankrupt_process(
                stock_a.get_price(), stock_b.get_price()
            ):
                agent.quit = True
                agents.remove(agent)
                log.logger.warning("Agent %s removed after bankruptcy.", agent.order)

        if date == util.EVENT_1_DAY:
            util.LOAN_RATE = util.EVENT_1_LOAN_RATE
            forum.append({"name": "MARKET", "message": util.EVENT_1_MESSAGE})

        if date == util.EVENT_2_DAY:
            util.LOAN_RATE = util.EVENT_2_LOAN_RATE
            forum.append({"name": "MARKET", "message": util.EVENT_2_MESSAGE})

        daily_loans = {}
        for agent in agents:
            daily_loans[agent.order] = agent.plan_loan(
                date, stock_a.get_price(), stock_b.get_price(), forum
            )

        for session in range(1, sessions + 1):
            sequence = agents[:]
            rng.shuffle(sequence)

            for agent in sequence:
                action = agent.plan_stock(
                    date, session, stock_a, stock_b,
                    order_books["A"], order_books["B"],
                )

                equity, cash, a_value, b_value = agent.get_proper_cash_value(
                    stock_a.get_price(), stock_b.get_price()
                )
                create_agent_session_record(
                    agent.order, date, session, equity, cash, a_value, b_value, action
                )

                if action.get("action_type") in {"buy", "sell"}:
                    action = dict(action)
                    action["agent"] = agent.order
                    action["date"] = date
                    handle_action(
                        action, order_books[action["stock"]], agents,
                        stock_a if action["stock"] == "A" else stock_b,
                        session, date,
                    )

            stock_a.update_price(date)
            stock_b.update_price(date)
            create_stock_record(date, session, stock_a.get_price(), stock_b.get_price())

        for agent in agents:
            estimate = agent.next_day_estimate()
            create_agent_daily_record(
                agent.order, date, daily_loans.get(agent.order, {"loan": "no"}), estimate
            )

        for agent in agents:
            message = agent.post_message()
            forum.append({"name": agent.order, "message": message})

        # Keep only recent public messages to avoid unbounded prompt growth.
        forum = forum[-agents_count - 5:]

    portfolios = []
    for agent in agents:
        equity, cash, a_value, b_value = agent.get_proper_cash_value(
            stock_a.get_price(), stock_b.get_price()
        )
        portfolios.append({
            "agent": agent.order,
            "personality": agent.character,
            "cash": round(cash, 2),
            "stock_A_value": round(a_value, 2),
            "stock_B_value": round(b_value, 2),
            "equity": round(equity, 2),
        })

    os.makedirs("res", exist_ok=True)
    summary = {
        "model": model,
        "agents": agents_count,
        "days": days,
        "sessions_per_day": sessions,
        "seed": seed,
        "final_prices": {"A": stock_a.get_price(), "B": stock_b.get_price()},
        "active_agents": len(agents),
        "portfolios": portfolios,
    }
    with open("res/summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    log.logger.info("Simulation finished. Results saved in res/.")
    return summary


def main():
    parser = argparse.ArgumentParser(description="AI-powered educational stock market simulation")
    parser.add_argument("--model", default=util.DEFAULT_MODEL,
                        help="Gemini model name, or 'demo' for an offline run")
    parser.add_argument("--agents", type=int, default=util.AGENTS_NUM)
    parser.add_argument("--days", type=int, default=util.TOTAL_DATE)
    parser.add_argument("--sessions", type=int, default=util.TOTAL_SESSION)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.agents < 1 or args.days < 1 or args.sessions < 1:
        parser.error("--agents, --days and --sessions must be positive integers")

    summary = simulation(args.model, args.agents, args.days, args.sessions, args.seed)
    print("\nSimulation complete.")
    print(f"Model: {summary['model']}")
    print(f"Agents: {summary['agents']} | Days: {summary['days']} | Sessions/day: {summary['sessions_per_day']}")
    print(f"Final prices: A=${summary['final_prices']['A']:.2f}, B=${summary['final_prices']['B']:.2f}")
    print("Results: res/summary.json, res/trades.csv, res/stocks.csv, res/agent_sessions.csv, res/agent_daily.csv")


if __name__ == "__main__":
    main()
