import json
from handler import lambda_handler
import pytest
from unittest.mock import patch

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


# Mock data
sample_session_id = 'foo'
sample_users = [
    {'name': 'Seth', 'role': 'Wizard'},
    {'name': 'Hank', 'role': 'Warrior'}
]
sample_body = {
    'users': sample_users,
    'user': 'Seth',
    'msg': 'I cast a fireball at the orc.'
}

sample_body_without_user_or_msg = {
    'users': sample_users,
}


def test_get_session_success():
    # Arrange
    event = generate_get_event(sample_session_id)

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['users'] == sample_users
    # assert body['dialogue'] == mock_get_item_response['Item']['Dialogue']

def test_get_session_not_found():
    # Arrange
    event = generate_get_event('non-existent-session')

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'error' in body

def test_post_session_new():
    # Arrange
    event = generate_post_event(sample_session_id, sample_body)

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    # assert body == 'The orc is engulfed in flames.'
    # Verify that DynamoDB put_item was called
    # assert mock_dynamodb.put_item.called

def test_post_session_existing():
    # Arrange
    event = generate_post_event(sample_session_id, {
        'user': 'Hank',
        'msg': 'I charge at the orc with my sword.'
    })

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    # assert body == 'You slash the orc, and it falls defeated.'

def test_post_invalid_method():
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

def test_post_missing_parameters():
    # Arrange
    event = generate_post_event(sample_session_id, {'msg': 'I look around.'})

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body

def test_post_without_user_or_msg():
    # Arrange
    event = generate_post_event(sample_session_id, sample_body_without_user_or_msg)

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'UserBios' in body
