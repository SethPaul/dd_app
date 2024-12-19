# -*- coding: utf-8 -*-
import json
import os
import structlog
import requests
from dotenv import load_dotenv

import pytest
import yaml
from pytest import param

# Load environment variables from .env file
load_dotenv()

with open(f"{os.path.dirname(__file__)}/../../../samconfig.yaml", "rb") as f:
    samconfig_dict = yaml.safe_load(f)

logger = structlog.get_logger()

DEPLOY_ENV = os.getenv("DEPLOY_ENV", "default")
API_URL = os.getenv("API_URL", "<API_URL>")  # This will now pull from .env file

sessions = [
    {
        "session_id": "get_session_success",
        "payload": {
            "httpMethod": "GET",
            "pathParameters": {"id": "test-session-id"},
        },
        "expected_response": {
            "body":json.dumps({
            "users": [
                {"name": "Seth", "role": "Wizard"},
                {"name": "Hank", "role": "Warrior"}
            ],
            "dialogue": []
            }),
            "statusCode": 200
        }
        

    },
    {
        "session_id": "get_session_not_found",
        "payload": {
            "httpMethod": "GET",
            "pathParameters": {"id": "non-existent-session"},
        },
        "expected_response": {
            "body": json.dumps({"error": "Session not found"}),
            "statusCode": 404
        }
    },
    {
        "session_id": "post_session_new",
        "payload": {
            "httpMethod": "POST",
            "pathParameters": {"id": "new-session-id"},
            "body": json.dumps({
                "users": [
                    {"name": "Seth", "role": "Wizard"},
                    {"name": "Hank", "role": "Warrior"}
                ],
                "user": "Seth",
                "msg": "I cast a fireball at the orc."
            })
        },
        "expected_response": {
            "body": '"The orc is engulfed in flames."',  # This is a placeholder. Actual response will vary.
            "statusCode": 200
        }
    },
        {
        "session_id": "test-session-id",
        "payload": {
            "httpMethod": "POST",
            "pathParameters": {"id": "new-session-id"},
            "body": json.dumps({
                "users": [
                    {"name": "Seth", "role": "Wizard"},
                    {"name": "Hank", "role": "Warrior"}
                ],
            })
        },
        "expected_response": {
            "body": '"Something about each user"',  # This is a placeholder. Actual response will vary.
            "statusCode": 200
        }
    },
    {
        "session_id": "post_session_existing",
        "payload": {
            "httpMethod": "POST",
            "pathParameters": {"id": "test-session-id"},
            "body": json.dumps({
                "user": "Hank",
                "msg": "I charge at the orc with my sword."
            })
        },
        "expected_response": {
            "body": '"You slash the orc, and it falls defeated."',  # This is a placeholder. Actual response will vary.
            "statusCode": 200
        }
    },
    {
        "session_id": "post_invalid_method",
        "payload": {
            "httpMethod": "PUT",
            "pathParameters": {"id": "test-session-id"},
        },
        "expected_response": {
            "body": json.dumps({"error": "Method not allowed"}),
            "statusCode": 200
        }
    },
    {
        "session_id": "post_missing_parameters",
        "payload": {
            "httpMethod": "POST",
            "pathParameters": {"id": "test-session-id"},
            "body": json.dumps({"msg": "I look around."})
        },
        "expected_response": {
            "body": json.dumps({"error": "KeyError: 'user'"}),  # Assuming this is the error message when 'user' is missing
            "statusCode": 200
        }
    }
]


@pytest.mark.parametrize("session", [
    param(session, id=session["session_id"]) for session in sessions
])
def test_api(session):
    url = f"{API_URL}/{session['payload']['pathParameters']['id']}"
    method = session['payload']['httpMethod']
    
    logger.info("Sending request", url=url, method=method, session_id=session['session_id'])
    
    if method == 'GET':
        response = requests.get(url)
    elif method == 'POST':
        body = json.loads(session['payload'].get('body', '{}'))
        response = requests.post(url, json=body)
    else:
        response = requests.request(method, url)
    
    logger.info("Received response", 
                status_code=response.status_code, 
                content=response.text,
                session_id=session['session_id'])
    
    assert response.status_code == session['expected_response']['statusCode'], f"Unexpected status code for session {session['session_id']}"
    
    logger.info(f"response.text: {response.text}")
