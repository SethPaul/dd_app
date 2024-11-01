import random
import simplejson as json
import boto3
import utils.prompt_helper as prompt_helper
import utils.session_manager as session_manager
import structlog

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('DungeonsAndDragonsSessions')

# Initialize structlog
logger = structlog.get_logger(__name__)

prompt_helper.setup_llm()
response_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Access-Control-Allow-Headers,Access-Control-Allow-Origin",
    "Access-Control-Allow-Methods": "DELETE,GET,OPTIONS,POST",
    "Content-Type": "text/html"
}


def lambda_handler(event, context):
    structlog.contextvars.clear_contextvars()
    logger.info("Lambda function invoked", requestevent=event)
    # Get HTTP method and session ID
    method = event['httpMethod']
    session_id = event['pathParameters']['id']
    structlog.contextvars.bind_contextvars(session_id=session_id)   

    client = prompt_helper.setup_llm()

    if method == 'GET':
        logger.info("Handling GET request")
        response = get_session(table, client, session_id)
    elif method == 'POST':
        logger.info("Handling POST request")
        body = json.loads(event['body'])
        response = add_entry(table, client, session_id, body)
    elif method == 'DELETE':
        logger.info("Handling DELETE request")
        response = delete_session(table, session_id)
    else:
        logger.warning("Unsupported HTTP method", method=method)
        response = {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'}),
            'headers': response_headers  # Add headers here
        }
    
    # Add headers to the response
    # response['headers'] = response_headers

    logger.info("Lambda function completed", response_status=response['statusCode'])
    
    return response

def get_session(table, client, session_id):
    logger.info("Retrieving session")
    try:
        # Retrieve session from DynamoDB
        session = session_manager.get_session(table, session_id) 
        if session:
            logger.info("Session retrieved successfully")
            response = {
                'statusCode': 200,
                'body': json.dumps({
                    'users': session.get('Users', []),
                    'dialogue': session.get('Dialogue', [])
                }),
                'headers': response_headers  # Add headers here
            }
        else:
            logger.warning("Session not found")
            response = {
                'statusCode': 404,
                'body': json.dumps({'error': 'Session not found'}),
                'headers': response_headers  # Add headers here
            }
    except Exception as e:
        logger.error("Error retrieving session", error=str(e), exc_info=e)
        response = {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': response_headers  # Add headers here
        }

    return response

def add_entry(table, client, session_id, body):
    logger.info("Adding entry to session")
    
    try:
        # Retrieve existing session or create a new one
        session = session_manager.get_or_create_session(table, client, session_id)
        
        bios_text = None

        # Add new users to session
        if 'users' in body:
            new_user_bios_json = session_manager.update_bios_as_needed(table, client, body, session)
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
                'headers': response_headers  # Add headers here
            }

        dm_response = session_manager.add_message_to_session(table, client, body, session)

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
            'headers': response_headers  # Add headers here
        }
       
    except Exception as e:
        logger.error("Error adding entry", error=str(e), exc_info=e)

        response = {
            'statusCode': 500,
            'body': json.dumps({'error': random.choice(prompt_helper.error_responses)}),
            'headers': response_headers  # Add headers here
        }

    return response


def delete_session(table, session_id):
    logger.info("Deleting session")
    client = prompt_helper.setup_llm()
    try:
        # Retrieve session from DynamoDB
        session = table.get_item(Key={'SessionId': session_id})
        if 'Item' in session:
            item = session['Item']
            thread_id = item.get('ThreadId')

            # Delete the OpenAI thread if it exists
            if thread_id:
                logger.info("Deleting OpenAI thread", thread_id=thread_id)
                prompt_helper.delete_thread(client, thread_id)

            # Delete the session from DynamoDB
            logger.info("Deleting session from DynamoDB")
            table.delete_item(Key={'SessionId': session_id})

            logger.info("Session deleted successfully")
            response = {
                'statusCode': 200,
                'body': json.dumps({'message': 'Session deleted successfully'}),
                'headers': response_headers  # Add headers here
            }
        else:
            logger.warning("Session not found for deletion")
            response = {
                'statusCode': 404,
                'body': json.dumps({'error': 'Session not found'}),
                'headers': response_headers  # Add headers here
            }
    except Exception as e:
        logger.error("Error deleting session", error=str(e))
        response = {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': response_headers  # Add headers here
        }

    return response
