"""Tests for building API endpoints."""
async def test_get_building_not_found(client):
    response = await client.get("/api/v1/buildings/BLD999")
    assert response.status_code == 404
