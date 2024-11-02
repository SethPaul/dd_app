import structlog
from . import prompt_helper

logger = structlog.get_logger(__name__)

async def create_session(table, client, session_id):
    thread_id = await prompt_helper.create_thread(client)
    item = {
        'SessionId': session_id,
        'Users': [],
        'Dialogue': [],
        'ChatHistory': [],
        'ThreadId': thread_id,
        'ConnectionIds': []
    }
    return item

async def update_session_connection_ids(table, session_id, connection_ids):
    await table.update_item(
        Key={'SessionId': session_id},
        UpdateExpression='SET ConnectionIds = :connection_ids',
        ExpressionAttributeValues={':connection_ids': connection_ids}
    )

async def get_session(table, session_id):
    session = await table.get_item(Key={'SessionId': session_id})
    return session['Item'] if 'Item' in session else None

async def get_or_create_session(table, client, session_id):
    # Retrieve existing session or create a new one
    session = await get_session(table, session_id)
    if session:
        logger.info("Existing session found")
    else:
        logger.info("Creating new session")
        session = await create_session(table, client, session_id)
    return session


async def update_bios_as_needed(table, client, body, item, stream_to_connections):
    new_users = []
    new_user_bios_json = []
    # If no UserBios, generate new bios for all users
    if 'UserBios' not in item or not item['UserBios']:
        item['UserBios'] = {}
        new_users = body['users']
        item['Users'] = new_users
    else:
        for user in body['users']:
            if user['name'] not in [u['name'] for u in item['Users']]:
                new_users.append(user)
                item['Users'].append(user)
        
    if new_users:
        new_user_bios_json = prompt_helper.generate_character_bios(
                client=client,
                thread_id=item['ThreadId'],
                users=new_users,
                stream_to_connections=stream_to_connections
                
            )
        character_dict = {char["name"]: char for char in new_user_bios_json}
        updated_user_bios = item['UserBios']|character_dict
        item['UserBios'].update(updated_user_bios)

    await table.put_item(Item=item)
    return new_user_bios_json

async def add_message_to_session(table, client, body, item, stream_to_connections):
     # Add user's action to dialogue
    user_action = {
        'user': body['user'],
        'msg': body['msg']
    }
    item['Dialogue'].append(user_action)
    # Update chat history
    item['ChatHistory'].append({'role': 'user', 'content': f"{body['user']}: {body['msg']}"})
    # Process action and generate DM response
    dm_response = await prompt_helper.process_action(client, item['ThreadId'], user_action, stream_to_connections)
    dm_dialogue = {
        'user': 'system',
        'msg': dm_response
    }
    item['Dialogue'].append(dm_dialogue)
    # Update chat history with assistant's response
    item['ChatHistory'].append({'role': 'assistant', 'content': dm_response})
    # Update session in DynamoDB
    await table.put_item(Item=item)
    return dm_response
 