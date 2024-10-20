import json
import logging
from utils.prompt_helper import generate_character_bios, setup_llm
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def llm_prep(mock_toggle):
    if mock_toggle:
        return MagicMock()
    return setup_llm()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def mock_openai():
    with patch('utils.prompt_helper.generate_character_bios') as mock_create:
        yield mock_create

@pytest.fixture
def mock_client():
    return MagicMock()


def test_generate_character_bios(mock_toggle, llm_prep, mock_openai, mock_client):
    if not mock_toggle:
        pytest.skip("This test requires mocks")
    
    # Arrange
    users = [
        {'name': 'Seth', 'role': 'Wizard'},
        {'name': 'Hank', 'role': 'Warrior'}
    ]
    thread_id = "test_thread_id"
    mock_openai.return_value = {
        "characters": [
            {
                "name": "Seth",
                "role": "Wizard",
                "background": "Seth is a reclusive wizard, shunned by society due to the dark nature of his magical studies...",
                "role_description": "Spellcaster/Damage Dealer",
                "example_actions": {
                    "magic_missile": "Magic Missile - A basic attack spell that never misses and deals damage to a single enemy.",
                    "shield": "Shield - Seth can cast a magical barrier around himself or an ally, reducing damage taken.",
                    "special_move": "Fireball - Seth can unleash a powerful explosion of fire, damaging all enemies in a targeted area."
                },
                "stats": {
                    "Strength": 2,
                    "Dexterity": 1,
                    "Constitution": 2,
                    "Intelligence": 8,
                    "Wisdom": 5,
                    "Charisma": 6
                }
            },
            {
                "name": "Hank",
                "role": "Warrior",
                "background": "Hank is a battle-hardened warrior, known for his incredible strength and unyielding resolve...",
                "role_description": "Tank/Frontline Fighter",
                "example_actions": {
                    "shield_bash": "Shield Bash - Hank can strike an enemy with his shield, stunning them temporarily and pushing them back.",
                    "cleave": "Cleave - Hank delivers a powerful swing of his weapon, damaging multiple enemies in front of him.",
                    "whirlwind_attack": "Whirlwind Attack - A spinning strike that simultaneously attacks all nearby foes, showcasing Hank's impressive martial skills."
                },
                "stats": {
                    "Strength": 8,
                    "Dexterity": 4,
                    "Constitution": 6,
                    "Intelligence": 2,
                    "Wisdom": 3,
                    "Charisma": 4
                }
            }
        ]
    }

    # Act
    result = generate_character_bios(mock_client, users, thread_id)

    # Log the response and result
    # logger.info(f"Mock OpenAI Response: {mock_response.choices[0].message.content}")
    logger.info(f"Generated Bios: {result}")

    # Assert
    assert isinstance(result, dict)
    assert "Seth" in result["characters"]
    assert "Hank" in result["characters"]
    assert "mysterious wizard" in result["characters"]["Seth"]
    assert "brave warrior" in result["characters"]["Hank"]
    
    mock_openai.assert_called_once()
    call_args = mock_openai.call_args[1]
    assert call_args['model'] == "gpt-4o-mini"
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

    # Assert client usage
    mock_client.beta.threads.messages.create.assert_called_once_with(
        thread_id=thread_id,
        role="user",
        content=pytest.approx(call_args['messages'][1]['content'])
    )

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
