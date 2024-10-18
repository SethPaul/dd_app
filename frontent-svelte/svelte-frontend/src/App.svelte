<script>
  import { onMount } from "svelte";
  import Chat from "./Chat.svelte";

  let groupSize = 0;
  let group = [];
  let isSetupComplete = false;
  let currentPerson = 0;
  let name = "";
  let role = "";
  let sessionId = "some-session-id"; // Adjust this with the actual session ID

  // Fetch session data when the app loads
  onMount(() => {
    fetchSession();
  });

  function fetchSession() {
    fetch(`/api/${sessionId}`)
      .then(response => response.json())
      .then(data => {
        group = data.users;
        // The dialogue from the session will be passed to the Chat component
        dialogue = data.dialogue || [];
        if (group.length > 0) {
          isSetupComplete = true;
        }
      })
      .catch(error => console.error("Error fetching session:", error));
  }

  function addPerson() {
    if (name && role) {
      group = [...group, { name, role }];
      name = "";
      role = "";
      currentPerson++;
      if (currentPerson >= groupSize) {
        // Setup complete
        isSetupComplete = true;
        sendRolesToBackend(group);  // Send roles to backend after setup
      }
    }
  }

  function sendRolesToBackend(group) {
    fetch(`/api/${sessionId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ users: group })
    })
    .then(response => response.json())
    .then(data => console.log("Roles setup response:", data))
    .catch(error => console.error("Error sending roles:", error));
  }
</script>

<main>
	<h2>Hi Saga Product Team!</h2>
	<h1>Welcome to The Cursed Idol of Black Hollow</h1>

	{#if !isSetupComplete}
		<div>
			<h2>Enter the number of people in your group:</h2>
			<input type="number" bind:value={groupSize} />

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
		text-align: center;
		padding: 1em;
		max-width: 240px;
		margin: 0 auto;
		background-color: gray;
	}

	h1 {	
		text-transform: uppercase;
	}
	h1, h2 {
		margin: 0;
		color: white;
	}
	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}
</style>
