"""Chunking case: big sales CSV -> naive fixed-size chunks -> keyword top-3 retrieval per question.
Writes data/sales-2025-full.csv and data/chunk-prompt-q1..q3.txt (what a document tool would pass to the chatbot)."""
import csv, io, math, random, re
from collections import Counter, defaultdict
from pathlib import Path

random.seed(11)
SP = Path(__file__).resolve().parent.parent / "data"
customers = {"Grand Hotel Scheldezicht": "Flanders", "Kantoorpark Zuid NV": "Flanders", "Hotel Ter Aa": "Flanders",
             "Brasserie De Klok": "Brussels", "Hotel Aurelia": "Brussels", "Co-work Dok": "Flanders",
             "Bistro Oude Markt": "Flanders", "Vergaderzalen Linde": "Brussels", "Restaurant Veldzicht": "Wallonia",
             "Hôtel des Ardennes": "Wallonia", "Café Noord BV": "Flanders", "Kantoren Meir Plaza": "Flanders",
             "Brasserie Sablon": "Brussels", "Hôtel Meuse Palace": "Wallonia", "Bureaux Namur Centre": "Wallonia"}
products = {"Espresso beans 1kg": 24.90, "Filter coffee 1kg": 19.50, "Capsules box 100": 38.00, "Machine rental (month)": 145.00}
rows, oid = [], 70001
for m in range(1, 13):
    for c, reg in customers.items():
        for p in random.sample(list(products), 3):
            qty = random.randint(4, 60) if "rental" not in p else random.randint(1, 4)
            d = random.randint(1, 28)
            rows.append([f"SO-{oid}", f"2025-{m:02d}-{d:02d}", c, reg, p, qty, f"{products[p]:.2f}", f"{qty*products[p]:.2f}"])
            oid += 1
rows.sort(key=lambda r: r[1])
header = ["Order ID", "Date", "Customer", "Region", "Product", "Qty", "Unit price (EUR)", "Net amount (EUR)"]
buf = io.StringIO(); w = csv.writer(buf, lineterminator="\n"); w.writerow(header); w.writerows(rows)
text = buf.getvalue()
(SP / "sales-2025-full.csv").write_text(text, encoding="utf-8-sig")

# naive chunking: fixed 2,000 characters, no respect for row boundaries, header only in chunk 1
SIZE = 2000
chunks = [text[i:i + SIZE] for i in range(0, len(text), SIZE)]

# keyword retrieval (BM25-lite)
tok = lambda s: [t for t in re.findall(r"[a-zà-ÿ0-9]+", s.lower()) if t not in {"the", "in", "of", "did", "we", "what", "was", "how", "many", "which", "from", "our", "total", "2025"}]
docs = [Counter(tok(c)) for c in chunks]; N = len(docs); avg = sum(sum(d.values()) for d in docs) / N
df = Counter(t for d in docs for t in d)
def top(q, k=3):
    qt = set(tok(q)); sc = []
    for i, d in enumerate(docs):
        L = sum(d.values()); s = 0
        for t in qt:
            if d[t]: s += math.log(1 + (N - df[t] + .5) / (df[t] + .5)) * d[t] * 2.2 / (d[t] + 1.2 * (.25 + .75 * L / avg))
        sc.append((s, i))
    return [i for s, i in sorted(sc, reverse=True)[:k]]

Q = {
    "q1": "What was the total 2025 revenue from Hotel Ter Aa?",
    "q2": "Which region generated the most revenue in 2025, and how much?",
    "q3": "How many boxes of capsules did we sell in December 2025?",
}
amt = lambda r: float(r[7])
truth = {
    "q1": f"€{sum(amt(r) for r in rows if r[2]=='Hotel Ter Aa'):,.2f} over {sum(1 for r in rows if r[2]=='Hotel Ter Aa')} orders",
    "q2": ", ".join(f"{k} €{v:,.2f}" for k, v in sorted(((reg, sum(amt(r) for r in rows if r[3]==reg)) for reg in {"Flanders","Brussels","Wallonia"}), key=lambda t: -t[1])),
    "q3": f"{sum(r[5] for r in rows if r[4]=='Capsules box 100' and r[1].startswith('2025-12'))} boxes",
}
print(f"rows {len(rows)}, chars {len(text)}, chunks {N}")
for k, q in Q.items():
    ids = top(q)
    print(f"\n{k}: {q}\n  TRUE: {truth[k]}\n  retrieved chunks: {ids} (chunk 0 has header: {0 in ids})")
    ctx = "\n".join(chunks[i] for i in ids)
    (SP / f"chunk-prompt-{k}.txt").write_text(
        "You are the assistant in a company's document Q&A tool. The tool found the relevant data in "
        "sales_2025.csv. Answer the user's question based on it.\n\n"
        f"--- Relevant data from sales_2025.csv ---\n{ctx}\n--- End of data ---\n\nUser question: {q}", encoding="utf-8")
