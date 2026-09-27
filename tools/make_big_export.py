"""Build a ~200k-row 2025 sales export with problems hidden deep in the file.

Layout of data/sales-2025-export.csv:
  1. ERP orders Jan-Dec in date order, with a "TOTAL" subtotal row after each month
  2. a webshop export appended below it (Belgian number format as text, dd/mm/yyyy dates)
  3. ERP orders of 20-30 November appended again (Black Friday week exported twice)
True best month is December; counting the duplicate week makes November look best.
"""
import csv, random, calendar
from collections import defaultdict
from pathlib import Path

random.seed(2026)
OUT = Path(__file__).resolve().parent.parent / "data" / "sales-2025-export.csv"

towns = ["Gent", "Antwerpen", "Leuven", "Brugge", "Mechelen", "Hasselt", "Kortrijk", "Aalst", "Oostende", "Genk",
         "Brussel", "Elsene", "Ukkel", "Schaerbeek", "Namur", "Liège", "Charleroi", "Mons", "Wavre", "Arlon"]
region = {t: ("Brussels" if t in {"Brussel", "Elsene", "Ukkel", "Schaerbeek"} else
              "Wallonia" if t in {"Namur", "Liège", "Charleroi", "Mons", "Wavre", "Arlon"} else "Flanders") for t in towns}
kinds = ["Hotel", "Café", "Brasserie", "Bistro", "Kantoorcentrum", "Restaurant", "Bakkerij", "Tearoom", "Vergadercentrum", "Koffiebar"]
customers = [(f"C-{1000 + i}", f"{k} {t}" + (f" {n}" if n > 1 else ""), region[t])
             for i, (k, t, n) in enumerate((k, t, n) for n in (1, 2) for k in kinds for t in towns)][:360]
products = {"Espresso beans 1kg": 24.90, "Filter coffee 1kg": 19.50, "Capsules box 100": 38.00,
            "Decaf beans 1kg": 26.40, "Machine rental (month)": 145.00, "Descaler pack": 12.90}
season = {1: .85, 2: .80, 3: .90, 4: .90, 5: .95, 6: .90, 7: .80, 8: .75, 9: .95, 10: 1.05, 11: 1.00, 12: 1.25}

ERP_ROWS, WEB_ROWS = 167_000, 18_000
weight = sum(season.values())
erp, oid = [], 400001
for m in range(1, 13):
    for _ in range(round(ERP_ROWS * season[m] / weight)):
        cid, cname, reg = random.choice(customers)
        p = random.choice(list(products))
        qty = random.randint(1, 3) if "rental" in p else random.randint(2, 40)
        d = random.randint(1, calendar.monthrange(2025, m)[1])
        erp.append([f"SO-{oid}", f"2025-{m:02d}-{d:02d}", cid, cname, reg, p, qty, products[p], round(qty * products[p], 2), "ERP"])
        oid += 1
erp.sort(key=lambda r: r[1])

web = []
for i in range(WEB_ROWS):
    m = random.choices(range(1, 13), weights=[season[x] for x in range(1, 13)])[0]
    d = random.randint(1, calendar.monthrange(2025, m)[1])
    p = random.choice(["Espresso beans 1kg", "Filter coffee 1kg", "Capsules box 100", "Decaf beans 1kg", "Descaler pack"])
    qty = random.randint(1, 4)
    web.append([f"WS-{900001 + i}", f"{d:02d}/{m:02d}/2025", "C-WEB", "Webshop customer", random.choice(["Flanders", "Brussels", "Wallonia"]),
                p, qty, products[p], round(qty * products[p], 2), "Webshop"])
web.sort(key=lambda r: (r[1][6:], r[1][3:5], r[1][:2]))

be = lambda v: f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
month_of = lambda r: int(r[1][5:7]) if r[9] == "ERP" else int(r[1][3:5])

# truth
true_m = defaultdict(float)
for r in erp + web: true_m[month_of(r)] += r[8]
true_total = sum(true_m.values())

# assemble file rows
lines = []
for m in range(1, 13):
    block = [r for r in erp if month_of(r) == m]
    lines += [[r[0], r[1], r[2], r[3], r[4], r[5], r[6], f"{r[7]:.2f}", f"{r[8]:.2f}", r[9]] for r in block]
    lines.append(["", "", "", f"TOTAL {calendar.month_name[m].upper()} 2025", "", "", "", "", f"{sum(r[8] for r in block):.2f}", "ERP"])
lines += [[r[0], r[1], r[2], r[3], r[4], r[5], r[6], be(r[7]), be(r[8]), r[9]] for r in web]
nov = [r for r in erp if r[1] >= "2025-11-20" and month_of(r) == 11]
lines += [[r[0], r[1], r[2], r[3], r[4], r[5], r[6], f"{r[7]:.2f}", f"{r[8]:.2f}", r[9]] for r in nov]

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Order ID", "Order date", "Customer ID", "Customer", "Region", "Product", "Qty", "Unit price (EUR)", "Net amount (EUR)", "Source system"])
    w.writerows(lines)

# where things are (1-based data row numbers, header = row 1 in Excel)
first_web = next(i for i, l in enumerate(lines) if l[9] == "Webshop") + 2
first_dup = len(lines) - len(nov) + 2
sub_rows = [i + 2 for i, l in enumerate(lines) if l[3].startswith("TOTAL")]

fmt = lambda v: f"€{v:,.0f}"
print(f"rows {len(lines):,} + header | file {OUT.stat().st_size/1e6:.1f} MB")
print(f"subtotal rows at Excel rows {sub_rows[0]:,} ... {sub_rows[-1]:,} | webshop block from row {first_web:,} | duplicate November from row {first_dup:,}")
print("TRUE total", fmt(true_total), "| best month", calendar.month_name[max(true_m, key=true_m.get)])
for m in range(1, 13): print(f"   {calendar.month_abbr[m]} {fmt(true_m[m])}")
# likely naive outcomes
erp_m = defaultdict(float)
for r in erp: erp_m[month_of(r)] += r[8]
nov_dup = sum(r[8] for r in nov)
web_total = sum(r[8] for r in web)
sub_total = sum(erp_m.values())
print("Scenario A: webshop text dropped, subtotals excluded, Nov duplicate counted:", fmt(true_total - web_total + nov_dup), "| November", fmt(erp_m[11] + nov_dup), "vs December", fmt(erp_m[12]))
print("Scenario B: as A but subtotals counted too:", fmt(true_total - web_total + nov_dup + sub_total))
print("Scenario C: only the duplicate missed:", fmt(true_total + nov_dup))
print(f"webshop value {fmt(web_total)} | duplicate value {fmt(nov_dup)} | subtotal rows sum {fmt(sub_total)}")
