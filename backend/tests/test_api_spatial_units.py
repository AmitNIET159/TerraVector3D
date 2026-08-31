"""Tests for spatial unit API endpoints."""
async def test_get_spatial_unit_not_found(client):
    response = await client.get("/api/v1/spatial-units/U999")
    assert response.status_code == 404

async def test_get_spatial_unit_by_vertical_id_not_found(client):
    response = await client.get("/api/v1/spatial-units/vertical/7A4B9C2D8E1F6G-F04-U401-R01")
    assert response.status_code == 404

async def test_get_spatial_unit_invalid_vertical_id(client):
    response = await client.get("/api/v1/spatial-units/vertical/INVALID")
    assert response.status_code == 422
