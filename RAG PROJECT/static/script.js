document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const fileInput = document.getElementById('file-input');
    const chatMessages = document.getElementById('chat-messages');
    const chatHistoryList = document.getElementById('chat-history');
    const sourceDocumentsList = document.getElementById('source-documents');
    const themeToggleBtn = document.getElementById('theme-toggle');
    const userInputField = document.getElementById('user-input');
    const sendButton = document.querySelector('.send-btn');
    const sidebarToggleBtn = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const chatArea = document.querySelector('.chat-area');
    const fileNameSpan = document.getElementById('file-name');
    const fileInputBtn = document.getElementById('file-input-button'); // Changed to match the new div
    const uploadIcon = document.getElementById('upload-icon');

    let startTime; // Variable to store the start time

    // Declare processingMessageElement, loadingBarContainer, and loadingBar globally
    let processingMessageElement;
    let loadingBarContainer;
    let loadingBar;

    // Function to toggle sidebar
    function toggleSidebar() {
        sidebar.classList.toggle('collapsed');
        chatArea.classList.toggle('sidebar-collapsed');

        // Update chat input form width
        updateChatInputFormWidth();

        // Change the icon and tooltip based on sidebar state
        if (sidebar.classList.contains('collapsed')) {
            sidebarToggleBtn.querySelector('i').classList.remove('fa-chevron-left');
            sidebarToggleBtn.querySelector('i').classList.add('fa-chevron-right');
            sidebarToggleBtn.setAttribute('aria-label', 'Expand Sidebar');

            
        } else {
            sidebarToggleBtn.querySelector('i').classList.remove('fa-chevron-right');
            sidebarToggleBtn.querySelector('i').classList.add('fa-chevron-left');
            sidebarToggleBtn.setAttribute('aria-label', 'Collapse Sidebar');

        }
    }

    // Function to update chat input form width based on sidebar state and screen size
    function updateChatInputFormWidth() {
        const sidebarWidth = sidebar.offsetWidth;
        const screenWidth = window.innerWidth;

        if (screenWidth > 768) {
            if (sidebar.classList.contains('collapsed')) {
                chatArea.style.marginLeft = '0';
                chatArea.style.maxWidth = '100%';
            } else {
                chatArea.style.marginLeft = `${sidebarWidth}px`;
                chatArea.style.maxWidth = `calc(100% - ${sidebarWidth}px)`;
            }
        } else {
            chatArea.style.marginLeft = '0';
            chatArea.style.maxWidth = '100%';
        }
    }

    sidebarToggleBtn.addEventListener('click', toggleSidebar);

    // Call updateChatInputFormWidth on window resize
    window.addEventListener('resize', updateChatInputFormWidth);

    // Call updateChatInputFormWidth initially to set the initial width
    updateChatInputFormWidth();

    function createLoadingCircle() {
        const loadingCircle = document.createElement('div');
        loadingCircle.classList.add('loading-circle');
        return loadingCircle;
    }

    function addMessageToChat(message, isUser, sourceDocuments = []) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        if (isUser) {
            messageElement.classList.add('user-message');
            messageElement.innerHTML = `
                <img src="/static/user-avatar.png" alt="User Avatar" class="profile-pic">
                <div class="message-content">${message}</div>
            `;
        } else {
            messageElement.classList.add('bot-message');
            messageElement.innerHTML = `
                <img src="/static/ai-avatar.png" alt="AI Avatar" class="profile-pic">
                <div class="message-content">${message}</div>
            `;
        }
        chatMessages.appendChild(messageElement);

        // Add to chat history only if it is a user query or a direct bot response
        if (isUser || message.startsWith('Thought for')) {
            const chatHistoryItem = document.createElement('li');
            chatHistoryItem.textContent = message;
            chatHistoryList.appendChild(chatHistoryItem);
        }

        // Add source documents to the list if available
        sourceDocumentsList.innerHTML = ''; // Clear previous source documents
        sourceDocuments.forEach(doc => {
            const sourceDocItem = document.createElement('li');
            sourceDocItem.textContent = doc;
            sourceDocumentsList.appendChild(sourceDocItem);
        });

        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageElement; // Return the message element
    }

    function sendMessage(message, file) {
        // Disable user input while the bot is thinking
        userInputField.disabled = true;
        sendButton.disabled = true;

        startTime = new Date();
        const thinkingMessageElement = addMessageToChat('Thinking...', false);
        const loadingCircle = createLoadingCircle();
        thinkingMessageElement.querySelector('.message-content').appendChild(loadingCircle);

        let formData = new FormData();
        if (file) {
            formData.append('file', file);
        } else if (message) {
            formData.append('question', message);
        }

        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const endTime = new Date();
            const timeDiff = (endTime - startTime) / 1000;

            // Replace only the content of the thinking message
            thinkingMessageElement.querySelector('.message-content').innerHTML = '';

            if (!isGreeting(message)) {
                // Add "Thought for x seconds" message
                const thoughtTimeDiv = document.createElement('div');
                thoughtTimeDiv.classList.add('thought-time');
                thoughtTimeDiv.textContent = `Thought for ${timeDiff.toFixed(1)} seconds`;
                thinkingMessageElement.querySelector('.message-content').appendChild(thoughtTimeDiv);
            }

            // Add the bot response after the thought time
            const botResponseDiv = document.createElement('div');
            botResponseDiv.textContent = data.bot_response;
            thinkingMessageElement.querySelector('.message-content').appendChild(botResponseDiv);

            sourceDocumentsList.innerHTML = '';
            data.source_documents.forEach(doc => {
                const sourceDocItem = document.createElement('li');
                sourceDocItem.textContent = doc;
                sourceDocumentsList.appendChild(sourceDocItem);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            addMessageToChat('Error: Could not get a response from the server.', false);
        })
        .finally(() => {
            // Re-enable user input after the bot has responded
            userInputField.disabled = false;
            sendButton.disabled = false;
        });
    }

    function handleFileUpload(file) {
        const fileName = file.name;
        addMessageToChat(`Uploading file: ${fileName}`, true); // Show upload message on user's side
    
        // Disable user input during file upload and processing
        userInputField.disabled = true;
        sendButton.disabled = true;
    
        // Create a message element for the loading bar
        processingMessageElement = addMessageToChat('Processing file...', false);
        loadingBarContainer = document.createElement('div');
        loadingBarContainer.classList.add('loading-bar-container');
        loadingBar = document.createElement('div');
        loadingBar.classList.add('loading-bar');
        loadingBar.style.width = '0%'; // Initialize to 0%
        loadingBarContainer.appendChild(loadingBar);
        processingMessageElement.querySelector('.message-content').appendChild(loadingBarContainer);
    
        let formData = new FormData();
        formData.append('file', file);
    
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            // File uploaded successfully, remove the temporary message
            if (processingMessageElement) {
                processingMessageElement.remove();
            }
            // Add a new "File uploaded successfully" message
            addMessageToChat('File uploaded successfully', false);
            // Now, create a new "Processing file..." message with a loading bar
            processingMessageElement = addMessageToChat('Processing file...', false);
            loadingBarContainer = document.createElement('div');
            loadingBarContainer.classList.add('loading-bar-container');
            loadingBar = document.createElement('div');
            loadingBar.classList.add('loading-bar');
            loadingBar.style.width = '0%'; // Initialize to 0%
            loadingBarContainer.appendChild(loadingBar);
            processingMessageElement.querySelector('.message-content').appendChild(loadingBarContainer);
            return fetch('/process', { method: 'POST' });
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            // Start updating the loading bar and checking the processing status
            checkProcessingStatus(loadingBar, processingMessageElement);
        })
        .catch(error => {
            console.error('Error:', error);
            addMessageToChat(`Error: ${error.message}`, false);
            // Re-enable user input on error
            userInputField.disabled = false;
            sendButton.disabled = false;
        });
    }
    
    

    function checkProcessingStatus(loadingBar, loadingBarMessage) {
        fetch('/processing_status')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed') {
                    // Replace the "Processing file..." message with "File processed successfully"
                    loadingBarMessage.querySelector('.message-content').innerHTML = 'File processed successfully';
                    // Add the "You can ask me anything..." message after processing is complete and the message has been updated
                    addMessageToChat('You can ask me anything about the uploaded document, such as, "What is the total amount in the invoice?"', false);
                    // Enable user input after "You can ask me anything..." message
                    userInputField.disabled = false;
                    sendButton.disabled = false;
                } else if (data.status === 'failed') {
                    // Update the message to indicate failure
                    loadingBarMessage.querySelector('.message-content').innerHTML = 'File processing failed. Please try again.';
                    // Enable user input on failure
                    userInputField.disabled = false;
                    sendButton.disabled = false;
                } else {
                    // Simulate progress update
                    let currentWidth = parseFloat(loadingBar.style.width) || 0;
                    let newWidth = Math.min(currentWidth + 10, 90); // Increment up to 90%
                    loadingBar.style.width = newWidth + '%';
    
                    // Continue checking the status
                    setTimeout(() => checkProcessingStatus(loadingBar, loadingBarMessage), 1000);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                addMessageToChat('Error checking processing status.', false);
                // Enable user input on error
                userInputField.disabled = false;
                sendButton.disabled = false;
            });
    }

    function isGreeting(message) {
        const greetings = ['hi', 'hello', 'hey', 'how are you', 'greetings'];
        const lowerCaseMessage = message.toLowerCase();
        return greetings.some(greeting => lowerCaseMessage.includes(greeting));
    }

    chatForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const message = document.getElementById('user-input').value;
        const file = fileInput.files[0];

        if (file) {
            // Don't handle file upload here anymore
            // File upload is handled in the fileInput change event listener
        } else if (message) {
            addMessageToChat(message, true); // Add user messages to the chat
            sendMessage(message, null);
            document.getElementById('user-input').value = '';
        }
    });

    fileInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            fileNameSpan.textContent = file.name;
            // Trigger the file upload immediately
            handleFileUpload(file);
            fileInput.value = ''; // Clear the file input
        } else {
            fileNameSpan.textContent = '';
        }
    });

    themeToggleBtn.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        const icon = themeToggleBtn.querySelector('i');
        icon.classList.toggle('fa-moon');
        icon.classList.toggle('fa-sun');
    });

    // Event listener for file input button
    fileInputLabel.addEventListener('click', function() {
        fileInput.click();
    });
});