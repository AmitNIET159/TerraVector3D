"""Tests for API error handling."""
async def test_identity_generate_bad_ulpin(client):
    response = await client.post(
        "/api/v1/identity/generate",
        json={"parent_ulpin": "BAD", "level": "04", "unit_code": "401", "revision": 1}
    )
    assert response.status_code == 422
