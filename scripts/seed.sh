#!/usr/bin/env bash
# Adds sample inventory through the public API.
#   ./scripts/seed.sh                         -> http://localhost:8000
#   ./scripts/seed.sh http://localhost:3000   -> through the frontend's nginx
#   HOST_HEADER=inventrack.local ./scripts/seed.sh http://localhost:8080   -> through the Ingress
set -euo pipefail
BASE="${1:-http://localhost:8000}"
HEADERS=(-H "Content-Type: application/json")
[[ -n "${HOST_HEADER:-}" ]] && HEADERS+=(-H "Host: $HOST_HEADER")

add() {
  local name=$1 sku=$2 category=$3 supplier=$4 qty=$5 price=$6 reorder=$7
  local body
  body=$(printf '{"name":"%s","sku":"%s","category":"%s","supplier":"%s","quantity":%s,"unit_price":%s,"reorder_level":%s}' \
    "$name" "$sku" "$category" "$supplier" "$qty" "$price" "$reorder")
  if curl -sf -o /dev/null "${HEADERS[@]}" -X POST "$BASE/api/items" -d "$body"; then
    echo "  added   $sku  $name"
  else
    echo "  skipped $sku  (already exists?)"
  fi
}

echo "Seeding $BASE"
add "Ergonomic Office Chair"   "CHR-210" "Furniture"   "SitWell Ltd"     14 7499  4
add "Standing Desk 140cm"      "DSK-140" "Furniture"   "SitWell Ltd"      3 18999 4
add "Wireless Keyboard"        "KBD-305" "Peripherals" "KeyCraft"        36 1899  10
add "Optical Mouse"            "MSE-120" "Peripherals" "KeyCraft"         6 549   10
add "24-inch IPS Monitor"      "MON-240" "Displays"    "PixelPoint"      11 10999 5
add "Laser Printer"            "PRN-500" "Printers"    "InkJetters"       2 13499 2
add "A4 Paper Ream (500)"      "PAP-A4"  "Stationery"  "PaperTrail Co"   80 289   25
add "Whiteboard Markers (4pk)" "MRK-004" "Stationery"  "PaperTrail Co"    0 199   15
add "USB-C Docking Station"    "DCK-900" "Accessories" "PortHub"          9 6499  3
add "Cat6 Ethernet Cable 5m"   "NET-605" "Networking"  "LinkWorks"       45 349   20
echo "Done."
