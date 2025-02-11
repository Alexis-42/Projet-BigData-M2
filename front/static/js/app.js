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
    updateParams()
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
        const bufferSize = 3;
        let inReadmeSection = false;
        const botMessageContainer = createMessageContainer('bot-message');
        let buffer = [];
        let readmeBuffer = [];
        let readmeState = 'OUTSIDE'; // 'OUTSIDE', 'START_FOUND', 'INSIDE'
        let partialMarker = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            buffer.push(chunk);
            let content = buffer.join('');
            
            // Gestion des marqueurs découpés
            while (true) {
                if (readmeState === 'OUTSIDE') {
                    const startIndex = content.indexOf('### README START ###');
                    if (startIndex > -1) {
                        // Ajouter tout le contenu avant le marqueur
                        botMessageContainer.innerHTML += content.substring(0, startIndex);
                        
                        // Initialiser le buffer README
                        readmeState = 'INSIDE';
                        content = content.substring(startIndex + '### README START ###'.length);
                        buffer = [content];
                        break;
                    } else {
                        // Vérifier si le chunk se termine par un début partiel de marqueur
                        const partial = content.slice(-'### README START ###'.length);
                        const markerIndex = '### README START ###'.indexOf(partial);
                        if (markerIndex > 0) {
                            partialMarker = partial;
                            content = content.slice(0, -partial.length);
                            readmeState = 'START_FOUND';
                        }
                        
                        // Ajouter tout le contenu normal
                        botMessageContainer.innerHTML += content;
                        buffer = [];
                        break;
                    }
                }
                else if (readmeState === 'START_FOUND') {
                    content = partialMarker + content;
                    partialMarker = '';
                    readmeState = 'OUTSIDE';
                    continue;
                }
                else if (readmeState === 'INSIDE') {
                    const endIndex = content.indexOf('### README END ###');
                    if (endIndex > -1) {
                        // Ajouter le contenu README final
                        readmeBuffer.push(content.substring(0, endIndex));
                        displayReadmeContent(readmeBuffer.join(''));
                        
                        // Reprendre le traitement normal
                        readmeState = 'OUTSIDE';
                        content = content.substring(endIndex + '### README END ###'.length);
                        buffer = [content];
                        readmeBuffer = [];
                        continue;
                    } else {
                        // Vérifier la fin partielle du marqueur
                        const partialEnd = content.slice(-'### README END ###'.length);
                        const markerIndex = '### README END ###'.indexOf(partialEnd);
                        if (markerIndex > 0) {
                            readmeBuffer.push(content.slice(0, -partialEnd.length));
                            partialMarker = partialEnd;
                            buffer = [];
                            break;
                        } else {
                            readmeBuffer.push(content);
                            buffer = [];
                            break;
                        }
                    }
                }
            }

            // Gestion du bufferSize pour le contenu normal
            if (readmeState === 'OUTSIDE' && buffer.length >= bufferSize) {
                botMessageContainer.innerHTML += buffer.join('');
                buffer = [];
                void botMessageContainer.offsetHeight;
            }
        }
        
        if (buffer.length > 0) {
            botMessageContainer.innerHTML += buffer.join('');
        }

        const { readmeContent, remainingText } = extractReadmeContent(botMessageContainer.textContent);
        if (readmeContent) {
            displayReadmeContent(readmeContent);
            botMessageContainer.textContent = remainingText.trim();
        }

        botMessageContainer.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Error:', error);
    }
}

function extractReadmeContent(responseText) {
    const readmeStartMarker = "### README START ###";
    const readmeEndMarker = "### README END ###";
    const startIndex = responseText.indexOf(readmeStartMarker);
    const endIndex = responseText.indexOf(readmeEndMarker);

    if (startIndex !== -1 && endIndex !== -1) {
        const readmeContent = responseText.substring(
            startIndex + readmeStartMarker.length, 
            endIndex
        ).trim();
        // Retirer la section README du texte original
        const remainingText = responseText.substring(0, startIndex) + 
                              responseText.substring(endIndex + readmeEndMarker.length);
        return { readmeContent, remainingText };
    }
    return { readmeContent: "", remainingText: responseText };
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
    const selectorContainer = document.querySelector('llm-selector-container');

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
