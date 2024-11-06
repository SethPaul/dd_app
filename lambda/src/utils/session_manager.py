import json
import os
import random
import structlog
import boto3

logger = structlog.get_logger(__name__)
import utils.session_operations as session_operations
import utils.prompt_helper as prompt_helper
from openai.types.beta.threads.text import Text

from botocore.exceptions import ClientError


def get_session(session_table, session_id):
    logger.info("Retrieving session")
    try:
        # Retrieve session from DynamoDB
        session = session_operations.get_session(
            session_table=session_table, 
            session_id=session_id
        )
        if session:
            logger.info("Session retrieved successfully")
            response = {
                'statusCode': 200,
                'body': json.dumps({
                    'users': session.get('user_set', []),
                    'chat_history': session.get('chat_history', []),
                    'user_bios': session.get('user_bios', {})

                })
            }
        else:
            logger.warning("Session not found")
            response = {
                'statusCode': 404,
                'body': json.dumps({'error': 'Session not found'}),
            }
    except Exception as e:
        logger.error(
            "Error retrieving session", 
            error=str(e), 
            exc_info=e
        )
        response = {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }

    return response

def add_entry(session_table, llm_client, session_id, message, connection_table, connection_id=None, api_gateway_management_client=None):
    logger.info("Adding entry to session")
    
    try:
        # Retrieve existing session or create a new one
        session = session_operations.get_or_create_session(
            session_table=session_table,
            llm_client=llm_client,
            session_id=session_id
        )
        processing_check = session_operations.check_processing_flag_to_session(
            session_table=session_table,
            session_id=session_id
        )
        if processing_check:
            return {
                'statusCode': 200,
                'body': "Wait a moment, I'm still divining what happened with the last action.",
            }
        stream_to_connections = StreamToConnections(
            api_gateway_management_client=api_gateway_management_client,
            session_id=session_id,
            connection_id=connection_id,
            connection_table=connection_table
        )
        stream_to_connections.get_connection_ids(
            connection_table=connection_table,
            session_id=session_id
        )
        supplied_message = message.get('msg', None)
        if supplied_message:
            if 'user' in message:
                supplied_message = f"\n\n {message['user']}: {supplied_message} \n\n"
            stream_to_connections(message=supplied_message)

        # Add new users to session
        new_user_bios_dict_list = None
        if 'users' in message:
            new_user_bios_dict_list = session_operations.update_bios_as_needed(
                session_table=session_table,
                llm_client=llm_client,
                body=message,
                session=session,
                stream_to_connections=stream_to_connections
            )
            if len(new_user_bios_dict_list) == 0:
                user_bios_json = [session['user_bios'][character] for character in session['user_bios'].keys()]
                bios_text = '\n'.join(user_bios_json)

            if new_user_bios_dict_list:
                user_bios_json = [new_user_bios_dict_list[character] for character in new_user_bios_dict_list.keys()]
                bios_text = '\n'.join(user_bios_json)

        if 'user' not in message or 'msg' not in message:
            return {
                'statusCode': 200,
                'body': bios_text,
            }
        segue_text = ""
        if new_user_bios_dict_list:
            segue_text = f"""
            I see new members have joined our party: 
            
            {bios_text}

            Now as for that action...
            """
            stream_to_connections(message="Now as for that action...")
            

        dm_response = session_operations.add_message_to_session(
            session_table=session_table,
            llm_client=llm_client,
            body=message,
            session=session,
            stream_to_connections=stream_to_connections
        )

        # add new user bios before the response
        if segue_text:
            dm_response = f"""
            {segue_text}
            {dm_response}
            """

        response = {
            'statusCode': 200,
            'body': json.dumps(dm_response),
        }
       
    except Exception as e:
        logger.error(
            "Error adding entry",
            error=str(e),
            exc_info=e
        )

        response = {
            'statusCode': 200,
            'body': json.dumps({'error': random.choice(prompt_helper.error_responses)}),
        }

    return response


def delete_session(session_table, session_id, connection_table):
    logger.info("Deleting session")
    llm_client = prompt_helper.setup_llm()
    try:
        # Retrieve session from DynamoDB
        session = session_operations.get_session(
            session_table=session_table, 
            session_id=session_id
        )
        if session:
            thread_id = session.get('ThreadId')

            # Delete the OpenAI thread if it exists
            if thread_id:
                logger.info("Deleting OpenAI thread", thread_id=thread_id)
                prompt_helper.delete_thread(
                    llm_client=llm_client,
                    thread_id=thread_id
                )

            # Delete the session from DynamoDB
            logger.info("Deleting session from DynamoDB")
            session_operations.delete_session(
                session_table=session_table,
                session_id=session_id,
                connection_table=connection_table
            )

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
    def __init__(self, api_gateway_management_client, session_id, connection_id, connection_table):
        self.session_id = session_id
        self.api_gateway_management_client = api_gateway_management_client
        self._connection_id = connection_id
        self.connection_table = connection_table
        self.connection_ids = []
    
    
    @property
    def connection_id(self):
        return self._connection_id
    
    def get_connection_ids(self, connection_table, session_id):
        self.connection_ids = session_operations.get_connection_ids(
            connection_table=connection_table,
            session_id=session_id
        )
    
    def __call__(self, message):
        # logger.info("Streaming to connections", connection_id=self.connection_id, connection_ids=self.connection_ids)

        # Convert message to bytes
        if isinstance(message, dict):
            message_bytes = json.dumps(message).encode('utf-8')
        elif isinstance(message, str):
            message_bytes = message.encode('utf-8')
        elif isinstance(message, list):
            message_bytes = json.dumps(message).encode('utf-8')
        elif isinstance(message, int):
            message_bytes = str(message).encode('utf-8')
        elif isinstance(message, float):
            message_bytes = str(message).encode('utf-8')
        elif isinstance(message, bool):
            message_bytes = str(message).encode('utf-8')
        elif isinstance(message, Text):
            message_bytes = message.value.encode('utf-8')
        else:
            message_bytes = str(message).encode('utf-8')

        for other_conn_id in self.connection_ids:
            try:
                # if other_conn_id != self._connection_id:
                send_response = self.api_gateway_management_client.post_to_connection(
                    Data=message_bytes, ConnectionId=other_conn_id
                )
            except self.api_gateway_management_client.exceptions.GoneException as e:
                logger.info("Connection %s is gone, removing.", other_conn_id, exc_info=e)
                try:
                    session_operations.remove_connection_id_from_session(
                        connection_table=self.connection_table,
                        connection_id=other_conn_id
                    )
                    self.connection_ids.remove(other_conn_id)
                except ClientError as e:
                    logger.exception("Couldn't remove connection %s.", other_conn_id, exc_info=e)
            except ClientError as e:
                logger.exception("Couldn't post to connection %s.", other_conn_id, exc_info=e)
