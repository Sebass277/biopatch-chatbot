document.addEventListener('DOMContentLoaded', () => {
    // --- SELECTORES (IDs de la página BioPatch) ---
    const chatToggle = document.getElementById('chat-toggle');
    const chatClose = document.getElementById('chat-close');
    const chatWindow = document.getElementById('chat-window');
    const toggleIcon = document.getElementById('toggle-icon');
    
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send'); // Botón de envío
    const chatMessages = document.getElementById('chat-messages');

    // --- ESTADO (Lógica de tu script.js) ---
    let isChatOpen = false; // Del widget BioPatch
    let isProcessing = false; // De tu script.js
    
    // (De tu script.js, con el mensaje de bienvenida de Patchy)
    const conversationHistory = [
        { role: "model", parts: [{ text: "¡Bienvenido/a! Soy **Patchy**, su asistente virtual experto en el proyecto BioPatch. Por favor, formule sus preguntas de forma clara. Al enviar un mensaje, usted acepta nuestros términos de uso y la política de confidencialidad de la información. Debido al control de calidad, la respuesta puede tardar unos segundos. ¿En qué podemos ayudarle hoy?" }] }
    ];

    // --- LÓGICA DEL WIDGET (Abrir/Cerrar) (de BioPatch) ---

    function openChat() {
        isChatOpen = true;
        chatToggle.setAttribute('aria-expanded', 'true');
        chatWindow.classList.remove('hidden', 'scale-95', 'opacity-0');
        chatWindow.classList.add('scale-100', 'opacity-100');
        toggleIcon.classList.add('rotate-180'); 
        chatInput.focus();

        // Muestra el mensaje de bienvenida SOLO la primera vez que se abre
        if (chatMessages.children.length === 0) {
             addMessage(conversationHistory[0].parts[0].text, 'bot');
        }
        chatMessages.scrollTop = chatMessages.scrollHeight; 
    }

    function closeChat() {
        isChatOpen = false;
        chatToggle.setAttribute('aria-expanded', 'false');
        chatWindow.classList.remove('scale-100', 'opacity-100');
        chatWindow.classList.add('scale-95', 'opacity-0');
        toggleIcon.classList.remove('rotate-180'); 

        setTimeout(() => {
            if (!isChatOpen) {
                chatWindow.classList.add('hidden');
            }
        }, 300);
    }

    chatToggle.addEventListener('click', () => {
        if (isChatOpen) {
            closeChat();
        } else {
            openChat();
        }
    });

    chatClose.addEventListener('click', closeChat);

    // --- LÓGICA DEL CHAT (de tu script.js) ---

    /**
     * Función 'addMessage' fusionada: 
     * Usa la lógica de 'marked.js' de tu script.js
     * Usa los estilos Tailwind de la página BioPatch
     */
    function addMessage(text, sender) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('flex', 'mb-3'); // Usamos mb-3 en lugar de space-y-3

        const messageBubble = document.createElement('div');
        messageBubble.classList.add('p-3', 'rounded-xl', 'max-w-[80%]', 'text-sm');

        if (sender === 'user') {
            // Estilo de usuario (Verde)
            messageContainer.classList.add('justify-end');
            messageBubble.classList.add('bg-green-500', 'text-white', 'rounded-tr-none');
            // 'marked.parse' no es necesario para el usuario, solo 'textContent'
            messageBubble.textContent = text; 
        } else { // 'bot'
            // Estilo de bot (Gris oscuro)
            messageContainer.classList.add('justify-start');
            messageBubble.classList.add('bg-gray-700', 'text-white', 'rounded-tl-none');
            // Usa marked.js para procesar el HTML (negritas, etc.)
            messageBubble.innerHTML = marked.parse(text); 
        }
        
        messageContainer.appendChild(messageBubble);
        chatMessages.appendChild(messageContainer);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return messageBubble; // Devuelve el elemento para poder eliminar el mje "Pensando..."
    }

    // Función para añadir a la MEMORIA (de tu script.js)
    function addToHistory(text, role) {
        conversationHistory.push({
            role: role === 'user' ? 'user' : 'model', 
            parts: [{ text: text }]
        });
    }

    // Función que llama al backend (de tu script.js)
    async function getBotResponse() {
        // Mensaje "Pensando" adaptado a Patchy
        const thinkingMessage = addMessage("🤖 Patchy está pensando...", 'bot');

        // Aplicar Enfriamiento (de tu script.js)
        isProcessing = true;
        chatInput.disabled = true;
        chatSend.disabled = true;
        chatSend.textContent = '...'; // Botón más pequeño

        try {
            // La misma llamada a tu backend /api/chat
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ history: conversationHistory }),
            });

            thinkingMessage.remove(); 
            
            if (!response.ok) {
                const errorData = await response.json();
                const errorMsg = `Error: ${errorData.error || 'No se pudo contactar al servidor.'}`;
                addMessage(errorMsg, 'bot');
                addToHistory(errorMsg, 'model'); // Guardar error
                return;
            }

            const data = await response.json();
            const botResponseText = data.response;
            
            // Mostrar y agregar respuesta (de tu script.js)
            addMessage(botResponseText, 'bot');
            addToHistory(botResponseText, 'model');

        } catch (error) {
            console.error("Error en getBotResponse:", error);
            thinkingMessage.remove(); 
            const errorMsg = "Ocurrió un error de conexión. ¿Está el servidor Python corriendo?";
            addMessage(errorMsg, 'bot');
            addToHistory(errorMsg, 'model'); // Guardar error
        } finally {
            // Quitar el Enfriamiento (de tu script.js)
            isProcessing = false;
            chatInput.disabled = false;
            chatSend.disabled = false;
            chatSend.textContent = 'Enviar';
            chatInput.focus(); // Re-enfocar el input
        }
    }

    // --- MANEJADOR DE ENVÍO DE FORMULARIO (de tu script.js) ---
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault(); 
        
        if (isProcessing) {
            return; // Evita envíos múltiples
        }

        const userText = chatInput.value.trim();
        if (userText === '') return; 

        // 1. Mostrar y agregar mensaje a la memoria
        addMessage(userText, 'user');
        addToHistory(userText, 'user');

        // 2. Llamar al backend
        getBotResponse(); 

        // 3. Limpiar el campo de entrada
        chatInput.value = '';
    });
});