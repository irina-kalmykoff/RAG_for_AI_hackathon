"""Generate a deliberately dirty sales ledger for Marlow & Finch plus clean and naive answers."""
import csv, random, calendar
from collections import defaultdict
from pathlib import Path

random.seed(2025)
OUT = Path(__file__).resolve().parent.parent / "data" / "sales-ledger-2025.csv"

wholesale = {  # customer: typical monthly invoice (EUR)
    "Grand Hotel Scheldezicht": 20000, "Kantoorpark Zuid NV": 14000, "Hotel Ter Aa": 11000,
    "Brasserie De Klok": 7500, "Hotel Belfort Suites": 9000, "Vergaderzalen Linde": 5200,
    "Co-work Dok": 4300, "Bistro Oude Markt": 3900, "Hotel Aurelia": 8200,
    "Restaurant Veldzicht": 3100, "Kantoren Meir Plaza": 6600, "Café Noord BV": 2800,
}
cafes = {"Café Antwerpen Zuid": 41000, "Café Leuven Ladeuze": 36000, "Café Gent Kouter": 47000}
ws_variants = ["Wholesale"] * 7 + ["wholesale ", "WHOLESALE", "Whole sale"]
cafe_variants = ["Cafés"] * 3 + ["Cafes", "cafés"]

rows = []   # clean records: dict(date, customer, channel, doc, amount, source)
inv = 25001
for m in range(1, 13):
    for c, base in wholesale.items():
        d = random.randint(3, 27)
        rows.append(dict(y=2025, m=m, d=d, customer=c, channel="Wholesale", doc="Invoice",
                         amount=round(base * random.uniform(0.85, 1.15), 2), source="ERP", no=f"INV-{inv}"))
        inv += 1
    rows.append(dict(y=2025, m=m, d=calendar.monthrange(2025, m)[1], customer="Web shop (monthly batch)",
                     channel="Online", doc="Invoice", amount=round(52000 * random.uniform(0.85, 1.15), 2),
                     source="ERP", no=f"INV-{inv}"))
    inv += 1
    for c, base in cafes.items():
        rows.append(dict(y=2025, m=m, d=calendar.monthrange(2025, m)[1], customer=c, channel="Cafés",
                         doc="Monthly takings", amount=round(base * random.uniform(0.85, 1.15), 2),
                         source="Café till system", no=""))
# credit notes (true value negative, stored positive)
for m in (3, 7, 11):
    rows.append(dict(y=2025, m=m, d=15, customer="Hotel Belfort Suites", channel="Wholesale", doc="Credit note",
                     amount=6000.00, source="ERP", no=f"CN-{800 + m}"))

def signed(r): return -r["amount"] if r["doc"] == "Credit note" else r["amount"]
def q(m): return (m - 1) // 3 + 1

# ---- truth
by_ch, by_q, by_cust = defaultdict(float), defaultdict(float), defaultdict(float)
for r in rows:
    by_ch[r["channel"]] += signed(r); by_q[q(r["m"])] += signed(r)
    if r["channel"] == "Wholesale": by_cust[r["customer"]] += signed(r)
total = sum(by_ch.values())

# ---- build dirty file rows
dirty = []
for r in sorted(rows, key=lambda r: (r["m"], r["d"], r["customer"])):
    if r["source"] == "ERP":
        date = f"{r['y']}-{r['m']:02d}-{r['d']:02d}"
        amt = f"{r['amount']:.2f}"
        ch = random.choice(ws_variants) if r["channel"] == "Wholesale" else r["channel"]
    else:
        date = f"{r['d']:02d}/{r['m']:02d}/{r['y']}"
        amt = f"{r['amount']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        ch = random.choice(cafe_variants)
    dirty.append([r["no"], date, r["customer"], ch, r["doc"], amt, r["source"]])

# duplicates: 10 Kantoorpark invoices exported twice (appended at the end, as from a second export)
kp = [x for x in dirty if x[2] == "Kantoorpark Zuid NV"][:10]
dups = [list(x) for x in kp]

# subtotal rows after each quarter (sum of the quarter's ERP amounts as they appear, i.e. naive)
final = []
for qq in range(1, 5):
    block = [x for x in dirty if q(int(x[1][5:7]) if "-" in x[1] else int(x[1][3:5])) == qq]
    final += block
    sub = sum(float(x[5]) for x in block if x[6] == "ERP")
    final.append(["", "", f"Q{qq} TOTAL", "", "", f"{sub:.2f}", "ERP"])
final += dups

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Invoice no", "Date", "Customer", "Channel", "Document type", "Amount (EUR)", "Source system"])
    w.writerows(final)

# ---- naive: sum every numeric Amount as-is (text amounts dropped), no dedupe, credits positive
naive_total = sum(float(x[5]) for x in final if x[6] == "ERP")
naive_cust = defaultdict(float)
for x in final:
    if x[6] == "ERP" and x[3].strip().lower().replace(" ", "") == "wholesale":
        naive_cust[x[2]] += float(x[5])

fmt = lambda v: f"{v:,.0f}"
print("rows in file:", len(final))
print("TRUE total:", fmt(total))
for k, v in by_ch.items(): print("  TRUE channel", k, fmt(v))
for k, v in sorted(by_q.items()): print("  TRUE Q", k, fmt(v))
print("  TRUE top wholesale customers:", [(c, fmt(v)) for c, v in sorted(by_cust.items(), key=lambda t: -t[1])[:4]])
print("NAIVE total (numeric Amount column, incl. subtotals+dups, credits +, cafe text dropped):", fmt(naive_total))
print("  NAIVE top wholesale customers:", [(c, fmt(v)) for c, v in sorted(naive_cust.items(), key=lambda t: -t[1])[:4]])
print("  cafe rows (text amounts):", sum(1 for x in final if x[6] != "ERP"), " dup rows:", len(dups), " credit notes: 3")
print("  Belfort true", fmt(by_cust["Hotel Belfort Suites"]), "naive", fmt(naive_cust["Hotel Belfort Suites"]))
print("  Kantoorpark true", fmt(by_cust["Kantoorpark Zuid NV"]), "naive", fmt(naive_cust["Kantoorpark Zuid NV"]))
