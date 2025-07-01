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
  let ws;
  let currentSentence = "";
  let currentStoryHTML = "";

  async function fetchSessionData(sessionId) {
    try {
      const response = await fetch(`${backendUrl}/${sessionId}`, {

        headers: { 
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Headers": "*",
        },
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
        currentStoryHTML = "Your party members are: <br><br>" + marked.parse(Object.values(data.user_bios).join('\n\n_____________________\n\n\n\n_____________________\n\n')) + "<br><br>" + currentStoryHTML;
        storyHtml = currentStoryHTML;
      }
      if (data.chat_history) {
        data.chat_history.forEach(message => {
          if (message.role === 'user') {
            currentStoryHTML += `<p><span class="user-name">${message.content.charAt(0).toUpperCase() + message.content.slice(1)}</span></p>`;
            storyHtml = currentStoryHTML;
          } else {
            currentStoryHTML += `<p><span class="ai-name">Dungeon Master: ${message.content.charAt(0).toUpperCase() + message.content.slice(1)}</span></p>`;
            storyHtml = currentStoryHTML;
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
    const urlParams = new URLSearchParams(window.location.search);
    const urlSessionId = urlParams.get('session');
    
    if (urlSessionId) {      
      await fetchSessionData(urlSessionId);
    }
    
    // Use existing session ID from URL if available, otherwise generate new one
    sessionId = urlSessionId || Math.random().toString(36).substring(2, 15);
    
    // Only update URL if we generated a new session ID
    if (!urlSessionId) {
      window.history.pushState({}, '', `/?session=${sessionId}`);
    }
    
    ws = new WebSocket(`wss://2myr6m0jz5.execute-api.us-west-1.amazonaws.com/dev?session_id=${sessionId}`);

    ws.onmessage = (event) => {
      const message = event.data;
      // Update story HTML with the new message
      if (message.includes("\n")) {
        currentStoryHTML += marked.parse(currentSentence + "<br>");
        currentSentence = "";
        storyHtml = currentStoryHTML;
        scrollToBottom();
      } else {
        currentSentence += message;
        storyHtml = currentStoryHTML + currentSentence;
      }

    };

    return () => {
      if (ws) ws.close();
    };
  });

  function toTitleCase(str) {
    return str.split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  }

  async function addPerson() {
    if (name && role) {
      group = [...group, { 
        name: toTitleCase(name), 
        role: toTitleCase(role) 
      }];
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

  function removePerson(index) {
    group = group.filter((_, i) => i !== index);
    if (group.length === 0) {
      isSetupComplete = false;
      currentPerson = 0;
      groupSize = 0;
    }
  }

  function editPerson(index) {
    const person = group[index];
    name = person.name;
    role = person.role;
    removePerson(index);
    currentPerson--;
    if (currentPerson < 0) currentPerson = 0;
  }

  let initialStoryHtml = `<p>The air is thick with fog as you and your fellow adventurers step into the village of Black Hollow. The sun barely penetrates the gloom, casting everything in an eerie, shadowy light. You can feel the eyes of the villagers on you—wary, fearful, but also hopeful.
    <br>
    <br>
    Lila, a young woman with worry etched on her face, approaches you. Her voice trembles as she speaks, "Thank the gods you've come! Our village is cursed. Ever since that idol was unearthed in the forest, darkness has fallen over us. Please, you must help us destroy it before it consumes us all."
    <br>
    <br>
    <hr>
    <p>
    Lila points to a dark, twisted path leading into the forest. The party begins down the path into the forest.  Before long the party comes across a group of shadowy figures chanting in the shadows off the path. It is unclear who they are or what they are doing.
    <br>
    <br>
    <hr>
    What shall you do?
    <hr>`;
    
  let storyHtml = currentStoryHTML = initialStoryHtml;

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
      
    } catch (error) {
      console.error("Error sending roles:", error);
    }
  }
  function scrollToBottom() {
    const storyContainer = document.querySelector('.story-container');
    if (storyContainer) {
      storyContainer.scrollTo({
      top: storyContainer.scrollHeight,
        behavior: 'smooth'  // Add smooth scrolling
      });
    }
  }
</script>

<svelte:head>
    <title>The Cursed Idol of Black Hollow</title>
</svelte:head> 

<div class="app-container">
  <main class="main-content">
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

  <aside class="party-panel">
    <div class="party-header">
      <h3>🎭 Party Management</h3>
    </div>
    
    <div class="party-content">
      {#if group.length > 0}
        <div class="party-members">
          <h4>Current Party ({group.length} members)</h4>
          {#each group as person, index}
            <div class="party-member">
              <div class="member-info">
                <span class="member-name">{person.name}</span>
                <span class="member-role">{person.role}</span>
              </div>
              <div class="member-actions">
                <button class="edit-btn" on:click={() => editPerson(index)} title="Edit">✏️</button>
                <button class="remove-btn" on:click={() => removePerson(index)} title="Remove">🗑️</button>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="empty-party">
          <p>No party members yet</p>
          <p>Add members to start your adventure!</p>
        </div>
      {/if}

      {#if isSetupComplete}
        <div class="party-stats">
          <h4>Party Stats</h4>
          <div class="stat-item">
            <span class="stat-label">Total Members:</span>
            <span class="stat-value">{group.length}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Session ID:</span>
            <span class="stat-value">{sessionId}</span>
          </div>
        </div>
      {/if}

      <div class="party-actions">
        {#if isSetupComplete}
          <button class="action-btn" on:click={() => { isSetupComplete = false; currentPerson = group.length; }}>
            Add More Members
          </button>
        {/if}
        <button class="action-btn secondary" on:click={() => { group = []; isSetupComplete = false; currentPerson = 0; groupSize = 0; }}>
          Reset Party
        </button>
      </div>
    </div>
  </aside>
</div>

<style>
  .app-container {
    display: flex;
    min-height: 100vh;
    background: #f5f5f5;
    font-family: 'Montserrat', sans-serif;
  }

  .main-content {
    flex: 1;
    padding: 2rem;
    background: #F3F4F4;
    margin: 1rem;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    text-align: center;
    overflow-y: auto;
  }

  .party-panel {
    width: 350px;
    background: white;
    border-left: 1px solid #e0e0e0;
    display: flex;
    flex-direction: column;
    box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
  }

  .party-header {
    background: linear-gradient(to right, rgba(255, 89, 90, 0.8), rgba(110, 211, 75, 0.8), rgba(30, 206, 202, 0.8), rgba(0, 98, 152, 0.8));
    color: white;
    padding: 1rem;
    text-align: center;
  }

  .party-header h3 {
    margin: 0;
    font-size: 1.2rem;
    font-weight: bold;
  }

  .party-content {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
  }

  .party-members h4 {
    color: rgba(0, 98, 152);
    margin-bottom: 1rem;
    font-size: 1rem;
  }

  .party-member {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
  }

  .member-info {
    display: flex;
    flex-direction: column;
    flex: 1;
  }

  .member-name {
    font-weight: bold;
    color: rgba(0, 98, 152);
    font-size: 0.9rem;
  }

  .member-role {
    color: #666;
    font-size: 0.8rem;
    font-style: italic;
  }

  .member-actions {
    display: flex;
    gap: 0.25rem;
  }

  .edit-btn, .remove-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 4px;
    font-size: 0.8rem;
  }

  .edit-btn:hover {
    background: #e3f2fd;
  }

  .remove-btn:hover {
    background: #ffebee;
  }

  .empty-party {
    text-align: center;
    color: #666;
    padding: 2rem 1rem;
  }

  .empty-party p {
    margin: 0.5rem 0;
  }

  .party-stats {
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #e0e0e0;
  }

  .party-stats h4 {
    color: rgba(0, 98, 152);
    margin-bottom: 0.75rem;
    font-size: 1rem;
  }

  .stat-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
  }

  .stat-label {
    color: #666;
  }

  .stat-value {
    font-weight: bold;
    color: rgba(0, 98, 152);
  }

  .party-actions {
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #e0e0e0;
  }

  .action-btn {
    width: 100%;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: bold;
    font-size: 0.85rem;
    background: linear-gradient(to right, rgba(255, 89, 90, 0.8), rgba(110, 211, 75, 0.8), rgba(30, 206, 202, 0.8), rgba(0, 98, 152, 0.8));
    color: white;
    transition: opacity 0.2s;
  }

  .action-btn:hover {
    opacity: 0.9;
  }

  .action-btn.secondary {
    background: #6c757d;
  }

  .container {
    background: linear-gradient(to right, rgba(255, 89, 90, 0.5), rgba(110, 211, 75, 0.5), rgba(30, 206, 202, 0.5), rgba(0, 98, 152, 0.5));
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

  /* Responsive design */
  @media (max-width: 768px) {
    .app-container {
      flex-direction: column;
    }
    
    .party-panel {
      width: 100%;
      max-height: 300px;
      border-left: none;
      border-top: 1px solid #e0e0e0;
    }
    
    .main-content {
      margin: 0.5rem;
    }
  }
</style>
