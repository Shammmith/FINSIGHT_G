# PDF/CSV extraction
# core_api/app/services/parser.py
import io
import pandas as pd
import pdfplumber
from app.services.pii_scrubber import normalize_description

def parse_csv(file_bytes: bytes) -> list[dict]:
    df = pd.read_csv(io.BytesIO(file_bytes))
    df.columns = [c.strip().lower() for c in df.columns]
    # Expect columns: date, description, amount, type — adjust mapping per bank format
    records = []
    for _, row in df.iterrows():
        records.append({
            "txn_date": pd.to_datetime(row.get("date")).date(),
            "cleaned_description": normalize_description(str(row.get("description", ""))),
            "raw_description": str(row.get("description", "")),
            "amount": float(row.get("amount", 0)),
            "txn_type": "credit" if float(row.get("amount", 0)) >= 0 else "debit",
        })
    return records

def parse_pdf(file_bytes: bytes) -> list[dict]:
    records = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table[1:]:  # skip header row
                    if not row or len(row) < 3:
                        continue
                    try:
                        records.append({
                            "txn_date": pd.to_datetime(row[0]).date(),
                            "cleaned_description": normalize_description(row[1] or ""),
                            "raw_description": row[1] or "",
                            "amount": float(str(row[2]).replace(",", "") or 0),
                            "txn_type": "debit" if "-" in str(row[2]) else "credit",
                        })
                    except (ValueError, IndexError):
                        continue  # skip malformed rows, don't fail whole parse
    return records