import json
import structlog
import boto3

import utils.session_operations as session_operations
import utils.session_manager as session_manager

from botocore.exceptions import ClientError 
logger = structlog.get_logger(__name__)

def handle_websocket_connection(event, session_table, connection_table, llm_client):
    
    route_key = event.get("requestContext", {}).get("routeKey")
    connection_id = event.get("requestContext", {}).get("connectionId")
    domain_name = event.get("requestContext", {}).get("domainName")
    stage = event.get("requestContext", {}).get("stage")
    body_str = event.get("body", '{"msg": ""}')
    logger.info("Websocket connection established", route_key=route_key, connection_id=connection_id, domain_name=domain_name, stage=stage)
    
    response = {"statusCode": 200}
    if route_key == "$connect":
        session_id = event.get("queryStringParameters", {"session_id": ""}).get("session_id")
        structlog.contextvars.bind_contextvars(session_id=session_id)  
        response["statusCode"] = handle_connect(
            session_id=session_id,
            session_table=session_table,
            connection_table=connection_table,
            connection_id=connection_id,
            llm_client=llm_client
        )
    elif route_key == "$disconnect":
        response["statusCode"] = handle_disconnect(
            connection_table=connection_table,
            connection_id=connection_id,
        )
    elif route_key == "sendmessage":
        domain = event.get("requestContext", {}).get("domainName")
        stage = event.get("requestContext", {}).get("stage")
        api_gateway_management_client = boto3.client(
            "apigatewaymanagementapi", endpoint_url=f"https://{domain}/{stage}"
        )
        
        body = json.loads(body_str) if body_str is not None else {"msg": ""}
        message = body.get("msg", "")   
        if domain is None or stage is None:
            logger.warning(
                "Couldn't send message. Bad endpoint in request: domain '%s', "
                "stage '%s'",
                domain,
                stage,
            )
            response["statusCode"] = 400
        else:
            response["statusCode"] = handle_message(
                session_table=session_table,    
                connection_table=connection_table,
                connection_id=connection_id,
                event_body=message,
                llm_client=llm_client,
                api_gateway_management_client=api_gateway_management_client
            )
    else:
        response["statusCode"] = 404

    return response

def handle_connect(session_id, session_table,connection_table, connection_id, llm_client):
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
        session = session_operations.get_or_create_session(
            session_table=session_table,
            llm_client=llm_client,
            session_id=session_id
        )
        # add the connection id to the session
        session_operations.add_connection_id_to_session(
            connection_table=connection_table,
            session_id=session_id,
            connection_id=connection_id
        )
        
        logger.info("Added connection %s for session %s.", connection_id, session_id)
    except ClientError:
        logger.exception(
            "Couldn't add connection %s for session %s.", connection_id, session_id
        )
        status_code = 503
    return status_code

def handle_disconnect(connection_table, connection_id):
    """
    Handles disconnections by removing the connection record from the DynamoDB table.

    :param table: The DynamoDB connection table.
    :param connection_id: The websocket connection ID of the connection to remove.
    :return: An HTTP status code that indicates the result of removing the connection
             from the DynamoDB table.
    """
    status_code = 200
    try:
        session_operations.remove_connection_id_from_session(
            connection_table=connection_table,
            connection_id=connection_id
        )
        logger.info("Disconnected connection %s.", connection_id)
    except ClientError:
        logger.exception("Couldn't disconnect connection %s.", connection_id)
        status_code = 503
    return status_code


def handle_message(session_table, connection_table, connection_id, event_body, llm_client, api_gateway_management_client):
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
        session_id = session_operations.get_session_id_for_connection(
            connection_table=connection_table,
            connection_id=connection_id
        )
        if session_id is None:
            logger.warning("Session ID not found for connection %s.", connection_id)
            status_code = 404
        else:
            structlog.contextvars.bind_contextvars(session_id=session_id)  
            session_manager.add_entry(
            session_table=session_table,
            llm_client=llm_client,
            session_id=session_id,
            message=event_body,
            connection_table=connection_table,
            connection_id=connection_id,
            api_gateway_management_client=api_gateway_management_client
        )
    except Exception as e:
        logger.exception("Error adding entry", error=str(e), event_body=event_body)
        status_code = 500

    return status_code
