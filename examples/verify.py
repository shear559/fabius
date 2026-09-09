"""Reproduce artifact checks; no model, network or third-party packages."""
import csv
import json
from decimal import Decimal
from pathlib import Path
from average import average

root = Path(__file__).resolve().parent
assert average([2, 4, 6]) == 4
assert average([5]) == 5
try:
    average([])
except ValueError as error:
    assert str(error) == "average requires at least one value"
else:
    raise AssertionError("empty average must raise ValueError")
with (root / "sales.csv").open(newline="") as stream:
    rows = list(csv.DictReader(stream))
totals = {row["product"]: Decimal(row["quantity"]) * Decimal(row["unit_price"]) for row in rows}
actual = json.loads((root / "sales-output.json").read_text())
assert actual["line_totals"] == totals
assert actual["total"] == sum(totals.values()) == 280
assert actual["items"] == sum(int(row["quantity"]) for row in rows) == 10
assert actual["largest_product_by_revenue"] == max(totals, key=totals.get) == "coffee"
assert actual["currency"] is None
print("PASS average: ordinary=4, singleton=5, empty=ValueError")
print("PASS sales: 120 + 90 + 70 = 280; items=10; largest=coffee; currency=unspecified")
