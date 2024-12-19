import json
import uuid

import pytest

import mock
import os
import dotenv

dotenv.load_dotenv()

# Sample event templates
def generate_get_event(session_id):
    return {
        'httpMethod': 'GET',
        'pathParameters': {'id': session_id},
        'requestContext': {
            'domainName': os.getenv('WEBSOCKET_API_URL'),
            'stage': os.getenv('STAGE')
        }
    }

def generate_post_event(session_id, body):
    return {
        'httpMethod': 'POST',
        'pathParameters': {'id': session_id},
        'body': json.dumps(body),
        'requestContext': {
            'domainName': os.getenv('WEBSOCKET_API_URL'),
            'stage': os.getenv('STAGE')
        }
    }

def generate_delete_event(session_id):
    return {
        'httpMethod': 'DELETE',
        'pathParameters': {'id': session_id},
        'requestContext': {
            'domainName': os.getenv('WEBSOCKET_API_URL'),
            'stage': os.getenv('STAGE')
        }
    }

# Mock data
sample_session_id = 'test-session-id'
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

def test_get_session_not_found():
    from handler import lambda_handler
    # Arrange
    event = generate_get_event('non-existent-session')

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'error' in body

def test_get_session_found():
    from handler import lambda_handler
    # Arrange
    event = generate_get_event(sample_session_id)

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'users' in body

def test_post_session_without_user():
    from handler import lambda_handler
    # Arrange
    event = generate_post_event(sample_session_id, sample_body_without_users)

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200

def test_session_lifecycle():
    from handler import lambda_handler
    # Arrange
    # random_session_id = str(uuid.uuid4())
    random_session_id = 'test-session-id'
    
    event = generate_post_event(random_session_id, sample_body)

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200, f"Failed to create session: {response['body']}"
    body = json.loads(response['body'])

    # Act
    response = lambda_handler(generate_get_event(random_session_id), None)

    # Assert
    assert response['statusCode'] == 200, f"Failed to get session: {response['body']}"
    body = json.loads(response['body'])
    assert body['users'] == sample_users

    # Act 
    response = lambda_handler(generate_post_event(random_session_id, sample_body_without_users), None)
    assert response['statusCode'] == 200, f"Failed to add user to session: {response['body']}"

    # Act   
    response = lambda_handler(generate_post_event(random_session_id, sample_body), None)
    assert response['statusCode'] == 200, f"Failed to add message to session: {response['body']}"

    # Act
    # delete the session
    response = lambda_handler(generate_delete_event(random_session_id), None)

    # Assert
    assert response['statusCode'] == 200, f"Failed to delete session: {response['body']}"
    body = json.loads(response['body'])
    assert body['message'] == 'Session deleted successfully'

def test_post_invalid_method():
    from handler import lambda_handler
    # Arrange
    event = {
        'httpMethod': 'PUT',
        'pathParameters': {'id': sample_session_id},
    }

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 405
    body = json.loads(response['body'])
    assert 'error' in body


@mock.patch.dict(
    os.environ,
    {"WEBSOCKET_API_URL": os.getenv('WEBSOCKET_API_URL'),
     "STAGE": os.getenv('STAGE')},
    clear=True,
)
def test_post_without_user_or_msg():
    from handler import lambda_handler
    # Arrange
    sample_session_id = str(uuid.uuid4())
    event = generate_post_event(sample_session_id, sample_body_without_user_or_msg)

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200

    # Act       
    response = lambda_handler(generate_get_event(sample_session_id), None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['users'] == sample_users

    # Act
    response = lambda_handler(generate_delete_event(sample_session_id), None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['message'] == 'Session deleted successfully'
