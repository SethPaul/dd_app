import json
from utils.prompt_helper import generate_character_bios, setup_llm
import pytest

@pytest.fixture
def llm_prep(mock_toggle):
    if mock_toggle:
        pytest.skip("This test requires real services")
    return setup_llm()

def test_generate_character_bios(mock_toggle, llm_prep):
    if mock_toggle:
        pytest.skip("This test requires real services")
    
    # Arrange
    users = [
        {'name': 'Seth', 'role': 'Wizard'},
        {'name': 'Hank', 'role': 'Warrior'}
    ]

    # Act
    result = generate_character_bios(llm_prep, users)

    # Assert
    assert isinstance(result, dict)
    assert "Seth" in result
    assert "Hank" in result
    

def test_generate_character_bios_fallback(llm_prep):
    # Arrange
    users = [
        {'name': 'Seth', 'role': 'Wizard'},
        {'name': 'Hank', 'role': 'Warrior'}
    ]

    # Act
    result = generate_character_bios(users)

    # Assert
    assert isinstance(result, dict)
    assert "Seth" in result
    assert "Hank" in result

def test_generate_character_bios_single_user(llm_prep):
    # Arrange
    users = [{'name': 'Lila', 'role': 'Rogue'}]
    # Act
    result = generate_character_bios(users)

    # Assert
    assert isinstance(result, dict)
    assert len(result) == 1
    assert "Lila" in result
