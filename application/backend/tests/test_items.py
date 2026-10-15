def test_create_item(client):
    response = client.post(
        "/api/items",
        json={"name": "USB-C Hub", "sku": "HUB-7", "quantity": 3, "unit_price": 19.99, "reorder_level": 4},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["category"] == "General"
    assert body["needs_reorder"] is True


def test_duplicate_sku_returns_409(client, keyboard):
    response = client.post("/api/items", json={"name": "Another", "sku": keyboard["sku"]})
    assert response.status_code == 409


def test_invalid_item_returns_422(client):
    response = client.post("/api/items", json={"name": "", "sku": "bad sku!", "quantity": -1})
    assert response.status_code == 422
    fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert fields == {"name", "sku", "quantity"}


def test_list_items(client, keyboard):
    response = client.get("/api/items")
    assert response.status_code == 200
    assert [item["sku"] for item in response.json()] == ["KB-100"]


def test_search_matches_name_sku_and_supplier(client, keyboard):
    client.post("/api/items", json={"name": "Webcam", "sku": "CAM-1", "supplier": "Visionary"})
    assert [i["sku"] for i in client.get("/api/items?search=webc").json()] == ["CAM-1"]
    assert [i["sku"] for i in client.get("/api/items?search=kb-1").json()] == ["KB-100"]
    assert [i["sku"] for i in client.get("/api/items?search=vision").json()] == ["CAM-1"]


def test_category_and_reorder_filters(client, keyboard):
    client.post("/api/items", json={"name": "HDMI Cable", "sku": "CAB-2", "category": "Cables", "quantity": 1})
    assert [i["sku"] for i in client.get("/api/items?category=Cables").json()] == ["CAB-2"]
    assert [i["sku"] for i in client.get("/api/items?reorder_only=true").json()] == ["CAB-2"]


def test_read_item(client, keyboard):
    response = client.get(f"/api/items/{keyboard['id']}")
    assert response.status_code == 200
    assert response.json()["supplier"] == "KeyCo"


def test_missing_item_returns_404(client):
    assert client.get("/api/items/424242").status_code == 404
    assert client.put("/api/items/424242", json={"name": "x"}).status_code == 404
    assert client.delete("/api/items/424242").status_code == 404


def test_update_changes_only_sent_fields(client, keyboard):
    response = client.put(f"/api/items/{keyboard['id']}", json={"quantity": 2, "unit_price": 50})
    assert response.status_code == 200
    body = response.json()
    assert body["quantity"] == 2
    assert body["unit_price"] == 50
    assert body["needs_reorder"] is True
    assert body["name"] == "Mechanical Keyboard"


def test_update_to_existing_sku_returns_409(client, keyboard):
    other = client.post("/api/items", json={"name": "Mouse", "sku": "MS-1"}).json()
    response = client.put(f"/api/items/{other['id']}", json={"sku": keyboard["sku"]})
    assert response.status_code == 409


def test_delete_item(client, keyboard):
    assert client.delete(f"/api/items/{keyboard['id']}").status_code == 204
    assert client.get(f"/api/items/{keyboard['id']}").status_code == 404


def test_categories(client, keyboard):
    client.post("/api/items", json={"name": "Cable", "sku": "C-1", "category": "Cables"})
    assert client.get("/api/categories").json() == ["Cables", "Peripherals"]
