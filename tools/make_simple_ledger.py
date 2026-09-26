"""Generate a small, tidy-looking Q1 sales file with two hidden traps: duplicate rows and cancelled invoices."""
import csv, random
from collections import defaultdict
from pathlib import Path

random.seed(7)
OUT = Path(__file__).resolve().parent.parent / "data" / "sales-q1-2025.csv"

customers = {  # typical invoice size (EUR); ~2 invoices per month each
    "Grand Hotel Scheldezicht": 9800, "Kantoorpark Zuid NV": 7400, "Hotel Ter Aa": 6900,
    "Brasserie De Klok": 4200, "Hotel Aurelia": 5100, "Co-work Dok": 2600,
}
rows, n = [], 1001
for m in (1, 2, 3):
    for c, base in customers.items():
        for d in random.sample(range(2, 28), 2):
            rows.append({"no": f"INV-{n}", "date": f"2025-{m:02d}-{d:02d}", "customer": c,
                         "amount": round(base * random.uniform(0.85, 1.15), 2), "status": "Paid"})
            n += 1
rows.sort(key=lambda r: r["date"])
for i, r in enumerate(rows):  # renumber in date order so duplicates stand out only if you look
    r["no"] = f"INV-{1001 + i}"

# Trap 2: three large Hotel Ter Aa invoices were cancelled (order rebooked), still in the export
ter_aa = [r for r in rows if r["customer"] == "Hotel Ter Aa"]
cancelled = []
for r in ter_aa[1::2][:3]:
    r["status"] = "Cancelled"
    cancelled.append(r)
# a few open invoices so Status looks like a normal column
for r in random.sample([r for r in rows if r["status"] == "Paid"], 5):
    r["status"] = "Open"

truth = defaultdict(float)
for r in rows:
    if r["status"] != "Cancelled":
        truth[r["customer"]] += r["amount"]

# Trap 1: five Kantoorpark invoices exported twice, appended at the end as from a second export
kp_dup = {r["no"] for r in [r for r in rows if r["customer"] == "Kantoorpark Zuid NV"][:5]}
dirty = rows + [dict(r) for r in rows if r["no"] in kp_dup]

with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Invoice no", "Date", "Customer", "Amount (EUR)", "Status"])
    for r in dirty:
        w.writerow([r["no"], r["date"], r["customer"], f"{r['amount']:.2f}", r["status"]])

naive = defaultdict(float)
for r in dirty:
    naive[r["customer"]] += r["amount"]
fmt = lambda v: f"€{v:,.0f}"
print("rows:", len(dirty))
print("TRUE total", fmt(sum(truth.values())), "| ranking:", [(c, fmt(v)) for c, v in sorted(truth.items(), key=lambda t: -t[1])[:3]])
print("NAIVE total", fmt(sum(naive.values())), "| ranking:", [(c, fmt(v)) for c, v in sorted(naive.items(), key=lambda t: -t[1])[:3]])
print("duplicate value", fmt(sum(r["amount"] for r in rows if r["no"] in kp_dup)), "| cancelled value", fmt(sum(r["amount"] for r in cancelled)))
