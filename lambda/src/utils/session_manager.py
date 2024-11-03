import json
import random
import structlog

logger = structlog.get_logger(__name__)
import utils.session_operations as session_operations
import utils.prompt_helper as prompt_helper

import aioboto3

from botocore.exceptions import ClientError

session = aioboto3.Session()
api_gateway_management_client = session.client('apigatewaymanagementapi')



async def get_session(table, session_id):
    logger.info("Retrieving session")
    try:
        # Retrieve session from DynamoDB
        session = await session_operations.get_session(table, session_id) 
        if session:
            logger.info("Session retrieved successfully")
            response = {
                'statusCode': 200,
                'body': json.dumps({
                    'users': session.get('Users', []),
                    'dialogue': session.get('Dialogue', [])
                })
            }
        else:
            logger.warning("Session not found")
            response = {
                'statusCode': 404,
                'body': json.dumps({'error': 'Session not found'}),
            }
    except Exception as e:
        logger.error("Error retrieving session", error=str(e), exc_info=e)
        response = {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }

    return response

async def add_entry(table, llm_client, session_id, body, connection_id=None):
    logger.info("Adding entry to session")
    
    try:
        # Retrieve existing session or create a new one
        session = await session_operations.get_or_create_session(table, llm_client, session_id)
        
        bios_text = None
        connection_ids = session.get('ConnectionIds', [])
        stream_to_connections = StreamToConnections(api_gateway_management_client, connection_id, connection_ids)
        await stream_to_connections(message= body)

        # Add new users to session
        if 'users' in body:
            new_user_bios_json = await session_operations.update_bios_as_needed(table, llm_client, body, session, stream_to_connections)
            if len(new_user_bios_json) == 0:
                user_bios_json = [session['UserBios'][character] for character in session['UserBios'].keys()]
                bios_text = prompt_helper.transform_to_html(user_bios_json)

            if new_user_bios_json:
                bios_text = prompt_helper.transform_to_html(new_user_bios_json)
        # if no action, return all stored bios
        
        if 'user' not in body or 'msg' not in body:
            return {
                'statusCode': 200,
                'body': bios_text,
            }

        dm_response = await session_operations.add_message_to_session(table, llm_client, body, session, stream_to_connections)

        # add new user bios before the response
        if bios_text:
            dm_response = f"""
            I see new members have joined our party: 
            {bios_text}

            Now as for that action...
            
            {dm_response}
            """

        # Return DM response
        response = {
            'statusCode': 200,
            'body': json.dumps(dm_response.replace("\u2018", "'").replace("\u2019", "'")),
        }
       
    except Exception as e:
        logger.error("Error adding entry", error=str(e), exc_info=e)

        response = {
            'statusCode': 500,
            'body': json.dumps({'error': random.choice(prompt_helper.error_responses)}),
        }

    return response


async def delete_session(table, session_id):
    logger.info("Deleting session")
    client = prompt_helper.setup_llm()
    try:
        # Retrieve session from DynamoDB
        session = await table.get_item(Key={'SessionId': session_id})
        if 'Item' in session:
            item = session['Item']
            thread_id = item.get('ThreadId')

            # Delete the OpenAI thread if it exists
            if thread_id:
                logger.info("Deleting OpenAI thread", thread_id=thread_id)
                await prompt_helper.delete_thread(client, thread_id)

            # Delete the session from DynamoDB
            logger.info("Deleting session from DynamoDB")
            await table.delete_item(Key={'SessionId': session_id})

            logger.info("Session deleted successfully")
            response = {
                'statusCode': 200,
                'body': json.dumps({'message': 'Session deleted successfully'}),
            }
        else:
            logger.warning("Session not found for deletion")
            response = {
                'statusCode': 404,
                'body': json.dumps({'error': 'Session not found'}),
            }
    except Exception as e:
        logger.error("Error deleting session", error=str(e))
        response = {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }

    return response


class StreamToConnections:  
    def __init__(self, api_gateway_management_client, connection_id, connection_ids):
        self.api_gateway_management_client = api_gateway_management_client
        self._connection_id = connection_id
        self.connection_ids = connection_ids
    
    @property
    def connection_id(self):
        return self._connection_id
    
    async def __call__(self, message):
        logger.info("Streaming to connections", connection_id=self.connection_id, connection_ids=self.connection_ids)

        for other_conn_id in self.connection_ids:
            try:
                if other_conn_id != self._connection_id:
                    send_response = await self.api_gateway_management_client.post_to_connection(
                        Data=message, ConnectionId=other_conn_id
                    )
            except ClientError:
                logger.exception("Couldn't post to connection %s.", other_conn_id)
            except self.api_gateway_management_client.exceptions.GoneException:
                logger.info("Connection %s is gone, removing.", other_conn_id)
                try:
                    await self.table.delete_item(Key={"connection_id": other_conn_id})
                except ClientError:
                    logger.exception("Couldn't remove connection %s.", other_conn_id)
