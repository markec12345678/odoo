// AI Concierge Chat Widget
(function() {
    "use strict";
    var conversationId = null;
    var isOpen = false;

    function toggleChat() {
        var container = document.getElementById('si_chatbot_container');
        if (isOpen) {
            container.classList.add('si-chatbot-hidden');
            isOpen = false;
        } else {
            container.classList.remove('si-chatbot-hidden');
            isOpen = true;
            document.getElementById('si_chatbot_text').focus();
        }
    }

    function addMessage(role, content) {
        var messages = document.getElementById('si_chatbot_messages');
        var div = document.createElement('div');
        div.className = 'si-chatbot-msg si-chatbot-' + role;
        div.textContent = content;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    function sendMessage() {
        var input = document.getElementById('si_chatbot_text');
        var text = input.value.trim();
        if (!text) return;
        input.value = '';
        addMessage('user', text);
        
        var loading = document.createElement('div');
        loading.className = 'si-chatbot-msg si-chatbot-assistant si-chatbot-loading';
        loading.textContent = '...';
        document.getElementById('si_chatbot_messages').appendChild(loading);

        fetch('/chatbot/send', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: text}),
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            loading.remove();
            if (data.success) {
                addMessage('assistant', data.response);
                conversationId = data.conversation_id;
            } else {
                addMessage('assistant', data.error || 'Napaka.');
            }
        })
        .catch(function(e) {
            loading.remove();
            addMessage('assistant', 'Povezava ni uspela. Poskusite kasneje.');
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        document.getElementById('si_chatbot_button').addEventListener('click', toggleChat);
        document.getElementById('si_chatbot_close').addEventListener('click', toggleChat);
        document.getElementById('si_chatbot_send').addEventListener('click', sendMessage);
        document.getElementById('si_chatbot_text').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
        addMessage('assistant', 'Pozdravljeni! Kako vam lahko pomagam?');
    });
})();
