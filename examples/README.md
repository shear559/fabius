# Four tasks you can check

Each example ships with what was typed, what came back, and how to check it. The inputs are synthetic, so nothing here needs your data.

## 1 · Summarize a sales CSV

**Typed:** "Summarize this CSV. Show each line total, the sum, and the largest product by revenue. Do not assume a currency." with [sales.csv](sales.csv): coffee 3 × 40, tea 5 × 18, mug 2 × 35.

**Came back** ([sales-output.json](sales-output.json)):

```json
{"line_totals": {"coffee": 120, "tea": 90, "mug": 70}, "total": 280, "items": 10,
 "largest_product_by_revenue": "coffee", "currency": null}
```

**Check it:** 120 + 90 + 70 = 280. The currency is `null` because the file never names one.

## 2 · Fix a Python bug and run the boundary tests

**Typed** ([average-input.md](average-input.md)): fix `average()`, which divided by `len(values) - 1`; an empty list must raise `ValueError`; run tests for `[2, 4, 6]`, `[5]` and `[]` and report what was observed.

**Came back** ([average.py](average.py)):

```python
def average(values):
    if not values:
        raise ValueError("average requires at least one value")
    return sum(values) / len(values)
```

**Check it:** `[2, 4, 6]` gives 4, `[5]` gives 5, and `[]` raises `ValueError` with exactly that message. [verify.py](verify.py) asserts all three.

## 3 · Turn meeting notes into next steps

**Typed** ([meeting-input.md](meeting-input.md)): notes with two named roles, three action dates, no decision owner and no approved budget. "Do not invent missing ownership or approval. Return a draft; do not send messages or create calendar events."

**Came back** ([meeting-output.md](meeting-output.md)): three actions with their dates (2026-09-14, 09-16, 09-17) and three open questions. The launch decision is listed with owner **Unspecified**, and the summary says "The notes do not approve a budget or a launch."

**Check it:** every owner and date traces to the notes. The missing owner stayed missing. The result is an unsent draft: no message, no calendar event.

## 4 · Plan a 30-second vertical video

**Typed** ([video-input.md](video-input.md)): a reusable bottle for commuters; available props are hands, a bottle, a bag and a bus stop; no camera footage, renderer or media tools connected.

**Came back** ([video-output.md](video-output.md)): five shots with captions and two caption alternatives, headed "This is a shot list, not a rendered video."

**Check it:** 5 + 6 + 7 + 7 + 5 = 30 seconds. Every shot uses only the listed props. The output ends with "No MP4 has been generated."

## The checks that run

[verify.py](verify.py) recomputes examples 1 and 2 with the Python standard library, with no model and no network. Its output:

```
PASS average: ordinary=4, singleton=5, empty=ValueError
PASS sales: 120 + 90 + 70 = 280; items=10; largest=coffee; currency=unspecified
```

Examples 3 and 4 are checked by reading: the checks are written at the foot of each output file.

To try one yourself, paste its prompt into a fresh session and start it with `fabius:`. The [Quickstart](../QUICKSTART.md) has the install commands.

These are demonstrations prepared by the maintainer (Codex desktop, Fabius 2.8.1). They are not a benchmark and not a comparison against a bare model. Professional or client use needs permission: see [LICENSE](../LICENSE).
