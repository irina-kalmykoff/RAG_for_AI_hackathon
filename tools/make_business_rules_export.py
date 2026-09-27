"""Level-2 test file: clean-looking 2025 export whose traps need business knowledge.

  - Webshop rows: amounts INCLUDE 21% VAT, though the column is called "Net amount" (ERP rows exclude VAT)
  - "Marlow & Finch Retail BV" is the company's own subsidiary (intercompany sales, eliminated at group level)
  - orders have several lines (one row per product), so rows are not orders
Writes data/sales-2025-export-v2.csv and prints the correct and likely wrong answers.
"""
import csv, random, calendar
from collections import defaultdict
from pathlib import Path

random.seed(4242)
OUT = Path(__file__).resolve().parent.parent / "data" / "sales-2025-export-v2.csv"
VAT = 1.21

towns = ["Gent", "Antwerpen", "Leuven", "Brugge", "Mechelen", "Hasselt", "Kortrijk", "Brussel", "Namur", "Liège", "Charleroi", "Mons"]
kinds = ["Hotel", "Café", "Brasserie", "Bistro", "Kantoorcentrum", "Restaurant", "Bakkerij", "Koffiebar"]
customers = [(f"C-{1100 + i}", f"{k} {t}") for i, (k, t) in enumerate((k, t) for k in kinds for t in towns)]
IC = ("C-0001", "Marlow & Finch Retail BV")
products = {"Espresso beans 1kg": 24.90, "Filter coffee 1kg": 19.50, "Capsules box 100": 38.00,
            "Decaf beans 1kg": 26.40, "Descaler pack": 12.90, "Milk frother jug": 17.50}
season = {1: .85, 2: .80, 3: .90, 4: .90, 5: .95, 6: .90, 7: .80, 8: .75, 9: .95, 10: 1.05, 11: 1.00, 12: 1.25}

rows = []            # [order, line, date, cid, cname, product, qty, unit, amount, source, net_value, kind]
def add_order(oid, date, cid, cname, source, qty_range, n_lines):
    for ln, p in enumerate(random.sample(list(products), n_lines), 1):
        qty = random.randint(*qty_range)
        unit = products[p] * (VAT if source == "Webshop" else 1)
        amt = round(qty * round(unit, 2), 2)
        net = amt / VAT if source == "Webshop" else amt
        kind = "ic" if cid == IC[0] else "ext"
        rows.append([oid, ln, date, cid, cname, p, qty, round(unit, 2), amt, source, net, kind])

o = 500001
for m in range(1, 13):
    days = calendar.monthrange(2025, m)[1]
    for _ in range(int(1500 * season[m])):                     # external ERP orders
        cid, cname = random.choice(customers)
        add_order(f"SO-{o}", f"2025-{m:02d}-{random.randint(1, days):02d}", cid, cname, "ERP", (4, 30), random.randint(2, 5)); o += 1
    for _ in range(int(700 * season[m])):                      # webshop orders (gross)
        add_order(f"WS-{o}", f"2025-{m:02d}-{random.randint(1, days):02d}", "C-WEB", "Webshop customer", "Webshop", (5, 25), random.randint(1, 3)); o += 1
    for _ in range(12):                                         # intercompany: large weekly-ish replenishments
        add_order(f"SO-{o}", f"2025-{m:02d}-{random.randint(1, days):02d}", IC[0], IC[1], "ERP", (180, 320), 5); o += 1

rows.sort(key=lambda r: (r[2], r[0], r[1]))
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Order ID", "Order date", "Customer ID", "Customer", "Product", "Qty", "Unit price (EUR)", "Net amount (EUR)", "Source system"])
    for r in rows:
        w.writerow([r[0], r[2], r[3], r[4], r[5], r[6], f"{r[7]:.2f}", f"{r[8]:.2f}", r[9]])

fmt = lambda v: f"€{v:,.0f}"
ext = [r for r in rows if r[11] == "ext"]
group_rev = sum(r[10] for r in ext)
naive_rev = sum(r[8] for r in rows)
by_c = defaultdict(float); by_c_naive = defaultdict(float)
for r in ext: by_c[r[4]] += r[10]
for r in rows: by_c_naive[r[4]] += r[8]
orders_ext = {r[0] for r in ext}
print(f"rows {len(rows):,} | orders {len({r[0] for r in rows}):,} | file {OUT.stat().st_size/1e6:.1f} MB")
print("CORRECT group revenue (external, excl. VAT):", fmt(group_rev))
print("  naive sum of column:", fmt(naive_rev), "| VAT in webshop:", fmt(sum(r[8] - r[10] for r in rows if r[9] == 'Webshop')), "| intercompany:", fmt(sum(r[8] for r in rows if r[11] == 'ic')))
print("  only VAT fixed (IC kept):", fmt(naive_rev - sum(r[8] - r[10] for r in rows if r[9] == 'Webshop')), "| only IC removed (VAT kept):", fmt(naive_rev - sum(r[8] for r in rows if r[11] == 'ic')))
print("CORRECT top 5 external customers:", [(c, fmt(v)) for c, v in sorted(by_c.items(), key=lambda t: -t[1])[:5]])
print("  naive top 5:", [(c, fmt(v)) for c, v in sorted(by_c_naive.items(), key=lambda t: -t[1])[:5]])
print("CORRECT average order value (external, excl. VAT, per order):", f"€{group_rev/len(orders_ext):,.2f}", f"over {len(orders_ext):,} orders")
print("  naive AOV per row (all rows, column sum):", f"€{naive_rev/len(rows):,.2f}", "| naive per order (all, column sum):", f"€{naive_rev/len({r[0] for r in rows}):,.2f}",
      "| per row external net:", f"€{group_rev/len(ext):,.2f}")
