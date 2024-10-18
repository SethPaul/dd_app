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
  // onMount(() => {
  //   fetchSession();
  // });

  // function fetchSession() {
  //   fetch(`https://jvgzcvmsoj.execute-api.us-west-2.amazonaws.com/Prod/`)
  //     .then(response => response.json())
  //     .then(data => {
  //       group = data.users;
  //       // The dialogue from the session will be passed to the Chat component
  //       dialogue = data.dialogue || [];
  //       if (group.length > 0) {
  //         isSetupComplete = true;
  //       }
  //     })
  //     .catch(error => console.error("Error fetching session:", error));
  // }

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
    fetch(`https://jvgzcvmsoj.execute-api.us-west-2.amazonaws.com/Prod/putItemHandler`, {
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
	<h2>Hi 👋 Saga Product Team!</h2>
	<h1>Welcome to The Cursed Idol of Black Hollow <br> 🪄🌑🖤✨👻🌌</h1>

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
    max-width: 240px;            /* Set max width */
    background: #F3F4F4;         /* Background color */
    font-family: 'Montserrat', sans-serif; /* Font family */
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Optional: adds a subtle shadow */
    border-radius: 10px;
    padding: 30px;
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
</style>
