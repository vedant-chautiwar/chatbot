import pytest
from httpx import AsyncClient

from tests.conftest import TEST_USER_1_ID, TEST_USER_2_ID


@pytest.mark.asyncio
async def test_create_conversation(auth_client_1: AsyncClient):
    """Authenticated user can create a conversation."""
    response = await auth_client_1.post("/api/conversations", json={"title": "AI Research"})
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == "AI Research"
    assert data["user_id"] == TEST_USER_1_ID
    assert data["message_count"] == 0


@pytest.mark.asyncio
async def test_list_conversations_and_pagination(auth_client_1: AsyncClient):
    """User can list their own conversations with pagination."""
    # Create 3 conversations
    for i in range(3):
        await auth_client_1.post("/api/conversations", json={"title": f"Conv {i}"})

    # Fetch page with limit 2
    res = await auth_client_1.get("/api/conversations?limit=2&offset=0")
    assert res.status_code == 200
    page = res.json()
    assert page["total"] == 3
    assert len(page["items"]) == 2
    assert page["limit"] == 2
    assert page["offset"] == 0

    # Fetch second page
    res_page2 = await auth_client_1.get("/api/conversations?limit=2&offset=2")
    assert res_page2.status_code == 200
    page2 = res_page2.json()
    assert len(page2["items"]) == 1


@pytest.mark.asyncio
async def test_get_conversation_detail(auth_client_1: AsyncClient):
    """User can fetch their conversation details and messages."""
    created = await auth_client_1.post("/api/conversations", json={"title": "Detail Test"})
    conv_id = created.json()["id"]

    res = await auth_client_1.get(f"/api/conversations/{conv_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["conversation"]["id"] == conv_id
    assert data["conversation"]["title"] == "Detail Test"
    assert isinstance(data["messages"], list)


@pytest.mark.asyncio
async def test_rename_conversation(auth_client_1: AsyncClient):
    """User can rename their conversation."""
    created = await auth_client_1.post("/api/conversations", json={"title": "Old Name"})
    conv_id = created.json()["id"]

    res = await auth_client_1.patch(
        f"/api/conversations/{conv_id}",
        json={"title": "New Awesome Name"},
    )
    assert res.status_code == 200
    assert res.json()["title"] == "New Awesome Name"


@pytest.mark.asyncio
async def test_rename_conversation_validation_error(auth_client_1: AsyncClient):
    """Blank title in rename must trigger 422 validation error."""
    created = await auth_client_1.post("/api/conversations", json={"title": "Initial"})
    conv_id = created.json()["id"]

    res = await auth_client_1.patch(
        f"/api/conversations/{conv_id}",
        json={"title": "   "},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_delete_conversation(auth_client_1: AsyncClient):
    """User can delete their conversation."""
    created = await auth_client_1.post("/api/conversations", json={"title": "To Delete"})
    conv_id = created.json()["id"]

    del_res = await auth_client_1.delete(f"/api/conversations/{conv_id}")
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Conversation deleted successfully"

    # Confirm it is no longer found
    get_res = await auth_client_1.get(f"/api/conversations/{conv_id}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_cross_user_access_blocked(
    auth_client_1: AsyncClient, auth_client_2: AsyncClient
):
    """
    CRITICAL SECURITY CHECK:
    User B must NEVER be able to read, update, or delete User A's conversations.
    Returns 404 without leaking conversation existence.
    """
    # User 1 creates a private conversation
    created = await auth_client_1.post(
        "/api/conversations",
        json={"title": "User 1 Secret Discussion"},
    )
    user1_conv_id = created.json()["id"]

    # User 2 attempts to GET User 1's conversation -> 404
    res_get = await auth_client_2.get(f"/api/conversations/{user1_conv_id}")
    assert res_get.status_code == 404
    assert res_get.json()["detail"] == "Conversation not found"

    # User 2 attempts to RENAME User 1's conversation -> 404
    res_patch = await auth_client_2.patch(
        f"/api/conversations/{user1_conv_id}",
        json={"title": "Hacked Title"},
    )
    assert res_patch.status_code == 404

    # User 2 attempts to DELETE User 1's conversation -> 404
    res_delete = await auth_client_2.delete(f"/api/conversations/{user1_conv_id}")
    assert res_delete.status_code == 404

    # User 2 lists conversations -> User 1's conversation is not listed
    res_list = await auth_client_2.get("/api/conversations")
    assert res_list.status_code == 200
    user2_items = res_list.json()["items"]
    assert not any(item["id"] == user1_conv_id for item in user2_items)
