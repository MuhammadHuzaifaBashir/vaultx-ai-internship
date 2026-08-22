# Task 04 — Extraction Tool Results

**Model:** gemini-3.5-flash-lite

## Sample 1

**Input:**
```
Hey team, quick note — got the bill from Acme Supplies, invoice #INV-2291,
    total came out to $432.50. Not sure when it's due, they didn't mention a date this time.
    Items were: office chairs, desk lamps, and a whiteboard.
```

**Extracted:**
```json
{
  "vendor_name": "Acme Supplies",
  "invoice_number": "INV-2291",
  "total_amount": 432.5,
  "due_date": null,
  "line_items": [
    "office chairs",
    "desk lamps",
    "whiteboard"
  ]
}
```

## Sample 2

**Input:**
```
INVOICE
    Vendor: Bright Cleaning Co.
    Invoice #: BC-1042
    Due: 2026-09-15
    Amount Due: $150.00
    Services: Weekly office cleaning (August)
```

**Extracted:**
```json
{
  "vendor_name": "Bright Cleaning Co.",
  "invoice_number": "BC-1042",
  "total_amount": 150.0,
  "due_date": "2026-09-15",
  "line_items": [
    "Weekly office cleaning (August)"
  ]
}
```

## Sample 3

**Input:**
```
Hi, just forwarding this — no invoice number on it, but it's from GreenLeaf Catering
    for the team lunch, $89.99 total. They said pay whenever, no rush.
```

**Extracted:**
```json
{
  "vendor_name": "GreenLeaf Catering",
  "invoice_number": null,
  "total_amount": 89.99,
  "due_date": null,
  "line_items": [
    "team lunch"
  ]
}
```
