"""Prompts used by the two-stock Stockagent simulation."""

BACKGROUND = """You are an autonomous trader in an educational simulated stock market.
The market contains two simulated companies: A and B.
Company A is an established chemical-industry company.
Company B is a younger technology company with higher recent growth.
Your decisions affect only the simulated market."""

LOAN_PROMPT = """{background}

It is simulation day {date}. Your personality is {character}.
You hold {stock_a} shares of A and {stock_b} shares of B.
Cash: {cash:.2f}
Current loans: {debt}
Maximum additional loan: {max_loan:.2f}

Available loan types:
0 = 1 month at {rate1}
1 = 2 months at {rate2}
2 = 3 months at {rate3}

Return ONLY one JSON object.
If you do not need a loan:
{{"loan":"no"}}
Otherwise:
{{"loan":"yes","loan_type":0,"amount":1000}}
"""

ACTION_PROMPT = """{background}

Simulation day {date}, trading session {session}.
Your personality is {character}.
Company A price: {a_price:.2f}
Company B price: {b_price:.2f}

Current A orders:
{a_orders}
Current B orders:
{b_orders}

Your holdings:
A: {stock_a} shares
B: {stock_b} shares
Cash: {cash:.2f}

Choose one action. The amount must be a positive integer and the price must be positive.
Return ONLY valid JSON.

Buy example:
{{"action_type":"buy","stock":"A","amount":10,"price":30.0}}

Sell example:
{{"action_type":"sell","stock":"B","amount":5,"price":18.0}}

If you do nothing:
{{"action_type":"no"}}
"""

RETRY_ACTION = """Your previous response failed validation for this reason:
{fail_response}

Return ONLY one valid JSON action using:
{{"action_type":"buy","stock":"A","amount":10,"price":30.0}}
or
{{"action_type":"sell","stock":"B","amount":5,"price":18.0}}
or
{{"action_type":"no"}}
"""

FORUM_PROMPT = """Write one short sentence for a public forum describing your simulated market observation today.
Do not give real-world financial advice. Return only the sentence."""

ESTIMATE_PROMPT = """Based on today's simulated market activity, return ONLY this JSON structure:
{{"buy_A":"yes","buy_B":"no","sell_A":"no","sell_B":"yes","loan":"no"}}
Each value must be exactly "yes" or "no"."""
