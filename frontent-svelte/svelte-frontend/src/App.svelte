<script>
  import { onMount } from "svelte";
  import { marked } from 'marked';

  let groupSize = 0;
  let group = [];
  let isSetupComplete = false;
  let currentPerson = 0;
  let name = "";
  let role = "";
  let sessionId;

  // Add new websocket-related state
  let wsMessages = [];
  let ws;
  let user_bios = [];

  let isResizing = false;
  let startX;
  let startWidth;

  let message = "";
  let selectedName = "";

  async function fetchSessionData(sessionId) {
    try {
      const response = await fetch(`https://bx9qs5sk31.execute-api.us-west-1.amazonaws.com/dev/${sessionId}`, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Headers": "*",
        }
      });
      if (!response.ok) {
        throw new Error('Session not found');
      }
      const data = await response.json();
      // Update storyHtml with previous messages instead of wsMessages
      if (data.users) {
        group = data.users;
        isSetupComplete = true; 
      }
      if (data.user_bios) {
        user_bios = Object.values(data.user_bios).join('\n\n_____________________\n\n\n\n_____________________\n\n');
      }
      if (data.chat_history) {
        data.chat_history.forEach(message => {
          if (message.role === 'user') {
            storyHtml += `<p><span class="user-name">${message.content.charAt(0).toUpperCase() + message.content.slice(1)}</span></p>`;
          } else {
            storyHtml += `<p><span class="ai-name">Dungeon Master: ${message.content.charAt(0).toUpperCase() + message.content.slice(1)}</span></p>`;
          }
          scrollToBottom();
        });
      }
      scrollToBottom();
    } catch (error) {
      console.error('Error fetching session:', error);
    }
  }

  // Generate random session ID and update URL
  onMount(async () => {
    // Check URL search params
    const urlParams = new URLSearchParams(window.location.search);
    const urlSessionId = urlParams.get('session');
    
    if (urlSessionId) {
      sessionId = urlSessionId;
      await fetchSessionData(sessionId);
    } else {
      // Generate random session ID if none exists
      sessionId = Math.random().toString(36).substring(2, 15);
      // Update URL without page reload
      window.history.pushState({}, '', `/?session=${sessionId}`);
    }

    // Setup WebSocket connection
    ws = new WebSocket(`wss://2myr6m0jz5.execute-api.us-west-1.amazonaws.com/dev?session_id=${sessionId}`);
    
    ws.onmessage = (event) => {
      const message = event.data;
      // Update story HTML with the new message
      storyHtml += message;
      scrollToBottom();
    };

    return () => {
      if (ws) ws.close();
    };
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
      
      // Update the story HTML with the received data
      if (response_text) {
        user_bios = response_text;
      }
      
    } catch (error) {
      console.error("Error sending roles:", error);
    }
  }

  // Add this function to handle scrolling
  function scrollToBottom() {
    const storyContainer = document.querySelector('.story-container');
    if (storyContainer) {
      storyContainer.scrollTop = storyContainer.scrollHeight ;
    }
  }

  function startResize(e) {
    isResizing = true;
    startX = e.clientX;
    startWidth = document.querySelector('.sidebar').offsetWidth;
    
    // Add event listeners for dragging
    document.addEventListener('mousemove', resize);
    document.addEventListener('mouseup', stopResize);
  }

  function resize(e) {
    if (!isResizing) return;
    
    const width = startWidth + (e.clientX - startX);
    const sidebar = document.querySelector('.sidebar');
    const main = document.querySelector('main');
    
    // Set min and max widths
    if (width > 100 && width < window.innerWidth * 0.8) {
      sidebar.style.width = `${width}px`;
      main.style.marginLeft = `${width}px`;
      main.style.width = `calc(100% - ${width}px)`;
    }
  }

  function stopResize() {
    isResizing = false;
    document.removeEventListener('mousemove', resize);
    document.removeEventListener('mouseup', stopResize);
  }

  async function sendMessage() {
    if (selectedName && message) {
      let chatMessage = { user: selectedName, msg: message };

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
        const response_text = await response.text();
        scrollToBottom();
        console.log("Chat response:", response_text);
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

<div class="layout">
  <aside class="sidebar">
    <h3>Party</h3>
    {#if user_bios.length > 0}
      <div class="party-bios">
        {@html marked(user_bios)}
      </div>
    {/if}
    <div class="message-container">
      {#each wsMessages as message}
        <div class="message">
          <span class="timestamp">{new Date(message.timestamp).toLocaleTimeString()}</span>
          <p>{message.content}</p>
        </div>
      {/each}
    </div>
    <div class="resize-handle" on:mousedown={startResize}></div>
  </aside>

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
      <div class="chat-controls">
        <select class="role-selection" bind:value={selectedName}>
          <option value="" disabled selected>Select Role</option>
          {#each group as person}
            <option value={person.name}>{person.name} ({person.role})</option>
          {/each}
        </select>

        <textarea 
          class="chat-input" 
          bind:value={message} 
          placeholder="Type your message" 
          rows="4" 
          on:keydown={handleKeyPress}
        ></textarea>
        <button on:click={sendMessage}>Send</button>
      </div>
    {/if}
  </main>
</div>

<style>
  main {
    width: calc(100% - 300px);  /* Start with a reasonable default width */
    margin-left: 300px;         /* Match the sidebar width */
    padding: 30px;
    text-align: center;
    background: #F3F4F4;
    font-family: 'Montserrat', sans-serif;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    border-radius: 10px;
    height: 100vh;
    overflow-y: auto;
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
			margin: 0 0 0 300px;      /* Only set left margin */
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
    scroll-behavior: smooth;
  }

  .story-container :global(p) {
    margin: 0 0 1em 0;
    line-height: 1.6;
  }

  .story-container :global(p:last-child) {
    margin-bottom: 0;
  }

  /* Add new sidebar styles */
  .layout {
    display: flex;
    width: 100%;
    height: 100vh;
    overflow: hidden;
  }

  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    width: 300px;
    height: 100vh;
    background: #2c3e50;
    color: white;
    padding: 1em;
    box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
    overflow-y: auto;
  }

  .resize-handle {
    position: absolute;
    right: 0;
    top: 0;
    width: 4px;
    height: 100%;
    background: rgba(255, 255, 255, 0.1);
    cursor: ew-resize;
  }

  .resize-handle:hover {
    background: rgba(255, 255, 255, 0.3);
  }

  /* Add a style to prevent text selection while resizing */
  .layout.resizing {
    user-select: none;
  }

  .message-container {
    height: calc(100vh - 4em);
    overflow-y: auto;
    padding-right: 10px;
  }

  .message {
    background: rgba(255, 255, 255, 0.1);
    margin: 10px 0;
    padding: 10px;
    border-radius: 5px;
  }

  .timestamp {
    font-size: 0.8em;
    color: #95a5a6;
  }

  .message p {
    margin: 5px 0 0 0;
  }

  .party-bios {
    padding: 10px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }

  .bio-entry {
    margin: 0.5em 0;
  }

  .bio-entry h4 {
    margin: 0;
    color: #ecf0f1;
  }

  .bio-entry p {
    margin: 0.2em 0 0 0;
    font-size: 0.9em;
    color: #bdc3c7;
  }

  .story-container :global(.user-name) {
    color: #2c3e50;
    font-weight: bold;
  }

  .story-container :global(.ai-name) {
    color: #3498db;
    font-weight: bold;
  }

  .chat-controls {
    margin-top: 20px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 20px;
  }

  .chat-input {
    border-radius: 10px;
    padding: 0.5rem;
    color: rgba(0, 98, 152);
    width: 100%;
  }

  .role-selection {
    border-radius: 10px;
    padding: 0.5rem;
    background: linear-gradient(to right, rgba(255, 89, 90, 0.3), rgba(110, 211, 75, 0.3), rgba(30, 206, 202, 0.3), rgba(0, 98, 152, 0.3));
  }

  button {
    padding: 10px 20px;
    border-radius: 10px;
    background: rgba(0, 98, 152, 0.8);
    color: white;
    border: none;
    cursor: pointer;
  }

  button:hover {
    background: rgba(0, 98, 152, 1);
  }
</style>
