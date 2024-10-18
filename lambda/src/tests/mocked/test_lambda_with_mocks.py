import json
import pytest
from unittest.mock import patch, MagicMock
from handler import lambda_handler
import handler

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
sample_session_id = 'test-session'
sample_users = [
    {'name': 'Seth', 'role': 'Wizard'},
    {'name': 'Hank', 'role': 'Warrior'}
]
sample_body = {
    'users': sample_users,
    'user': 'Seth',
    'msg': 'I cast a fireball at the orc.'
}

# Mock responses
mock_get_item_response = {
    'Item': {
        'SessionId': sample_session_id,
        'Users': sample_users,
        'Dialogue': [
            {'user': 'Seth', 'msg': 'I cast a fireball at the orc.'},
            {'user': 'system', 'msg': 'The orc is engulfed in flames.'}
        ],
        'ChatHistory': []
    }
}

@pytest.fixture
def mock_dynamodb():
    with patch('handler.dynamodb') as mock_dynamodb_resource:
        mock_table = MagicMock()
        mock_dynamodb_resource.resource.return_value.Table.return_value = mock_table
        yield mock_table

@pytest.fixture
def mock_openai():
    with patch('handler.openai') as mock_openai_module:
        mock_chat_completion = MagicMock()
        mock_chat_completion.create.return_value = {
            'choices': [{
                'message': {
                    'content': 'The orc is engulfed in flames.'
                }
            }]
        }
        mock_openai_module.ChatCompletion = mock_chat_completion
        yield mock_openai_module

def test_get_session_success(mock_dynamodb):
    # Arrange
    mock_dynamodb.get_item.return_value = mock_get_item_response
    event = generate_get_event(sample_session_id)

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['users'] == sample_users
    assert body['dialogue'] == mock_get_item_response['Item']['Dialogue']

def test_get_session_not_found(mock_dynamodb):
    # Arrange
    mock_dynamodb.get_item.return_value = {}
    event = generate_get_event('non-existent-session')

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'error' in body

def test_post_session_new(mock_dynamodb, mock_openai):
    # Arrange
    mock_dynamodb.get_item.return_value = {}
    event = generate_post_event(sample_session_id, sample_body)

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body == 'The orc is engulfed in flames.'
    # Verify that DynamoDB put_item was called
    assert mock_dynamodb.put_item.called

def test_post_session_existing(mock_dynamodb, mock_openai):
    # Arrange
    mock_dynamodb.get_item.return_value = mock_get_item_response
    event = generate_post_event(sample_session_id, {
        'user': 'Hank',
        'msg': 'I charge at the orc with my sword.'
    })
    # Update mock OpenAI response
    mock_openai.ChatCompletion.create.return_value = {
        'choices': [{
            'message': {
                'content': 'You slash the orc, and it falls defeated.'
            }
        }]
    }

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body == 'You slash the orc, and it falls defeated.'
    # Verify that DynamoDB put_item was called
    assert mock_dynamodb.put_item.called

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


def test_post_session_new_users(mock_dynamodb, mock_openai):
    # Arrange
    mock_dynamodb.get_item.return_value = {}
    event = generate_post_event(sample_session_id, {'users': sample_users})

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert "Generated bio for new character" in body
    mock_dynamodb.put_item.assert_called_once()
    mock_openai.assert_called_once()

def test_post_session_add_new_user(mock_dynamodb, mock_openai):
    # Arrange
    existing_users = [{'name': 'Seth', 'role': 'Wizard'}]
    mock_dynamodb.get_item.return_value = {'Item': {'SessionId': sample_session_id, 'Users': existing_users, 'Dialogue': [], 'ChatHistory': [], 'UserBios': {}}}
    new_user = {'name': 'Hank', 'role': 'Warrior'}
    event = generate_post_event(sample_session_id, {'users': existing_users + [new_user]})

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert "Generated bio for new character" in body
    mock_dynamodb.put_item.assert_called_once()
    mock_openai.assert_called_once()
    # Check that the call to put_item includes the new user
    put_item_call_args = mock_dynamodb.put_item.call_args[1]['Item']
    assert len(put_item_call_args['Users']) == 2
    assert new_user in put_item_call_args['Users']

def test_post_session_no_new_users(mock_dynamodb, mock_openai):
    # Arrange
    existing_users = [{'name': 'Seth', 'role': 'Wizard'}, {'name': 'Hank', 'role': 'Warrior'}]
    mock_dynamodb.get_item.return_value = {'Item': {'SessionId': sample_session_id, 'Users': existing_users, 'Dialogue': [], 'ChatHistory': []}}
    event = generate_post_event(sample_session_id, {'users': existing_users})

    # Act
    response = lambda_handler(event, None)

    # Assert
    assert response['statusCode'] == 500  # Because 'user' and 'msg' are missing
    body = json.loads(response['body'])
    assert 'error' in body
    mock_dynamodb.put_item.assert_not_called()
    mock_openai.assert_not_called()

# ... existing code ...