import json
import structlog

import utils.session_operations as session_operations
import utils.session_manager as session_manager

from botocore.exceptions import ClientError 
logger = structlog.get_logger(__name__)

async def handle_websocket_connection(event, table, llm_client):
    
    route_key = event.get("requestContext", {}).get("routeKey")
    connection_id = event.get("requestContext", {}).get("connectionId")
    domain_name = event.get("requestContext", {}).get("domainName")
    stage = event.get("requestContext", {}).get("stage")
    body_str = event.get("body", '{"msg": ""}')
    body = json.loads(body_str) if body_str is not None else {"msg": ""}

    logger.info("Websocket connection established", route_key=route_key, connection_id=connection_id, domain_name=domain_name, stage=stage)
    session_id = event.get("queryStringParameters", {"session_id": "global"}).get("session_id")
    if not session_id or session_id == "global":
        logger.warning("No session id provided")
        session_id = body.get("session_id", 'global')
    structlog.contextvars.bind_contextvars(session_id=session_id)  
    response = {"statusCode": 200}
    if route_key == "$connect":
        response["statusCode"] = await handle_connect(session_id, table, connection_id, llm_client)
    elif route_key == "$disconnect":
        response["statusCode"] = await handle_disconnect(session_id, table, connection_id, llm_client)
    elif route_key == "sendmessage":
        domain = event.get("requestContext", {}).get("domainName")
        stage = event.get("requestContext", {}).get("stage")
        if domain is None or stage is None:
            logger.warning(
                "Couldn't send message. Bad endpoint in request: domain '%s', "
                "stage '%s'",
                domain,
                stage,
            )
            response["statusCode"] = 400
        else:
  
            response["statusCode"] = await handle_message(
                session_id, table, connection_id, body, llm_client
            )
    else:
        response["statusCode"] = 404

    return response

async def handle_connect(session_id, table, connection_id, llm_client):
    """
    Handles new connections by adding the connection ID and user name to the
    DynamoDB table.

    :param session_id: The ID of the session that the connection is for.
    :param table: The DynamoDB connection table.
    :param connection_id: The websocket connection ID of the new connection.
    :return: An HTTP status code that indicates the result of adding the connection
             to the DynamoDB table.
    """
    status_code = 200

    try:
        session = await session_operations.get_or_create_session(table, llm_client, session_id)
        # add the connection id to the session
        new_connection_ids = session["ConnectionIds"] + [connection_id]
        await session_operations.update_session_connection_ids(table, session_id, new_connection_ids)
        
        logger.info("Added connection %s for session %s.", connection_id, session_id)
    except ClientError:
        logger.exception(
            "Couldn't add connection %s for session %s.", connection_id, session_id
        )
        status_code = 503
    return status_code

async def handle_disconnect(session_id, table, connection_id, llm_client):
    """
    Handles disconnections by removing the connection record from the DynamoDB table.

    :param table: The DynamoDB connection table.
    :param connection_id: The websocket connection ID of the connection to remove.
    :return: An HTTP status code that indicates the result of removing the connection
             from the DynamoDB table.
    """
    status_code = 200
    try:
        session = await session_operations.get_or_create_session(table, llm_client, session_id)
        new_connection_ids = [conn_id for conn_id in session.get("ConnectionIds", []) if conn_id != connection_id]
        await session_operations.update_session_connection_ids(table, session_id, new_connection_ids)
        logger.info("Disconnected connection %s.", connection_id)
    except ClientError:
        logger.exception("Couldn't disconnect connection %s.", connection_id)
        status_code = 503
    return status_code


async def handle_message(session_id, table, connection_id, event_body, llm_client):
    """
    Handles messages sent by a participant in the chat. Looks up all connections
    currently tracked in the DynamoDB table, and uses the API Gateway Management API
    to post the message to each other connection.

    When posting to a connection results in a GoneException, the connection is
    considered disconnected and is removed from the table. This is necessary
    because disconnect messages are not always sent when a client disconnects.

    :param table: The DynamoDB connection table.
    :param connection_id: The ID of the connection that sent the message.
    :param event_body: The body of the message sent from API Gateway. This is a
                       dict with a `msg` field that contains the message to send.
    :param apig_management_client: A Boto3 API Gateway Management API client.
    :return: An HTTP status code that indicates the result of posting the message
             to all active connections.
    """
    status_code = 200
    try:    
        await session_manager.add_entry(table, llm_client, session_id, event_body, connection_id)
    except Exception as e:
        logger.exception("Error adding entry", error=str(e), event_body=event_body)
        status_code = 500

    return status_code
