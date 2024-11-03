
import boto3
import structlog
from utils.http_handler import handle_http_request
from utils.websocket_handler import handle_websocket_connection
import utils.prompt_helper as prompt_helper


import asyncio
import aioboto3

# Initialize LLM client
llm_client = prompt_helper.setup_llm()
# Initialize DynamoDB resource
session = aioboto3.Session()
dynamodb = session.resource('dynamodb')

# Initialize structlog
logger = structlog.get_logger(__name__)


async def lambda_handler(event, context):
    structlog.contextvars.clear_contextvars()
    logger.info("Lambda function invoked", requestevent=event)
    async with session.resource('dynamodb') as dynamodb:
        table = await dynamodb.Table('DungeonsAndDragonsSessions')
        # Get HTTP method and session ID
        if 'httpMethod' in event:
            return await handle_http_request(event, table, llm_client)
        else:
            return await handle_websocket_connection(event, table, llm_client)
