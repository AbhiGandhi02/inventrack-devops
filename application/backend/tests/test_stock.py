def test_receive_and_ship_stock(client, keyboard):
    url = f"/api/items/{keyboard['id']}/movements"
    assert client.post(url, json={"change": 10, "reason": "Delivery"}).json()["quantity"] == 30
    assert client.post(url, json={"change": -26, "reason": "Order 77"}).json()["quantity"] == 4


def test_cannot_ship_more_than_in_stock(client, keyboard):
    response = client.post(f"/api/items/{keyboard['id']}/movements", json={"change": -21})
    assert response.status_code == 400
    assert "only 20 in stock" in response.json()["detail"]


def test_zero_change_is_rejected(client, keyboard):
    assert client.post(f"/api/items/{keyboard['id']}/movements", json={"change": 0}).status_code == 400


def test_movement_history_is_newest_first(client, keyboard):
    url = f"/api/items/{keyboard['id']}/movements"
    client.post(url, json={"change": 5, "reason": "Delivery"})
    client.post(url, json={"change": -3, "reason": "Order 12"})
    history = client.get(url).json()
    assert [(m["change"], m["reason"], m["quantity_after"]) for m in history] == [
        (-3, "Order 12", 22),
        (5, "Delivery", 25),
    ]


def test_movements_of_missing_item_return_404(client):
    assert client.get("/api/items/999/movements").status_code == 404


def test_summary(client, keyboard):
    client.post(
        "/api/items",
        json={"name": "Monitor", "sku": "MON-27", "category": "Displays", "quantity": 2, "unit_price": 199.99},
    )
    body = client.get("/api/summary").json()
    assert body == {
        "item_count": 2,
        "units_in_stock": 22,
        "stock_value": round(20 * 45.5 + 2 * 199.99, 2),
        "reorder_count": 1,
        "category_count": 2,
    }


def test_summary_of_empty_inventory(client):
    assert client.get("/api/summary").json()["stock_value"] == 0
