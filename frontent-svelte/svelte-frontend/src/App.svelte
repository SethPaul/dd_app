<script>
  import { onMount } from "svelte";
  import { marked } from 'marked';
  import Chat from "./Chat.svelte";

  let groupSize = 0;
  let group = [];
  let isSetupComplete = false;
  let currentPerson = 0;
  let name = "";
  let role = "";
  let sessionId;

  // Generate random session ID and update URL
  onMount(() => {
    const pathSessionId = window.location.pathname.slice(1); // Remove leading slash
    if (pathSessionId) {
      sessionId = pathSessionId;
    } else {
      // Generate random session ID if none in URL
      sessionId = Math.random().toString(36).substring(2, 15);
      // Update URL without page reload
      window.history.pushState({}, '', `/${sessionId}`);
    }
  });

  async function addPerson() {
    if (name && role) {
      group = [...group, { name, role }];
      name = "";
      role = "";
      currentPerson++;
      if (currentPerson >= groupSize) {
        // Setup complete
        isSetupComplete = true;
        await sendRolesToBackend(group);  // Send roles to backend after setup
      }
    }
  }

  let storyHtml = `<p>The air is thick with fog as you and your fellow adventurers step into the village of Black Hollow. The sun barely penetrates the gloom, casting everything in an eerie, shadowy light. You can feel the eyes of the villagers on you—wary, fearful, but also hopeful.
    <br>
    <br>
    Lila, a young woman with worry etched on her face, approaches you. Her voice trembles as she speaks, "Thank the gods you've come! Our village is cursed. Ever since that idol was unearthed in the forest, darkness has fallen over us. Please, you must help us destroy it before it consumes us all."
    <br>
    <br>
She points to a dark, twisted path leading into the forest. The party begins down the path into the forest.  Before long the party comes across a group of shadowy figures chanting in the shadows off the path. It is unclear who they are or what they are doing.</p>`; // Initial story HTML

  const backendUrl = "https://dd-api.ironoak.io";

  async function sendRolesToBackend(group) {
    try {
      const response = await fetch(`${backendUrl}/${sessionId}`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Headers": "*",
        },
        body: JSON.stringify({ users: group }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const response_text = await response.text();
      console.log("Roles setup response:", response_text);
      
      // Parse the markdown response and convert to HTML
      if (response_text) {
        storyHtml = marked.parse(response_text);
      }
      
    } catch (error) {
      console.error("Error sending roles:", error);
    }
  }
</script>

<main>
	<h2>Hi 👋 Saga Product Team!</h2>
	<h1>Welcome to The Cursed Idol of Black Hollow <br> 🪄🌑🖤✨👻🌌</h1>
  <p>Session ID: {sessionId}</p>
  <br>
	<div class="story-container">
		{@html storyHtml}
	</div>
	<br>
	{#if !isSetupComplete}
		<div class="container">
			<h2>Enter the number of people in your group:</h2>
			<input class="member-number" type="number" bind:value={groupSize} />

			{#if groupSize > 0 && currentPerson < groupSize}
				<h2>Enter Name and Role for Person {currentPerson + 1}</h2>
				<input type="text" placeholder="Name" bind:value={name} />
				<input type="text" placeholder="Role" bind:value={role} />
				<button on:click={addPerson}>Add Person</button>
			{/if}
		</div>
	{:else}
		<!-- Once group setup is done, move to chat -->
		<Chat {group} sessionId={sessionId} />
	{/if}
</main>

<style>
  main {
    position: absolute;           /* Allows for positioning the element relative to the body */
    top: 50%;                    /* Position it 50% from the top */
    left: 50%;                   /* Position it 50% from the left */
    transform: translate(-50%, -50%); /* Shift the element back by half its height and width */
    text-align: center;          /* Center the text inside the main element */
    padding: 1em;                /* Add padding */
    max-width: 80vw;            /* Set max width */
    background: #F3F4F4;         /* Background color */
    font-family: 'Montserrat', sans-serif; /* Font family */
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Optional: adds a subtle shadow */
    border-radius: 10px;
    padding: 30px;
    width: 80%;
    margin: 0 auto;
  }
  .container {
    background: linear-gradient(to right, rgba(255, 89, 90, 0.5), rgba(110, 211, 75, 0.5), rgba(30, 206, 202, 0.5), rgba(0, 98, 152, 0.5)); /* Adjust alpha (0.7) as needed */
    border-radius: 10px;
    padding: 10px;
    margin-top: 50px;
  }
	h1 {	
		text-transform: uppercase;
	}
	h1, h2 {
		margin: 20px;
		color: rgba(0, 98, 152);
	}
  .member-number {
    margin-top: 20px;
    border-radius: 10px;
    width: 50px;
  }
	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}

  .story-container {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #ccc;
    padding: 10px;
    border-radius: 5px;
    background-color: #fff;
    text-align: left;
  }

  .story-container :global(p) {
    margin: 0 0 1em 0;
    line-height: 1.6;
  }

  .story-container :global(p:last-child) {
    margin-bottom: 0;
  }
</style>
