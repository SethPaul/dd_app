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


def lambda_handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_handler(event, context))

async def async_handler(event, context):
    structlog.contextvars.clear_contextvars()
    logger.info("Lambda function invoked", requestevent=event)
    async with session.resource('dynamodb') as dynamodb:
        session_table = await dynamodb.Table('DungeonsAndDragonsSessions')
        ## TODO: Add connection only table
        ## TODO: add lock on session table to prevent race condition
        connection_table = await dynamodb.Table('DungeonsAndDragonsConnections')

        # Get HTTP method and session ID
        if 'httpMethod' in event:
            return await handle_http_request(event, session_table, connection_table, llm_client)
        else:
            return await handle_websocket_connection(event, session_table, connection_table, llm_client)
