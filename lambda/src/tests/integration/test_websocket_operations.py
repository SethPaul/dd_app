import pytest
import json
from unittest.mock import Mock
import boto3
from botocore.stub import Stubber
from handler import lambda_handler

@pytest.fixture
def apigw_websocket_event():
    """Fixture for API Gateway WebSocket event"""
    return {'headers': {'Host': '2myr6m0jz5.execute-api.us-west-1.amazonaws.com', 'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits', 'Sec-WebSocket-Key': 'v7pgEDCqwA23ckY45tS0tw==', 'Sec-WebSocket-Version': '13', 'User-Agent': 'Python/3.12 websockets/13.1', 'X-Amzn-Trace-Id': 'Root=1-672ab448-11a48ce34cd2192b31ecb5bd', 'X-Forwarded-For': '67.2.185.203', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https'}, 'multiValueHeaders': {'Host': ['2myr6m0jz5.execute-api.us-west-1.amazonaws.com'], 'Sec-WebSocket-Extensions': ['permessage-deflate; client_max_window_bits'], 'Sec-WebSocket-Key': ['v7pgEDCqwA23ckY45tS0tw=='], 'Sec-WebSocket-Version': ['13'], 'User-Agent': ['Python/3.12 websockets/13.1'], 'X-Amzn-Trace-Id': ['Root=1-672ab448-11a48ce34cd2192b31ecb5bd'], 'X-Forwarded-For': ['67.2.185.203'], 'X-Forwarded-Port': ['443'], 'X-Forwarded-Proto': ['https']}, 'queryStringParameters': {'session_id': 'test-session-id'}, 'multiValueQueryStringParameters': {'session_id': ['test-session-id']}, 'requestContext': {'routeKey': '$connect', 'eventType': 'CONNECT', 'extendedRequestId': 'AzEbWEFmSK4FcdQ=', 'requestTime': '06/Nov/2024:00:11:52 +0000', 'messageDirection': 'IN', 'stage': 'dev', 'connectedAt': 1730851912281, 'requestTimeEpoch': 1730851912282, 'identity': {'userAgent': 'Python/3.12 websockets/13.1', 'sourceIp': '67.2.185.203'}, 'requestId': 'AzEbWEFmSK4FcdQ=', 'domainName': '2myr6m0jz5.execute-api.us-west-1.amazonaws.com', 'connectionId': 'AzEbWdXXyK4CGZA=', 'apiId': '2myr6m0jz5'}, 'isBase64Encoded': False}

# {
#         'requestContext': {
#             'connectionId': 'test-connection-id',
#             'routeKey': '$connect',
#             'domainName': 'test-domain',
#             'stage': 'test',
#         },
#         'queryStringParameters': {
#             "session_id": "test-session-id"
#         },
#         'body': None
#     }

@pytest.fixture
def dynamodb_client():
    """Fixture for DynamoDB client with stubber"""
    client = boto3.client('dynamodb')
    stubber = Stubber(client)
    stubber.activate()
    return client, stubber

class TestWebSocketOperations:
    def test_connection_handler(self, apigw_websocket_event, dynamodb_client):
        """Test successful WebSocket connection"""
        client, stubber = dynamodb_client
        
        # Mock DynamoDB put_item for connection
        stubber.add_response(
            'put_item',
            {},
            {
                'TableName': 'dd-infra-connections',
                'Item': {
                    'connection_id': {'S': 'test-connection-id'},
                    'session_id': {'S': 'test-session-id'}
                }
            }
        )
        
        
        response = lambda_handler(apigw_websocket_event, None)
        
        assert response['statusCode'] == 200

    def test_disconnect_handler(self, apigw_websocket_event, dynamodb_client):
        """Test successful WebSocket disconnection"""
        client, stubber = dynamodb_client
        
        # Mock DynamoDB delete_item for disconnection
        stubber.add_response(
            'delete_item',
            {},
            {
                'TableName': 'dd-infra-connections',
                'Key': {
                    'connectionId': {'S': 'test-connection-id'}
                }
            }
        )
        event = apigw_websocket_event.copy()
        event['requestContext']['routeKey'] = '$disconnect'
        event['queryStringParameters'] = {}
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200

    def test_message_handler(self, apigw_websocket_event, dynamodb_client):
        """Test WebSocket message handling"""
        client, stubber = dynamodb_client
        
        # Mock DynamoDB get_item for message
        stubber.add_response(
            'get_item',
            {
                'Item': {
                    'connection_id': {'S': 'test-connection-id'},
                    'session_id': {'S': 'test-session-id'}
                }
            },
            {
                'TableName': 'dd-infra-connections',
                'Key': {
                    'connection_id': {'S': 'test-connection-id'}
                }
            }
        )

        # Modify event to include message body
        event = apigw_websocket_event.copy()
        requestevent={
            'requestContext': 
            {'routeKey': 'sendmessage', 
            'messageId': 'Avq3PdgjyK4CIYQ=', 
            'eventType': 'MESSAGE', 
            'extendedRequestId': 'Avq3PF31yK4FU-Q=', 
            'requestTime': '04/Nov/2024:23:26:37 +0000', 
            'messageDirection': 'IN', 
            'stage': 'dev', 
            'connectedAt': 1730762795720, 
            'requestTimeEpoch': 1730762797991, 
            'identity': {'userAgent': 'Python/3.12 websockets/13.1', 'sourceIp': '67.2.185.203'}, 
                'requestId': 'Avq3PF31yK4FU-Q=', 
                'domainName': '2myr6m0jz5.execute-api.us-west-1.amazonaws.com', 
                'connectionId': 'test-connection-id', 
                'apiId': '2myr6m0jz5'
            }, 
            'body': '{"action": "sendmessage", "msg": {"user": "Seth", "msg": "I cast a fireball at the enemies."}}', 
            'isBase64Encoded': False,
        }
        # event['body'] = json.dumps({'action': 'test', 'message': 'Hello, WebSocket!'})
        # event['requestContext']['routeKey'] = 'sendmessage'
        
        response = lambda_handler(requestevent, None)
        
        assert response['statusCode'] == 200
     
    def test_invalid_message_format(self, apigw_websocket_event):
        """Test handling of invalid message format"""
        event = apigw_websocket_event.copy()
        event['body'] = 'invalid-json'
        event['requestContext']['routeKey'] = '$default'
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
