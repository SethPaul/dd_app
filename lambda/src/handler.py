import json
import boto3
import openai

# Initialize DynamoDB resource
# dynamodb = boto3.resource('dynamodb')
# table = dynamodb.Table('DungeonsAndDragonsSessions')

# secret_client = boto3.client('secretsmanager')

# response = secret_client.get_secret_value(
#     SecretId='dd_open_ai_key'
# )

# # Set OpenAI API key from environment variable
# openai.api_key = response["SecretString"]



def lambda_handler(event, context):
    # Get HTTP method and session ID
    method = event['httpMethod']
    session_id = event['pathParameters']['id']

    if method == 'GET':
        # Handle GET request to retrieve session history
        response = get_session(session_id)
    elif method == 'POST':
        # Handle POST request to add a new entry
        body = json.loads(event['body'])
        response = add_entry(session_id, body)
    else:
        # Unsupported HTTP method
        response = {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    return response

def get_session(session_id):
    # try:
    #     # Retrieve session from DynamoDB
    #     session = table.get_item(Key={'SessionId': session_id})
    #     if 'Item' in session:
    #         item = session['Item']
    #         response = {
    #             'statusCode': 200,
    #             'body': json.dumps({
    #                 'users': item.get('Users', []),
    #                 'dialogue': item.get('Dialogue', [])
    #             })
    #         }
    #     else:
    #         # Session not found
    #         response = {
    #             'statusCode': 404,
    #             'body': json.dumps({'error': 'Session not found'})
    #         }
    # except Exception as e:
    #     # Internal server error
    #     response = {
    #         'statusCode': 500,
    #         'body': json.dumps({'error': str(e)})
    #     }


    response = {
                'isBase64Encoded': False,
                'statusCode': 200,
                'body': json.dumps({
                        "users": [
                            {"name": "Seth", "role":"Wizard"},
                            {"name": "Hank", "role":"Warrior"},
                            
                        ],
                        "dialogue": [
                            {"user": "system", "msg": "Welcome to the adventure"},
                            {"user": "seth", "msg": "I use my magic elixir to grow gigantic"},
                            {"user": "system", "msg": "You roll a 3. the elixir back fires and you shrink to half size"}
                        ]
                        }),
                        "headers":{
                            "Content-Type": "application/json"
                        }
                

                
            }
    return response

def add_entry(session_id, body):
    # try:
    #     # Retrieve existing session or create a new one
    #     session = table.get_item(Key={'SessionId': session_id})
    #     if 'Item' in session:
    #         item = session['Item']
    #     else:
    #         item = {
    #             'SessionId': session_id,
    #             'Users': [],
    #             'Dialogue': [],
    #             'ChatHistory': []
    #         }
    #         # Initialize chat history with the dungeon master prompt
    #         initial_prompt = get_dungeon_master_prompt(body.get('users', []))
    #         item['ChatHistory'] = [{'role': 'system', 'content': initial_prompt}]
    #         # Update users if provided
    #         if 'users' in body:
    #             item['Users'] = body['users']
    #     # Update users if provided
    #     if 'users' in body:
    #         item['Users'] = body['users']
    #     # Add user's action to dialogue
    #     user_action = {
    #         'user': body['user'],
    #         'msg': body['msg']
    #     }
    #     item['Dialogue'].append(user_action)
    #     # Update chat history
    #     item['ChatHistory'].append({'role': 'user', 'content': f"{body['user']}: {body['msg']}"})
    #     # Process action and generate DM response
    #     dm_response = process_action(item['ChatHistory'])
    #     dm_dialogue = {
    #         'user': 'system',
    #         'msg': dm_response
    #     }
    #     item['Dialogue'].append(dm_dialogue)
    #     # Update chat history with assistant's response
    #     item['ChatHistory'].append({'role': 'assistant', 'content': dm_response})
    #     # Update session in DynamoDB
    #     table.put_item(Item=item)
    #     # Return DM response
    #     response = {
    #         'statusCode': 200,
    #         'body': json.dumps(dm_response)
    #     }
    # except Exception as e:
    #     # Internal server error
    #     response = {
    #         'statusCode': 500,
    #         'body': json.dumps({'error': str(e)})
    #     }

    response = {
        'isBase64Encoded': False,
        'headers': {
            "Content-Type": "application/json"
        },
        'statusCode': 200,
        'body': "Hank rolls a 20. Seth lands on the giant's head. The giant is confused"
    }
    return response

def process_action(chat_history):
    # Call OpenAI ChatCompletion API
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=chat_history,
        max_tokens=150,
        temperature=0.7,
        n=1,
        stop=None
    )
    assistant_reply = response['choices'][0]['message']['content']
    return assistant_reply

def get_dungeon_master_prompt(users):
    # Generate the dungeon master prompt
    user_descriptions = '\n'.join([f"{user['name']} is a {user['role']}" for user in users])
    prompt = f"""You are a Dungeon Master for a simplified Dungeons and Dragons game designed for players unfamiliar with standard rules. Your goal is to guide the players through an exciting and fun adventure that lasts around 15 minutes or approximately 15 actions. The party consists of the following members:

{user_descriptions}

The adventure should be accessible and enjoyable, focusing on storytelling and collaborative play. Avoid complex rules or mechanics. Encourage creativity and help the players move towards a successful conclusion.

Begin the adventure when the first player provides their action."""
    return prompt
