import json
import structlog

import utils.session_manager as session_manager

logger = structlog.get_logger(__name__)



response_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Access-Control-Allow-Headers,Access-Control-Allow-Origin",
    "Access-Control-Allow-Methods": "DELETE,GET,OPTIONS,POST",
    "Content-Type": "text/html"
}

async def handle_http_request(event, table, llm_client):
    method = event['httpMethod']
    session_id = event['pathParameters']['id']
    structlog.contextvars.bind_contextvars(session_id=session_id)   

    if method == 'GET':
        logger.info("Handling GET request")
        response = await session_manager.get_session(table, session_id)
    elif method == 'POST':
        logger.info("Handling POST request")
        body = json.loads(event['body'])
        response = await session_manager.add_entry(table, llm_client, session_id, body)
    elif method == 'DELETE':
        logger.info("Handling DELETE request")
        response = await session_manager.delete_session(table, session_id)
    else:
        logger.warning("Unsupported HTTP method", method=method)
        response = {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'}),
            }

        logger.info("Lambda function completed", response_status=response['statusCode'])
    response['headers'] = response_headers
    return response
