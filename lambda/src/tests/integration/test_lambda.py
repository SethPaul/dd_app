import json
import uuid
from handler import lambda_handler
import pytest

# Sample event templates
def generate_get_event(session_id):
    return {
        'httpMethod': 'GET',
        'pathParameters': {'id': session_id},
    }

def generate_post_event(session_id, body):
    return {
        'httpMethod': 'POST',
        'pathParameters': {'id': session_id},
        'body': json.dumps(body)
    }

def generate_delete_event(session_id):
    return {
        'httpMethod': 'DELETE',
        'pathParameters': {'id': session_id},
    }

# Mock data
sample_session_id = 'koioih8u98udw'
sample_users = [
    {'name': 'Seth', 'role': 'Wizard'},
    {'name': 'Hank', 'role': 'Warrior'}
]

sample_body_without_user_or_msg = {
    'users': sample_users,
}
sample_body_without_users = {
    'user': 'Seth',
    'msg': 'I cast a fireball at the enemies.'
}
sample_body = sample_body_without_user_or_msg | sample_body_without_users

@pytest.mark.asyncio
async def test_get_session_success():
    # Arrange
    event = generate_get_event("existing-session")

    # Act
    response = await lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['users'] == sample_users


@pytest.mark.asyncio
async def test_get_session_not_found():
    # Arrange
    event = generate_get_event('non-existent-session')

    # Act
    response = await lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'error' in body

@pytest.mark.asyncio
async def test_post_session_new():
    # Arrange
    random_session_id = str(uuid.uuid4())
    event = generate_post_event(random_session_id, sample_body)

    # Act
    response = await lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])

    # delete the session
    lambda_handler(generate_delete_event(random_session_id), None)

@pytest.mark.asyncio
async def test_post_session_existing():
    # Arrange
    
    event = generate_post_event("existing-session", sample_body)

    # Act
    response = await lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body != None

@pytest.mark.asyncio
async def test_post_invalid_method():
    # Arrange
    event = {
        'httpMethod': 'PUT',
        'pathParameters': {'id': sample_session_id},
    }

    # Act
    response = await lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 405
    body = json.loads(response['body'])
    assert 'error' in body


@pytest.mark.asyncio
async def test_post_without_user_or_msg():
    # Arrange
    event = generate_post_event(sample_session_id, sample_body_without_user_or_msg)

    # Act
    response = await lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200
    
