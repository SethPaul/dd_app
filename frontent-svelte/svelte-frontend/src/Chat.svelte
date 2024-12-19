<script>
  import { onMount } from "svelte";
  export let group = [];
  export let sessionId;
  let message = "";

  let ws;
  let selectedRole = "";
  let conversation = [];

  // Fetch the session dialogue on mount
  export let dialogue = [];
  onMount(() => {
    conversation = [...dialogue];
  });

  const backendUrl = "https://dd-api.ironoak.io";

  async function sendMessage() {
    if (selectedRole && message) {
      let chatMessage = { user: selectedRole.toLowerCase(), msg: message };
      message = "";


      try {
        const response = await fetch(`${backendUrl}/${sessionId}`, {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
          },
          body: JSON.stringify(chatMessage)
        });

        const responseText = await response.text();
        console.log(responseText);
        // conversation = [...conversation, { role: "LLM", message: responseText }];
      } catch (error) {
        console.error("Error:", error);
      }
    }
  }
  
  async function handleKeyPress(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      await sendMessage();
    }
  }
</script>

<div class="chat-section">
  <select class="role-selection" bind:value={selectedRole}>
    <option value="" disabled selected>Select Role</option>
    {#each group as person}
      <option value={person.role}>{person.name} ({person.role})</option>
    {/each}
  </select>

  <textarea class="chat-input" bind:value={message} 
    placeholder="Type your message" 
    rows="4" 
    style="width: 100%;"
    on:keydown={handleKeyPress}></textarea>
  <button on:click={sendMessage}>Send</button>

</div>

<style>


  .role-selection {
    border-radius: 10px;
    background: linear-gradient(to right, rgba(255, 89, 90, 0.3), rgba(110, 211, 75, 0.3), rgba(30, 206, 202, 0.3), rgba(0, 98, 152, 0.3));
  }
  .chat-input {
    border-radius: 10px;
    margin-top: 1rem;
    padding: 0.5rem;
    color: rgba(0, 98, 152);
  }
</style>
