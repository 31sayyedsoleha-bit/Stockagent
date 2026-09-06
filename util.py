"""Configuration and helper utilities for the Stockagent simulation."""
import os
import random
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import settings as local_settings
except Exception:
    local_settings = None


def _get_setting(name, default=""):
    if local_settings and hasattr(local_settings, name):
        value = getattr(local_settings, name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return os.getenv(name, default)


GOOGLE_API_KEY = _get_setting("GOOGLE_API_KEY", "")
OPENAI_API_KEY = _get_setting("OPENAI_API_KEY", "")
DEFAULT_MODEL = _get_setting("DEFAULT_MODEL", "gemini-3.1-flash-lite")

# Small defaults make a first run affordable and quick. They can be overridden
# from the command line with --agents, --days and --sessions.
AGENTS_NUM = int(_get_setting("AGENTS_NUM", "6"))
TOTAL_DATE = int(_get_setting("TOTAL_DATE", "5"))
TOTAL_SESSION = int(_get_setting("TOTAL_SESSION", "2"))

STOCK_NAMES = ["A", "B"]
STOCK_INITIAL_PRICE = {"A": 30.0, "B": 18.0}
STOCK_A_INITIAL_PRICE = STOCK_INITIAL_PRICE["A"]
STOCK_B_INITIAL_PRICE = STOCK_INITIAL_PRICE["B"]

MIN_INITIAL_PROPERTY = 100_000.0
MAX_INITIAL_PROPERTY = 5_000_000.0

LOAN_TYPE = ["one-month", "two-month", "three-month"]
LOAN_TYPE_DATE = [22, 44, 66]
LOAN_RATE = [0.027, 0.030, 0.033]
REPAYMENT_DAYS = [22, 44, 66, 88, 110, 132]

EVENT_1_DAY = 3
EVENT_1_MESSAGE = (
    "The government has announced a reduction in the reserve requirement ratio. "
    "The lending interest rates have been lowered."
)
EVENT_1_LOAN_RATE = [0.024, 0.027, 0.030]

EVENT_2_DAY = 999999
EVENT_2_MESSAGE = ""
EVENT_2_LOAN_RATE = [0.0255, 0.0285, 0.0315]

SEASON_REPORT_DAYS = [1, 3, 5]

FINANCIAL_REPORT_A = [
    "Company A quarterly report: revenue growth 9.5%, revenue 4484 million, gross margin 41.1%, net profit 856.7 million, cash flow 756.8 million.",
    "Company A quarterly report: revenue growth 7.4%, revenue 4417.8 million, gross margin 35.7%, net profit 493.9 million, cash flow 396.5 million.",
    "Company A quarterly report: revenue growth 8.7%, revenue 4041.3 million, gross margin 37.5%, net profit 724.4 million, cash flow 639.5 million.",
    "Company A quarterly report: revenue growth 7.8%, revenue 5024.0 million, gross margin 42.5%, net profit 1031.2 million, cash flow 945.5 million.",
]

FINANCIAL_REPORT_B = [
    "Company B quarterly report: revenue growth 20.0%, revenue 1319.9 million, gross margin 31.2%, net profit 224.9 million, cash flow 208.7 million.",
    "Company B quarterly report: revenue growth 19.9%, revenue 1096.7 million, gross margin 31.3%, net profit 186.8 million, cash flow 181.7 million.",
    "Company B quarterly report: revenue growth 18.2%, revenue 1676.7 million, gross margin 31.6%, net profit 278.3 million, cash flow 266.1 million.",
    "Company B quarterly report: revenue growth 16.0%, revenue 1075.1 million, gross margin 32.4%, net profit 181.2 million, cash flow 161.2 million.",
]

def random_init(stock_a_initial, stock_b_initial, rng=None):
    rng = rng or random
    while True:
        stock_a = rng.randint(0, int(MAX_INITIAL_PROPERTY / stock_a_initial / 4))
        stock_b = rng.randint(0, int(MAX_INITIAL_PROPERTY / stock_b_initial / 4))
        cash = rng.uniform(MIN_INITIAL_PROPERTY, MAX_INITIAL_PROPERTY / 2)
        debt_amount = rng.uniform(0, MAX_INITIAL_PROPERTY / 5)
        equity = stock_a * stock_a_initial + stock_b * stock_b_initial + cash
        if MIN_INITIAL_PROPERTY <= equity <= MAX_INITIAL_PROPERTY and debt_amount <= equity:
            break
    debt = {
        "loan": "yes",
        "amount": round(debt_amount, 2),
        "loan_type": rng.randrange(len(LOAN_TYPE)),
        "repayment_date": LOAN_TYPE_DATE[0],
    }
    return stock_a, stock_b, cash, debt


def reset_rates():
    global LOAN_RATE
    LOAN_RATE = [0.027, 0.030, 0.033]
