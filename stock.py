"""Stock model for the simulated market."""
class Stock:
    def __init__(self, name, initial_price, initial_stock=0, is_new=False):
        self.name = name
        self.price = float(initial_price)
        self.initial_stock = initial_stock
        self.is_new = is_new
        self.history = {}
        self.session_deal = []

    def add_session_deal(self, price_and_amount):
        self.session_deal.append(price_and_amount)

    def update_price(self, date):
        if self.session_deal:
            self.price = float(self.session_deal[-1]["price"])
            self.history[date] = list(self.session_deal)
        self.session_deal.clear()

    def get_price(self):
        return self.price

    def gen_financial_report(self, index):
        import util
        reports = {"A": util.FINANCIAL_REPORT_A, "B": util.FINANCIAL_REPORT_B}
        return reports[self.name][index % len(reports[self.name])]
