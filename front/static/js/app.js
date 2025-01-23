async function sendChat() {
    let userInput = document.getElementById("userInput").value.trim();
    if (!userInput) return; // Don't send empty messages

    // Add user's message to the chat area
    appendMessage(userInput, 'user-message');

    // Clear input after sending
    document.getElementById("userInput").value = '';

    try {
        // Start the POST request to send the message
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userInput })
        });

        let reader = response.body.getReader();
        let decoder = new TextDecoder();

        // Create a container for the bot's message
        let botMessageContainer = createMessageContainer('bot-message');

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            let chunk = decoder.decode(value, { stream: true });
            // Replace newline characters with HTML <br> tags
            chunk = chunk.replace(/\n/g, '<br>');
            botMessageContainer.innerHTML += chunk;
        }
        // Scroll the bot's message container into view
        botMessageContainer.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Error:', error);
    }
}

function createCustomDropdown(nativeSelect) {
    const container = document.createElement('div');
    container.className = 'custom-dropdown';

    const button = document.createElement('button');
    button.className = 'dropdown-toggle';
    button.innerHTML = `
        ${nativeSelect.options[0]?.text || 'Select LLM'}
        <svg class="dropdown-arrow" viewBox="0 0 24 24">
            <path d="M7 10l5 5 5-5z"/>
        </svg>
    `;

    const list = document.createElement('ul');
    list.className = 'dropdown-menu';

    // Création des options
    Array.from(nativeSelect.options).forEach(option => {
        const li = document.createElement('li');
        li.textContent = option.text;
        li.dataset.value = option.value;
        li.addEventListener('click', () => {
            nativeSelect.value = option.value;
            button.firstChild.textContent = option.text;
            container.classList.remove('open');
        });
        list.appendChild(li);
    });

    // Gestion du toggle
    button.addEventListener('click', (e) => {
        e.preventDefault();
        container.classList.toggle('open');
    });

    // Fermeture au clic externe
    document.addEventListener('click', (e) => {
        if (!container.contains(e.target)) {
            container.classList.remove('open');
        }
    });

    container.appendChild(button);
    container.appendChild(list);
    return container;
}


async function loadLLMOptions() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const llmSelector = document.getElementById('llmSelector');
    const selectorContainer = document.querySelector('.llm-selector-container');

    loadingIndicator.style.display = 'block';

    try {
        const response = await fetch('/get_llm_list');
        if (!response.ok) throw new Error("Failed to fetch LLM list");
        const data = await response.json();

        llmSelector.innerHTML = '';
        
        data.llms.forEach(llm => {
            const option = document.createElement('option');
            option.value = llm.id;
            option.textContent = llm.name;
            llmSelector.appendChild(option);
        });

        const customDropdown = createCustomDropdown(llmSelector);
        selectorContainer.appendChild(customDropdown);
        
        llmSelector.style.display = 'none';

    } catch (error) {
        console.error("Error loading LLM options:", error);
    } finally {
        loadingIndicator.style.display = 'none';
    }
}

function appendMessage(text, className) {
    let messageContainer = createMessageContainer(className);
    messageContainer.innerHTML = text.replace(/\n/g, '<br>'); // Replace newlines with <br>
    document.getElementById('chatArea').appendChild(messageContainer);
    messageContainer.scrollIntoView({ behavior: 'smooth' });
}

function createMessageContainer(className) {
    let div = document.createElement('div');
    div.classList.add('message', className);
    if (className === 'bot-message') {
        div.classList.add('fade-in');
    }
    document.getElementById('chatArea').appendChild(div);
    return div;
}
