import json
import logging
from handler import generate_character_bios
import pytest
from unittest.mock import patch, MagicMock

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def mock_openai():
    with patch('handler.openai.chat.completions.create') as mock_create:
        yield mock_create

def test_generate_character_bios(mock_openai):
    # Arrange
    users = [
        {'name': 'Seth', 'role': 'Wizard'},
        {'name': 'Hank', 'role': 'Warrior'}
    ]
    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        "Seth: A mysterious wizard with a penchant for arcane experiments. His eyes sparkle with otherworldly knowledge.\n"
        "Hank: A brave warrior with bulging muscles and a heart of gold. His sword has seen many battles, and his scars tell tales of victory."
    )
    mock_openai.return_value = mock_response

    # Act
    result = generate_character_bios(users)

    # Log the response and result
    logger.info(f"Mock OpenAI Response: {mock_response.choices[0].message.content}")
    logger.info(f"Generated Bios: {result}")

    # Assert
    assert isinstance(result, dict)
    assert "Seth" in result
    assert "Hank" in result
    assert "mysterious wizard" in result["Seth"]
    assert "brave warrior" in result["Hank"]
    
    mock_openai.assert_called_once()
    call_args = mock_openai.call_args[1]
    assert call_args['model'] == "gpt-3.5-turbo"
    assert len(call_args['messages']) == 2
    assert call_args['messages'][0]['role'] == "system"
    assert call_args['messages'][1]['role'] == "user"
    assert "Seth" in call_args['messages'][1]['content']
    assert "Hank" in call_args['messages'][1]['content']
    assert "Wizard" in call_args['messages'][1]['content']
    assert "Warrior" in call_args['messages'][1]['content']
    assert "Format your response as follows:" in call_args['messages'][1]['content']

    # Log the prompt sent to OpenAI
    logger.info(f"Prompt sent to OpenAI: {call_args['messages'][1]['content']}")

def test_generate_character_bios_single_user(mock_openai):
    # Arrange
    users = [{'name': 'Lila', 'role': 'Rogue'}]
    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        "Lila: A nimble rogue with quick fingers and a quicker wit. Her shadowy past is as mysterious as her current motives."
    )
    mock_openai.return_value = mock_response

    # Act
    result = generate_character_bios(users)

    # Log the response and result
    logger.info(f"Mock OpenAI Response: {mock_response.choices[0].message.content}")
    logger.info(f"Generated Bios: {result}")

    # Assert
    assert isinstance(result, dict)
    assert len(result) == 1
    assert "Lila" in result
    assert "nimble rogue" in result["Lila"]

def test_generate_character_bios_empty_list(mock_openai):
    # Arrange
    users = []

    # Act
    result = generate_character_bios(users)

    # Log the result
    logger.info(f"Generated Bios (Empty List): {result}")

    # Assert
    assert isinstance(result, dict)
    assert len(result) == 0
    mock_openai.assert_not_called()

def test_generate_character_bios_malformed_response(mock_openai):
    # Arrange
    users = [
        {'name': 'Seth', 'role': 'Wizard'},
        {'name': 'Hank', 'role': 'Warrior'}
    ]
    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        "Seth is a mysterious wizard.\n"
        "Hank is a brave warrior."
    )
    mock_openai.return_value = mock_response

    # Act
    result = generate_character_bios(users)

    # Log the response and result
    logger.info(f"Mock OpenAI Response (Malformed): {mock_response.choices[0].message.content}")
    logger.info(f"Generated Bios (Malformed Response): {result}")

    # Assert
    assert isinstance(result, dict)
    assert len(result) == 0  # No valid bios parsed

def test_generate_character_bios_mixed_format(mock_openai):
    # Arrange
    users = [
        {'name': 'Seth', 'role': 'Wizard'},
        {'name': 'Hank', 'role': 'Warrior'},
        {'name': 'Lila', 'role': 'Rogue'}
    ]
    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        "Seth: A mysterious wizard with arcane knowledge.\n"
        "Hank is a brave warrior with a heart of gold.\n"
        "Lila: A nimble rogue with a shadowy past."
    )
    mock_openai.return_value = mock_response

    # Act
    result = generate_character_bios(users)

    # Log the response and result
    logger.info(f"Mock OpenAI Response (Mixed Format): {mock_response.choices[0].message.content}")
    logger.info(f"Generated Bios (Mixed Format): {result}")

    # Assert
    assert isinstance(result, dict)
    assert len(result) == 2  # Only Seth and Lila should be parsed correctly
    assert "Seth" in result
    assert "Lila" in result
    assert "Hank" not in result
    assert "mysterious wizard" in result["Seth"]
    assert "nimble rogue" in result["Lila"]
