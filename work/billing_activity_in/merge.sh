#!/bin/sh
# Merge the IN pages into the release manual (release "Usermanualsources", asset Billing.Reporting.-.Billing.Activity.gui).
# Usage: work/billing_activity_in/merge.sh path/to/Billing.Reporting.-.Billing.Activity.gui
set -e
cd "$(dirname "$0")/../.."
REL="$1"; IN="output/Billing & Reporting - Billing Activity (IN).gui"; OUT="output/Billing & Reporting - Billing Activity (with IN).gui"
P=".venv/bin/python tools/ilis.py --no-open gui"
$P build work/billing_activity_in --out "$IN" >/dev/null
$P insert "$REL" /tmp/merge_in.gui --donor "$IN" --parent "Billing Activity Group Functions" \
  --match '^(Proforma Invoice Generation - Batch|Credit Invoice - IT \(Batch Function\))$'
$P insert /tmp/merge_in.gui "$OUT" --donor "$IN" --parent "Billing Activity Side Functions" \
  --match '^(Invoice Generation Single - \(IN\)|Proforma Invoice Generation - Single|Proforma Invoice Query & Reversal|E Invoice Operations)$'
rm -f /tmp/merge_in.gui
