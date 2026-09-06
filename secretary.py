"""API integration and strict response validation."""
import json
import re
from log.custom_logger import log
import util

try:
    from google import genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def _extract_json(text):
    if not isinstance(text, str):
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def run_api(model, prompt, temperature=0.2):
    model = str(model).strip()

    if model.lower() in {"demo", "dry-run", "dryrun"}:
        return '{"action_type":"no"}'

    if model.lower().startswith("gemini"):
        if not util.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is not configured. Add it to your local .env/settings.py "
                "or use --model demo."
            )
        if genai is None:
            raise ImportError("Install the Gemini SDK with: pip install google-genai")
        client = genai.Client(api_key=util.GOOGLE_API_KEY)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"temperature": temperature},
        )
        return response.text or ""

    if model.lower().startswith("gpt"):
        if not util.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured.")
        if OpenAI is None:
            raise ImportError("Install the OpenAI SDK with: pip install openai")
        client = OpenAI(api_key=util.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    raise ValueError(f"Unsupported model: {model}")


class Secretary:
    def __init__(self, model):
        self.model = model

    def get_response(self, prompt, temperature=0.2):
        return run_api(self.model, prompt, temperature)

    def check_loan(self, resp, max_loan):
        data = _extract_json(resp)
        if not isinstance(data, dict) or "loan" not in data:
            return False, "Return exactly one JSON object containing the 'loan' key.", None
        loan = str(data["loan"]).lower()
        if loan == "no":
            return True, "", {"loan": "no"}
        if loan != "yes":
            return False, "The 'loan' value must be yes or no.", None
        if data.get("loan_type") not in (0, 1, 2):
            return False, "loan_type must be 0, 1, or 2.", None
        try:
            amount = float(data["amount"])
        except (KeyError, TypeError, ValueError):
            return False, "amount must be a positive number.", None
        if amount <= 0 or amount > max_loan:
            return False, f"amount must be between 0 and {max_loan:.2f}.", None
        return True, "", {
            "loan": "yes",
            "loan_type": int(data["loan_type"]),
            "amount": round(amount, 2),
        }

    def check_action(self, resp, cash, stock_a_amount, stock_b_amount, stock_a_price, stock_b_price):
        data = _extract_json(resp)
        if not isinstance(data, dict) or "action_type" not in data:
            return False, "Return exactly one JSON object containing action_type.", None

        action_type = str(data["action_type"]).lower()
        if action_type == "no":
            return True, "", {"action_type": "no"}
        if action_type not in {"buy", "sell"}:
            return False, "action_type must be buy, sell, or no.", None

        stock = data.get("stock")
        if stock not in {"A", "B"}:
            return False, "stock must be A or B.", None

        try:
            amount = int(data["amount"])
            price = float(data["price"])
        except (KeyError, TypeError, ValueError):
            return False, "amount must be an integer and price must be a number.", None

        if amount <= 0 or price <= 0:
            return False, "amount and price must be positive.", None

        if action_type == "buy" and amount * price > cash + 1e-9:
            return False, f"Buy value cannot exceed available cash ({cash:.2f}).", None

        holdings = {"A": stock_a_amount, "B": stock_b_amount}
        if action_type == "sell" and amount > holdings[stock]:
            return False, f"You only hold {holdings[stock]} shares of {stock}.", None

        return True, "", {
            "action_type": action_type,
            "stock": stock,
            "amount": amount,
            "price": round(price, 4),
        }

    def check_estimate(self, resp):
        data = _extract_json(resp)
        keys = {"buy_A", "buy_B", "sell_A", "sell_B", "loan"}
        if not isinstance(data, dict) or set(data) != keys:
            return False, "Return exactly buy_A, buy_B, sell_A, sell_B and loan.", None
        if any(data[k] not in {"yes", "no"} for k in keys):
            return False, "Every estimate value must be yes or no.", None
        return True, "", data
