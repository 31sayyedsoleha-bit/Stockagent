"""Autonomous trader for the Stockagent educational simulation."""
import random
import time
import util
from log.custom_logger import log
from prompt.agent_prompt import (
    BACKGROUND, LOAN_PROMPT, ACTION_PROMPT, RETRY_ACTION,
    FORUM_PROMPT, ESTIMATE_PROMPT,
)


class Agent:
    PERSONALITIES = ["Conservative", "Aggressive", "Balanced", "Growth-Oriented"]

    def __init__(self, i, stock_a_price, stock_b_price, secretary, model, rng=None):
        self.order = i
        self.secretary = secretary
        self.model = model
        self.rng = rng or random.Random()
        self.character = self.rng.choice(self.PERSONALITIES)
        self.stock_a_amount, self.stock_b_amount, self.cash, init_debt = util.random_init(
            stock_a_price, stock_b_price, self.rng
        )
        self.init_proper = self.get_total_proper(stock_a_price, stock_b_price)
        self.loans = [init_debt]
        self.is_bankrupt = False
        self.quit = False
        self.chat_history = []

    def _is_demo(self):
        return self.model.lower() in {"demo", "dry-run", "dryrun"}

    def _ask(self, prompt, temperature=0.2):
        return self.secretary.get_response(prompt, temperature)

    def get_total_loan(self):
        return sum(float(loan["amount"]) for loan in self.loans)

    def get_total_proper(self, stock_a_price, stock_b_price):
        return (
            self.cash
            + self.stock_a_amount * stock_a_price
            + self.stock_b_amount * stock_b_price
        )

    def get_proper_cash_value(self, stock_a_price, stock_b_price):
        a_value = self.stock_a_amount * stock_a_price
        b_value = self.stock_b_amount * stock_b_price
        return self.cash + a_value + b_value, self.cash, a_value, b_value

    def _demo_loan(self, max_loan):
        if max_loan <= 0 or self.rng.random() < 0.75:
            return {"loan": "no"}
        amount = round(min(max_loan, max(1000, self.cash * 0.1)), 2)
        return {"loan": "yes", "loan_type": 0, "amount": amount}

    def plan_loan(self, date, stock_a_price, stock_b_price, lastday_forum_message):
        if self.quit:
            return {"loan": "no"}

        max_loan = max(0.0, self.init_proper - self.get_total_loan())
        if max_loan <= 0:
            return {"loan": "no"}

        if self._is_demo():
            loan = self._demo_loan(max_loan)
        else:
            prompt = LOAN_PROMPT.format(
                background=BACKGROUND,
                date=date,
                character=self.character,
                stock_a=self.stock_a_amount,
                stock_b=self.stock_b_amount,
                cash=self.cash,
                debt=self.loans,
                max_loan=max_loan,
                rate1=util.LOAN_RATE[0],
                rate2=util.LOAN_RATE[1],
                rate3=util.LOAN_RATE[2],
            )
            response = self._ask(prompt)
            ok, reason, loan = self.secretary.check_loan(response, max_loan)
            retries = 0
            while not ok and retries < 2:
                retries += 1
                response = self._ask(
                    f"Previous response failed validation: {reason}\n"
                    '{"loan":"no"} or {"loan":"yes","loan_type":0,"amount":1000}'
                )
                ok, reason, loan = self.secretary.check_loan(response, max_loan)
            if not ok:
                loan = {"loan": "no"}

        if loan["loan"] == "yes":
            loan["repayment_date"] = date + util.LOAN_TYPE_DATE[loan["loan_type"]]
            self.loans.append(loan)
            self.cash += loan["amount"]
        return loan

    def _demo_action(self, stock_a, stock_b):
        choices = []
        if self.cash >= stock_a.get_price():
            choices.append(("A", stock_a.get_price()))
        if self.cash >= stock_b.get_price():
            choices.append(("B", stock_b.get_price()))
        if self.stock_a_amount > 0:
            choices.append(("A", stock_a.get_price()))
        if self.stock_b_amount > 0:
            choices.append(("B", stock_b.get_price()))

        if not choices or self.rng.random() < 0.35:
            return {"action_type": "no"}

        stock, price = self.rng.choice(choices)
        if self.rng.random() < 0.5 and self.cash >= price:
            amount = max(1, min(10, int(self.cash // price)))
            return {"action_type": "buy", "stock": stock, "amount": amount, "price": round(price, 2)}

        holding = self.stock_a_amount if stock == "A" else self.stock_b_amount
        if holding > 0:
            amount = self.rng.randint(1, min(10, int(holding)))
            return {"action_type": "sell", "stock": stock, "amount": amount, "price": round(price, 2)}
        return {"action_type": "no"}

    def plan_stock(self, date, session, stock_a, stock_b, stock_a_deals, stock_b_deals):
        if self.quit:
            return {"action_type": "no"}

        if self._is_demo():
            return self._demo_action(stock_a, stock_b)

        prompt = ACTION_PROMPT.format(
            background=BACKGROUND,
            date=date,
            session=session,
            character=self.character,
            a_price=stock_a.get_price(),
            b_price=stock_b.get_price(),
            a_orders=stock_a_deals,
            b_orders=stock_b_deals,
            stock_a=self.stock_a_amount,
            stock_b=self.stock_b_amount,
            cash=self.cash,
        )
        response = self._ask(prompt)
        ok, reason, action = self.secretary.check_action(
            response, self.cash, self.stock_a_amount, self.stock_b_amount,
            stock_a.get_price(), stock_b.get_price()
        )
        retries = 0
        while not ok and retries < 2:
            retries += 1
            response = self._ask(RETRY_ACTION.format(fail_response=reason))
            ok, reason, action = self.secretary.check_action(
                response, self.cash, self.stock_a_amount, self.stock_b_amount,
                stock_a.get_price(), stock_b.get_price()
            )
        return action if ok else {"action_type": "no"}

    def buy_stock(self, stock_name, amount, price):
        if self.quit or amount <= 0 or self.cash < amount * price:
            return False
        self.cash -= amount * price
        if stock_name == "A":
            self.stock_a_amount += amount
        elif stock_name == "B":
            self.stock_b_amount += amount
        else:
            return False
        return True

    def sell_stock(self, stock_name, amount, price):
        if self.quit or amount <= 0:
            return False
        if stock_name == "A":
            if self.stock_a_amount < amount:
                return False
            self.stock_a_amount -= amount
        elif stock_name == "B":
            if self.stock_b_amount < amount:
                return False
            self.stock_b_amount -= amount
        else:
            return False
        self.cash += amount * price
        return True

    def loan_repayment(self, date):
        if self.quit:
            return
        for loan in self.loans[:]:
            if loan["repayment_date"] == date:
                self.cash -= loan["amount"] * (1 + util.LOAN_RATE[loan["loan_type"]])
                self.loans.remove(loan)
        self.is_bankrupt = self.cash < 0

    def interest_payment(self):
        if self.quit:
            return
        for loan in self.loans:
            self.cash -= loan["amount"] * util.LOAN_RATE[loan["loan_type"]] / 12
        self.is_bankrupt = self.cash < 0

    def bankrupt_process(self, stock_a_price, stock_b_price):
        if self.cash >= 0:
            self.is_bankrupt = False
            return False

        for name, price in [("A", stock_a_price), ("B", stock_b_price)]:
            holding = self.stock_a_amount if name == "A" else self.stock_b_amount
            if holding <= 0:
                continue
            needed = -self.cash
            sell_amount = min(holding, int((needed + price - 1e-9) // price))
            if sell_amount > 0:
                self.sell_stock(name, sell_amount, price)
            if self.cash >= 0:
                self.is_bankrupt = False
                return False

        self.is_bankrupt = self.cash < 0
        return self.is_bankrupt

    def post_message(self):
        if self.quit:
            return ""
        if self._is_demo():
            return f"{self.character} trader observed today's simulated market activity."
        try:
            return self._ask(FORUM_PROMPT, temperature=0.5).strip()
        except Exception as exc:
            log.logger.warning("Forum API error: %s", exc)
            return "No forum message generated."

    def next_day_estimate(self):
        default = {"buy_A": "no", "buy_B": "no", "sell_A": "no", "sell_B": "no", "loan": "no"}
        if self.quit or self._is_demo():
            return default
        try:
            response = self._ask(ESTIMATE_PROMPT)
            ok, _, estimate = self.secretary.check_estimate(response)
            return estimate if ok else default
        except Exception as exc:
            log.logger.warning("Estimate API error: %s", exc)
            return default
