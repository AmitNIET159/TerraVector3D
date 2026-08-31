"""Tests for parcel API endpoints."""
async def test_list_parcels_empty(client):
    response = await client.get("/api/v1/parcels")
    assert response.status_code == 200
    assert response.json() == []

async def test_get_parcel_not_found(client):
    response = await client.get("/api/v1/parcels/7A4B9C2D8E1F6G")
    assert response.status_code == 404

async def test_get_parcel_invalid_ulpin(client):
    response = await client.get("/api/v1/parcels/invalid")
    assert response.status_code == 422
