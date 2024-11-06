import json
import time
import structlog
from . import prompt_helper
from boto3.dynamodb.conditions import Key

logger = structlog.get_logger(__name__)
connection_ids = []

def create_session(session_table, llm_client, session_id):
    thread_id = prompt_helper.create_thread(llm_client)
    session = {
        'session_id': session_id,
        'user_set': [],
        'dialogue': [],
        'chat_history': [],
        'thread_id': thread_id,
        'expiration_time': int(time.time()) + 3600 * 24 * 7
    }
    session_table.put_item(Item=session)
    return session

def add_connection_id_to_session(connection_table, session_id, connection_id):
    connection_table.put_item(
        Item={
            'session_id': session_id, 
            'connection_id': connection_id,
            'expiration_time': int(time.time()) + 360000
        }
    )

def get_session_id_for_connection(connection_table, connection_id):
    connection = connection_table.get_item(Key={'connection_id': connection_id})
    return connection['Item']['session_id'] if 'Item' in connection else None

def remove_connection_id_from_session(connection_table, connection_id):
    connection_table.update_item(
        Key={'connection_id': connection_id},
        UpdateExpression='SET expiration_time = :expiration_time',
        ExpressionAttributeValues={':expiration_time': int(time.time()+30)}
    )

def get_connection_ids(connection_table, session_id):
    current_time = int(time.time())
    connection_ids = connection_table.scan(
        FilterExpression=Key('session_id').eq(session_id) & Key('expiration_time').gt(current_time),
        ProjectionExpression='connection_id'
    )
    return [connection['connection_id'] for connection in connection_ids['Items']] if connection_ids['Items'] else []

def check_processing_flag_to_session(session_table, session_id):
    session = session_table.get_item(Key={'session_id': session_id}, ProjectionExpression='processing')
    return session.get('processing', False) 

def get_session(session_table, session_id):
    session = session_table.get_item(Key={'session_id': session_id})
    return session['Item'] if 'Item' in session else None


def delete_session(session_table, session_id, connection_table):
    session_table.delete_item(Key={'session_id': session_id})
    # get all connection ids    
    connection_ids = get_connection_ids(connection_table, session_id)
    for connection_id in connection_ids:
        remove_connection_id_from_session(connection_table, connection_id)

def get_or_create_session(session_table, llm_client, session_id):
    # Retrieve existing session or create a new one
    session = get_session(
        session_table=session_table, 
        session_id=session_id
    )
    if session:
        logger.info("Existing session found")
    else:
        logger.info("Creating new session")
        session = create_session(
            session_table=session_table, 
            llm_client=llm_client, 
            session_id=session_id
        )
    return session


def update_bios_as_needed(session_table, llm_client, body, session, stream_to_connections):
    new_users = []
    new_user_bios_dict_list = []
    updated_user_bios = {}
    # If no UserBios, generate new bios for all users
    if 'user_bios' not in session or not session['user_bios']:
        session['user_bios'] = {}
        new_users = list({v['name']:v for v in session['user_set'] + body['users']}.values())
    else:
        for user in body['users']:
            if user['name'] not in [u['name'] for u in session['user_set']]:
                new_users.append(user)
    
    if new_users:
        stream_to_connections(message="I see new members have joined our party:")
        new_user_bios_dict_list =  prompt_helper.generate_character_bios(
                llm_client=llm_client,
                thread_id=session['thread_id'],
                users=new_users,
                stream_to_connections=stream_to_connections
                
            )
        character_dict = {char: new_user_bios_dict_list[char] for char in new_user_bios_dict_list}
        updated_user_bios = session['user_bios']|character_dict
        
    
    if new_users:
        users = list({v['name']:v for v in session['user_set'] + new_users}.values())
        session_table.update_item(
            Key={'session_id': session['session_id']}, 
            UpdateExpression='SET user_set = :users, user_bios = :user_bios', 
            ExpressionAttributeValues={':users': users, ':user_bios': updated_user_bios}
        )
    elif updated_user_bios:
        session_table.update_item(
            Key={'session_id': session['session_id']}, 
            UpdateExpression='SET user_bios = :user_bios', 
            ExpressionAttributeValues={':user_bios': updated_user_bios}
        )   
    return new_user_bios_dict_list

def add_message_to_session(session_table, llm_client, body, session, stream_to_connections):
     # Add user's action to dialogue
    user_action = {
        'user': body['user'],
        'msg': body['msg']
    }
    session['dialogue'].append(user_action)
    # Update chat history
    session['chat_history'].append({'role': 'user', 'content': f"{body['user']}: {body['msg']}"})
    # Process action and generate DM response
    dm_response = prompt_helper.process_action(
        llm_client=llm_client,
        thread_id=session['thread_id'],
        user_action=user_action,
        stream_to_connections=stream_to_connections
    )
    dm_dialogue = {
        'user': 'Dungeon Master',
        'msg': (dm_response
                    .replace("\u2018", "'")
                    .replace("\u2019", "'")
        )
    }
    session['dialogue'].append(dm_dialogue)

    # Update chat history with assistant's response
    session['chat_history'].append({'role': 'Dungeon Master', 'content': dm_response})
    # Update session in DynamoDB
    session_table.update_item(
        Key={'session_id': session['session_id']}, 
        UpdateExpression='SET dialogue = :dialogue, chat_history = :chat_history', 
        ExpressionAttributeValues={':dialogue': session['dialogue'], ':chat_history': session['chat_history']}
    )
    return dm_response
 