import hljs from 'https://cdn.jsdelivr.net/npm/highlight.js@11.7.0/+esm';
import { marked } from 'https://cdn.jsdelivr.net/npm/marked@11.1.1/+esm';

document.addEventListener('DOMContentLoaded', function () {
    console.log("Le DOM est chargé !");
    console.log("marked est chargé :", !!marked);
    initApp();
});

function initApp() {
    console.log("L'application est initialisée !");

    marked.setOptions({
        silent: false,
        highlight: function(code, lang) {
            return hljs.highlightAuto(code).value;
        }
    });

    loadLLMOptions();

    document.getElementById('docCount').addEventListener('change', updateParams);
    document.getElementById('similarity').addEventListener('input', updateParams);
    document.getElementById('applyParams').addEventListener('click', applyRAGParams);

    const sendButton = document.getElementById('sendButton');
    sendButton.addEventListener('click', sendChat);
    updateParams();
}

function updateParams() {
    ragParams.docCount = parseInt(document.getElementById('docCount').value);
    ragParams.similarityThreshold = parseFloat(document.getElementById('similarity').value);
    document.getElementById('similarityValue').textContent = ragParams.similarityThreshold.toFixed(1);
}

function applyRAGParams() {
    console.log('Paramètres RAG mis à jour:', ragParams);
}

let ragParams = {
    docCount: 3, // subject to changes
    similarityThreshold: 0.7 // subject to changes
};

async function sendChat() {
    const userInput = document.getElementById("userInput").value.trim();
    if (!userInput) return;

    appendMessage(userInput, 'user-message');
    document.getElementById("userInput").value = '';
    document.querySelector('.llm-selector-container').style.display = 'none';

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: userInput,
                rag_params: {
                    doc_count: ragParams.docCount,
                    similarity: ragParams.similarityThreshold
                }
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        const botMessageContainer = createMessageContainer('bot-message');
        let buffer = [];
        const bufferSize = 3;

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            buffer.push(chunk);
            
            if (buffer.length >= bufferSize) {
                botMessageContainer.innerHTML += buffer.join('');
                buffer = [];
                void botMessageContainer.offsetHeight;
            }
        }
        
        if (buffer.length > 0) {
            botMessageContainer.innerHTML += buffer.join('');
        }

        document.querySelector('.llm-selector-container').style.display = 'flex';

        const readmeContent = extractReadmeContent(botMessageContainer.textContent);
        if (readmeContent) displayReadmeContent(readmeContent);
        
        botMessageContainer.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Error:', error);
        document.querySelector('.llm-selector-container').style.display = 'flex';
    }
}

function extractReadmeContent(responseText) {
    const readmeStartMarker = "### README START ###";
    const readmeEndMarker = "### README END ###";
    const startIndex = responseText.indexOf(readmeStartMarker);
    const endIndex = responseText.indexOf(readmeEndMarker);

    if (startIndex !== -1 && endIndex !== -1) {
        return responseText.substring(startIndex + readmeStartMarker.length, endIndex).trim();
    }
    return "";
}

function displayReadmeContent(content, nom_repo="README") {
    const cleanedContent = content.replace(/\\"/g, '"').replace(/^[ \t]+/gm, '');
    const readmeList = document.getElementById('readmeList');
    readmeList.innerHTML = '';

    const readmeItem = document.createElement('div');
    readmeItem.className = 'readme-item';
    
    const header = document.createElement('div');
    header.className = 'readme-header';
    header.innerHTML = `
        <span>📄 README</span>
        <span class="toggle-arrow">▼</span>
    `;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'readme-content';
    contentDiv.innerHTML = marked.parse(cleanedContent);

    header.addEventListener('click', () => {
        const isExpanded = contentDiv.style.display === 'block';
        contentDiv.style.display = isExpanded ? 'none' : 'block';
        header.querySelector('.toggle-arrow').textContent = isExpanded ? '▼' : '▲';
        readmeItem.classList.toggle('expanded', !isExpanded);
    });

    readmeItem.appendChild(header);
    readmeItem.appendChild(contentDiv);
    readmeList.appendChild(readmeItem);

    if (typeof hljs !== 'undefined') {
        contentDiv.querySelectorAll('pre code').forEach(hljs.highlightElement);
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

    button.addEventListener('click', (e) => {
        e.preventDefault();
        container.classList.toggle('open');
    });

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
    messageContainer.innerHTML = text.replace(/\n/g, '<br>');
    document.getElementById('chatArea').appendChild(messageContainer);
    messageContainer.scrollIntoView({ behavior: 'smooth' });
}

function createMessageContainer(className) {
    let div = document.createElement('div');
    div.classList.add('message', className);
    if (className === 'bot-message') {
        const avatar = document.createElement('div');
        avatar.className = 'bot-avatar';
        div.prepend(avatar);
    }
    document.getElementById('chatArea').appendChild(div);
    return div;
}
