# ml_engine/tests/fixtures/sample_transactions.py

SAMPLE_DESCRIPTIONS = [
    # Cluster A: Coffee/Cafe — deliberately inconsistent naming
    "SBUX COFFEE #4521", "STARBUCKS STORE 1102", "Starbucks Coffee Co",
    "COSTA COFFEE LTD", "Blue Bottle Coffee", "CAFE NERO 0091",

    # Cluster B: Ride-hailing / Transport
    "UBER TRIP HELP.UBER.COM", "UBER *EATS", "LYFT RIDE 8827",
    "OLA CABS PVT LTD", "RAPIDO BIKE TAXI",

    # Cluster C: Streaming/Subscriptions
    "NETFLIX.COM", "SPOTIFY PREMIUM", "AMAZON PRIME VIDEO",
    "DISNEY PLUS HOTSTAR", "YOUTUBE PREMIUM",

    # Cluster D: Groceries
    "WALMART SUPERCENTER", "WHOLE FOODS MKT", "TRADER JOE'S #412",
    "BIGBASKET ONLINE", "RELIANCE FRESH STORE",

    # Cluster E: Income (salary/credits) — tests income vs expense split
    "SALARY CREDIT ACME CORP", "PAYROLL DEPOSIT XYZ INC", "FREELANCE PAYMENT RECEIVED",

    # Noise / ambiguous — tests robustness
    "MISC PAYMENT REF#88213", "ATM WITHDRAWAL", "BANK FEE CHARGE",
]

# Ground-truth expectation: descriptions from the SAME lettered group
# should land in the SAME cluster, even with zero shared keywords
# (e.g., "SBUX" vs "Starbucks Coffee Co" vs "Costa Coffee Ltd")
EXPECTED_GROUPS = {
    "coffee": ["SBUX COFFEE #4521", "STARBUCKS STORE 1102", "Starbucks Coffee Co",
               "COSTA COFFEE LTD", "Blue Bottle Coffee", "CAFE NERO 0091"],
    "transport": ["UBER TRIP HELP.UBER.COM", "UBER *EATS", "LYFT RIDE 8827",
                  "OLA CABS PVT LTD", "RAPIDO BIKE TAXI"],
    "subscriptions": ["NETFLIX.COM", "SPOTIFY PREMIUM", "AMAZON PRIME VIDEO",
                       "DISNEY PLUS HOTSTAR", "YOUTUBE PREMIUM"],
    "groceries": ["WALMART SUPERCENTER", "WHOLE FOODS MKT", "TRADER JOE'S #412",
                  "BIGBASKET ONLINE", "RELIANCE FRESH STORE"],
    "income": ["SALARY CREDIT ACME CORP", "PAYROLL DEPOSIT XYZ INC", "FREELANCE PAYMENT RECEIVED"],
}