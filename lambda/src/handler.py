
import boto3
import structlog
from utils.http_handler import handle_http_request
from utils.websocket_handler import handle_websocket_connection
import utils.prompt_helper as prompt_helper

# Initialize LLM client
llm_client = prompt_helper.setup_llm()
# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('DungeonsAndDragonsSessions')

# Initialize structlog
logger = structlog.get_logger(__name__)


async def lambda_handler(event, context):
    structlog.contextvars.clear_contextvars()
    logger.info("Lambda function invoked", requestevent=event)
    # Get HTTP method and session ID
    if 'httpMethod' in event:
        return await handle_http_request(event, table, llm_client)
    else:
        return await handle_websocket_connection(event, table, llm_client)
