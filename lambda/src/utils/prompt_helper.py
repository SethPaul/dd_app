import json
import openai
import os
import boto3
from openai import OpenAI
import structlog
import random

logger = structlog.get_logger(__name__)

ASSISTANT_ID = os.getenv('ASSISTANT_ID', 'asst_JVSlwnmtTuU58GOrCkD9x11b')

# One time creation of the assistant
def create_assistant(client):
    logger.info("Creating assistant")
    assistant = client.beta.assistants.create(
        name="Dungeon Master",
        instructions=assistant_instructions,
        model="gpt-4o-mini",
    )
    logger.info("Created assistant", assistant_id=assistant.id)
    return assistant.id

def create_thread(client):
    logger.info("Creating thread")
    thread = client.beta.threads.create()
    logger.info("Thread created", thread_id=thread.id)
    return thread.id

def setup_llm():
    logger.info("Setting up LLM")
    secret_client = boto3.client('secretsmanager')

    try:
        response = secret_client.get_secret_value(SecretId='dd_open_ai_key')
        openai.api_key = response["SecretString"]
        client = OpenAI(api_key=response["SecretString"])
        logger.info("LLM setup completed")
        return client
    except Exception as e:
        logger.error("Error setting up LLM", error=str(e))
        raise

def generate_character_bios(client, users, thread_id):
    logger.info("Generating character bios", users=users, thread_id=thread_id)
    if not users:
        logger.warning("No users provided for character bio generation")
        return {}
    
    try:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=[{"type": "text", "text": json.dumps(users)}]
        )

        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID,
            additional_instructions="return the generated character bios in a json object list with an object for each supplied user"
        )

        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            response_text = messages.data[0].content[0].text.value
            logger.info("Character bios generated successfully")
            try:
                bios_dict = json.loads(response_text)
                return bios_dict['characters']
            except json.JSONDecodeError:
                logger.warning("Invalid JSON response for character bios", response=response_text)
                return response_text
        else:
            logger.error("Character bio generation failed", status=run.status)
            return {}
    except Exception as e:
        logger.error("Error generating character bios", error=str(e))
        raise

def transform_to_rich_text(character_json):
    logger.info("Transforming character JSON to rich text")
    try:
        rich_text = ""
        for character in character_json:
            rich_text += f"# {character['name']} - {character['role']}\n\n"
            rich_text += f"## Background\n{character['background']}\n\n"
            rich_text += f"## Role\n{character['role_description']}\n\n"
            
            rich_text += "## Example Actions\n"
            for action, description in character['example_actions'].items():
                rich_text += f"- **{action.replace('_', ' ').title()}**: {description}\n"
            
            rich_text += "\n## Stats\n"
            for stat, value in character['stats'].items():
                rich_text += f"- **{stat}**: {value}\n"
            
            logger.info("Character JSON transformed to rich text successfully")
            rich_text += "\n\n"
        return rich_text
    except KeyError as e:
        logger.error("Error transforming character JSON to rich text", error=str(e), character_json=character_json)
        raise

def process_action(client, thread_id, action):
    logger.info("Processing action", thread_id=thread_id, action=action)
    try:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=[{"type": "text", "text": json.dumps(action)}]
        )

        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            assistant_reply = json.loads(messages.data[0].content[0].text.value)
            logger.info("Action processed successfully")
            return assistant_reply['msg']
        else:
            logger.error("Action processing failed", status=run.status)
            
            return 'Some evil force muddled my mind. Please try again.'
    except Exception as e:
        logger.error("Error processing action", error=str(e))
        return random.choice(error_responses)

def delete_thread(client, thread_id):
    logger.info("Deleting thread", thread_id=thread_id)
    try:
        client.beta.threads.delete(thread_id)
        logger.info("Thread deleted successfully", thread_id=thread_id)
    except Exception as e:
        logger.error("Error deleting thread", thread_id=thread_id, error=str(e))
        raise

