import json
from handler import generate_character_bios
from unittest.mock import patch, MagicMock


def test_generate_character_bios():
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
    

def test_generate_character_bios_fallback():
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

def test_generate_character_bios_single_user():
    # Arrange
    users = [{'name': 'Lila', 'role': 'Rogue'}]
    # Act
    result = generate_character_bios(users)

    # Assert
    assert isinstance(result, dict)
    assert len(result) == 1
    assert "Lila" in result

