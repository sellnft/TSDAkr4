import pytest
from faker import Faker

fake = Faker()
Faker.seed(42)

class TestUserAPI:
    @pytest.mark.asyncio
    async def test_create_user_success(self, async_client, clean_db):
        user_data = {
            "username": fake.user_name(),
            "age": fake.random_int(min=18, max=100)
        }
        response = await async_client.post("/users", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["username"] == user_data["username"]
        assert data["age"] == user_data["age"]
        assert isinstance(data["id"], int)

    @pytest.mark.asyncio
    async def test_get_existing_user(self, async_client, clean_db):
        user_data = {"username": fake.user_name(), "age": 30}
        create_response = await async_client.post("/users", json=user_data)
        user_id = create_response.json()["id"]
        
        response = await async_client.get(f"/users/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == user_data["username"]
        assert data["age"] == user_data["age"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, async_client, clean_db):
        response = await async_client.get("/users/99999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    @pytest.mark.asyncio
    async def test_delete_existing_user(self, async_client, clean_db):
        user_data = {"username": fake.user_name(), "age": 25}
        create_response = await async_client.post("/users", json=user_data)
        user_id = create_response.json()["id"]
        
        response = await async_client.delete(f"/users/{user_id}")
        
        assert response.status_code == 204
        assert response.text == ""

    @pytest.mark.asyncio
    async def test_delete_same_user_twice(self, async_client, clean_db):
        user_data = {"username": fake.user_name(), "age": 25}
        create_response = await async_client.post("/users", json=user_data)
        user_id = create_response.json()["id"]
        
        first_delete = await async_client.delete(f"/users/{user_id}")
        assert first_delete.status_code == 204
        
        second_delete = await async_client.delete(f"/users/{user_id}")
        assert second_delete.status_code == 404
        assert second_delete.json()["detail"] == "User not found"