<script>
  import { onMount } from "svelte";
  export let group = [];
  export let sessionId;
  let message = "";
  let selectedRole = "";
  let conversation = [];

  // Fetch the session dialogue on mount
  export let dialogue = [];
  onMount(() => {
    conversation = [...dialogue];
  });

  function sendMessage() {
    if (selectedRole && message) {
      let chatMessage = { user: selectedRole.toLowerCase(), msg: message }; // Changed to match your backend payload

      conversation = [...conversation, { role: selectedRole, message }];
      message = "";

      fetch(`https://jvgzcvmsoj.execute-api.us-west-2.amazonaws.com/Prod/putItemHandler`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(chatMessage) // Send the message in the expected format
      })
      .then(response => response.json())
      .then(data => {
        conversation = [...conversation, { role: "LLM", message: data.response }]; // Adjusted based on your backend response
      })
      .catch(error => console.error("Error:", error));
    }
  }
  
  function handleKeyPress(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();  // Prevents adding new line in textarea
      sendMessage();
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

  <div class="conversation">
    {#each conversation as msg}
      <p><strong>{msg.role}:</strong> {msg.message}</p>
    {/each}
  </div>
</div>

<style>

  .conversation {
    border: 1px solid #ccc;
    padding: 1rem;
    margin-top: 1rem;
    max-height: 300px;
    max-width: 300px;
    overflow-y: auto;
    border-radius: 10px;
    background-color: rgba(110, 211, 75, 0.3);
    color: rgba(0, 98, 152);
  }
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
