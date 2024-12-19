import structlog
from utils.http_handler import handle_http_request
from utils.websocket_handler import handle_websocket_connection
import utils.prompt_helper as prompt_helper


import boto3

# Initialize LLM client
llm_client = prompt_helper.setup_llm()
# Initialize DynamoDB resource
session = boto3.Session()
dynamodb = session.resource('dynamodb')

# Initialize structlog
logger = structlog.get_logger(__name__)


def lambda_handler(event, context):
    structlog.contextvars.clear_contextvars()
    logger.info("Lambda function invoked", requestevent=event)
    session_table = dynamodb.Table('dd-infra-sessions')
    connection_table = dynamodb.Table('dd-infra-connections')

        # Get HTTP method and session ID
    if 'httpMethod' in event:
        return handle_http_request(event, session_table, connection_table, llm_client)
    else:
        return handle_websocket_connection(event, session_table, connection_table, llm_client)
