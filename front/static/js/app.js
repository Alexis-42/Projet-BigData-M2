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

async function loadLLMOptions() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const llmSelector = document.getElementById('llmSelector');

    // Show loading indicator
    loadingIndicator.style.display = 'block';

    if (llmSelector.innerHTML !== ''){
        try {
            const response = await fetch('/get_llm_list');
            if (!response.ok) {
                throw new Error("Failed to fetch LLM list");
            }
            const data = await response.json();

            // Clear existing options
            llmSelector.innerHTML = '';

            // Add new options from the API
            data.llms.forEach(llm => {
                const option = document.createElement('option');
                option.value = llm.id;
                option.textContent = llm.name;
                llmSelector.appendChild(option);
            });
        } catch (error) {
            console.error("Error loading LLM options:", error);
        } finally {
            // Hide loading indicator
            loadingIndicator.style.display = 'none';
        }
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