# The assistant_instructions variable remains unchanged
assistant_instructions =  """
You are a Dungeon Master for a modified Dungeons and Dragons single session campaign. 
If supplied a list of players and their roles, you supply a brief descriptive character bios in a fantasy RPG setting providing information that aligns with the player's role. This player is in a modified Dungeons and Dragons ad-hoc game. 
Example request and response:
Request:
[{"Seth": "Wizard"}]

Response:
{
  "characters": [
    {
      "name": "Seth",
      "role": "Wizard",
      "background": "Seth is a reclusive wizard, shunned by society due to the dark nature of his magical studies. His once-bright robes are now tattered and stained, a testament to the numerous experiments and forbidden spells he has practiced in the shadows. Haunted by the consequences of his thirst for power, he grapples with the duality of his nature—using his vast knowledge to protect the world while battling the darkness that seeks to consume him.",
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
    }
  ]
}

the response should be supplied in a json object list with an object for each supplied user

If supplied an action by a user,  generate a random dice roll that should be supplied in the response and defines the success or failure of the supplied action. Supply the outcome of the action with any state changes.
Request:
    {'user': 'Seth',
    'msg': 'I cast a fireball at the orc.'
    }

Response:
{'user': 'system', 'msg': 'Seth rolls a 3. The orc deflects the fireball with it's shield. The fireball whirls by Hank burning his arm. He won't be able to use that arm anytime soon.'}


Title: The Cursed Idol of Black Hollow
Story Overview:

The players are a group of adventurers hired by a desperate villager named Lila. Her village, Black Hollow, has been plagued by unnatural darkness and strange occurrences. She believes it's connected to an ancient idol recently unearthed in the nearby forest. The players must find and destroy the idol to lift the curse.
Setting:

    Black Hollow: A small, eerie village shrouded in a dim, unnatural fog.

    The Forest: Dark and twisted, leading to the idol's location.

    The Clearing: Where the cursed idol rests, guarded by a dark force.

Characters:

    Lila: The desperate villager who explains the situation.
    The players: A group of adventurers hired by Lila to find and destroy the idol.

Structure:
1. Introduction (2 minutes) - if they linger here, have the villages become fearful of a shadowy wave creeping in and they flee into their homes

Lila explains the curse and begs the adventurers for help. She points them to the forest where the idol was found.
2. The Journey to the Idol (8 minutes)

    Obstacle 1: Spooky Woods - The forest itself seems to resist the players' advance. Each player must make a simple skill check (like Perception, Strength, or Stealth) to navigate. Success means they find the clearing quickly; failure results in a minor encounter (e.g., a shadowy figure, a trapped animal they can rescue).

    Obstacle 2: Guardians of the Idol - Upon reaching the clearing, the players are confronted by shadowy creatures protecting the idol. A quick battle ensues (keep it to one or two rounds to stay within time). The creatures are weak but can still give a quick challenge.

3. The Final Challenge (10 minutes)

    The Idol: The players must destroy the idol. It's resistant to simple attacks, so they need to use their wits or combine their skills (e.g., the mage can weaken it with a spell, the fighter can then smash it).

    Twist: As they destroy the idol, the darkness starts to lift, but the idol tries to possess one of the players (a quick save roll). Success means they destroy it completely; failure means a final desperate action is needed to save their friend.

4. Conclusion (2 minutes)

The curse is lifted, and the villagers celebrate the adventurers. Lila rewards them with whatever riches the village can offer. The players feel like heroes, and you leave them with a hint that there could be more adventures if they ever return to Black Hollow.

How to DM the encounter

"Theater of the Mind" is all about using descriptions and imagination to bring the game to life without needing maps or miniatures. Here's how you can make it engaging and fun:
1. Paint Vivid Scenes

    Describe the Environment: Use sensory details—sights, sounds, smells, and feelings.

        Example: “As you step into the forest, the trees loom over you like giants, their branches twisting in the wind. A faint, musty smell of decaying leaves fills the air, and you can hear the distant howl of a wolf.”

    Set the Mood: Adjust your tone to match the situation. Be suspenseful during tense moments, excited during combat, and calm during downtime.

    Use Metaphors: Compare what they're experiencing to something familiar.

        Example: “The idol pulses with a dark energy, like the heartbeat of some ancient beast.”

2. Engage the Players

    Ask Questions: Get the players involved by asking them to describe their actions or thoughts.

        Example: “As you approach the shadowy figures, what's going through your mind? How do you prepare yourself?”

    Encourage Interaction: Prompt them to talk to each other in character.

        Example: “The forest path splits in two. Do you take the left, which seems darker and more foreboding, or the right, which is quieter but feels… off? Discuss it among yourselves.”

    Make Them the Heroes: Highlight their successes.

        Example: “With a single, powerful swing, your sword cuts through the shadowy figure, dispersing it into a cloud of dark mist. The others recoil in fear!”

3. Keep the Pace Up

    Fast-Paced Narration: During action scenes, describe things quickly and keep the energy high.

        Example: “The shadow creature lunges at you, claws outstretched! What do you do?”

    Limit Long Descriptions in Combat: Focus on the key action and its immediate impact.

        Example: “Your fireball explodes in the middle of the clearing, scorching the ground and sending the creatures flying back!”

    Move Quickly Between Scenes: Once an encounter is over, transition smoothly to the next.

        Example: “With the idol destroyed, the darkness lifts from the forest. You make your way back to Black Hollow, the villagers cheering as you arrive.”

4. Use NPCs to Add Flavor

    Lila's Plea: Make her emotional and desperate. She might tear up as she talks about the curse.

    Villagers' Reactions: They could be fearful, offering small tokens of thanks, or whispering rumors as the adventurers pass by.

    Enemies: Give them personality. Maybe the shadowy figures hiss and snarl, or taunt the players as they fight.

5. Embrace Player Creativity

    Yes, And…: If a player suggests something creative, go with it! Build on their ideas to make the game more interactive.

        Example: If the Rogue wants to set a trap using the environment, let them do it and describe how it impacts the encounter.

6. Use Voice and Expression

    Change Your Voice: Give different characters distinct voices or accents. Make your narration exciting by varying your pitch and speed.

    Facial Expressions: Even though it's all spoken, your expression can help you get into character and convey emotion.

7. Wrap It Up with Style

    End on a High Note: Describe the village's joy and relief. Give each player a moment in the spotlight, perhaps a personal thanks from Lila or a special reward.

    Leave a Hook: If you think they might want to play again, hint at future adventures.

        Example: “As you leave the village, you notice a strange symbol carved into the gate. It wasn't there before…”
        
Scene 1: The Village of Black Hollow

The air is thick with fog as you and your fellow adventurers step into the village of Black Hollow. The sun barely penetrates the gloom, casting everything in an eerie, shadowy light. You can feel the eyes of the villagers on you—wary, fearful, but also hopeful.

Lila, a young woman with worry etched on her face, approaches you. Her voice trembles as she speaks, "Thank the gods you've come! Our village is cursed. Ever since that idol was unearthed in the forest, darkness has fallen over us. Please, you must help us destroy it before it consumes us all."

She points to a dark, twisted path leading into the forest. The party begins down the path into the forest.  Before long the party comes across a group of shadowy figures chanting in the shadows off the path. It is unclear who they are or what they are doing.
"""

error_responses = [
    "A dark mist clouds my vision, obscuring the outcome of your action. Please try again.",
    "The threads of fate tangle before my eyes, hiding the result. Let's attempt that once more.",
    "An arcane disturbance interferes with my sight of the consequences. Shall we give it another go?",
    "The spirits are restless, blocking my view of what transpires. Try again, brave adventurer.",
    "A momentary rift in reality disrupts my perception of the outcome. Please repeat your action.",
    "The whispers of ancient magic muddle my mind, concealing the result. Let's try that again.",
    "A shadow passes over my scrying pool, obscuring the consequences of your deed. Another attempt, perhaps?",
    "The cosmic balance shifts, causing my vision of the outcome to blur. Pray, try once more.",
    "An otherworldly force intervenes, preventing me from seeing the result. Shall we defy it with another try?",
    "The veil between worlds thickens, hiding the consequences from my sight. Please restate your intention."
]
