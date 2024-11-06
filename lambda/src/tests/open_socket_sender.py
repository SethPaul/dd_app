# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Purpose

Shows how to use the AWS SDK for Python (Boto3) with Amazon API Gateway V2 to
create a websocket chat application. The application routes all requests to an AWS
Lambda function that tracks connections in an Amazon DynamoDB table and posts
messages to other chat participants.
"""

import argparse
import asyncio
import io
import json
import logging
import os
import uuid
import zipfile

import boto3
from dotenv import load_dotenv
import websockets
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


async def chat_demo(uri):
    """
    Shows how to use the deployed websocket API to connect users to the chat
    application and send messages to them.

    The demo connects three passive users who listen for messages, and one active
    user who sends messages to the other users through the websocket API.

    :param uri: The websocket URI of the chat application.
    """
    print(f"Connecting to {uri}")
    # session_id = str(uuid.uuid4())
    session_id = "test-session-id"
    
    async def sender(name):
        async with websockets.connect(uri=f"{uri}?session_id={session_id}") as socket:
            # for msg in ('foo', 'bar', 'baz'):
            #     await asyncio.sleep(1)
            #     print(f"< {name}: {msg}")         
            await socket.send(json.dumps({"action": "sendmessage", "msg": {
            'user': "Seth",
            'msg': 'I cast a fireball at the enemies.',
            'session_id': session_id
            }}))

    await asyncio.gather(
        sender("DemoDude")
    )


def main():
    load_dotenv()
    # uri = os.getenv("WEBSOCKET_URL")
    # uri="wss://j1n451vl6g.execute-api.us-west-1.amazonaws.com/test"
    uri="wss://2myr6m0jz5.execute-api.us-west-1.amazonaws.com/dev"
    asyncio.run(chat_demo(uri))

if __name__ == "__main__":
    main()
