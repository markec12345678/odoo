odoo.define('l10n_si_chatbot_widget', function (require) {
    "use strict";
    var publicWidget = require('web.public.widget');

    publicWidget.registry.ChatbotWidget = publicWidget.Widget.extend({
        selector: '#si-chatbot-bubble',
        events: {
            'click': '_onBubbleClick',
        },
        start: function () {
            this._super.apply(this, arguments);
            var self = this;
            $('#si-chatbot-close').on('click', function () {
                $('#si-chatbot-window').hide();
            });
            $('#si-chatbot-send').on('click', function () {
                self._sendMessage();
            });
            $('#si-chatbot-text').on('keypress', function (e) {
                if (e.which === 13) self._sendMessage();
            });
            this._loadHistory();
        },
        _onBubbleClick: function () {
            $('#si-chatbot-window').toggle();
            if ($('#si-chatbot-window').is(':visible')) {
                $('#si-chatbot-text').focus();
            }
        },
        _sendMessage: function () {
            var text = $('#si-chatbot-text').val().trim();
            if (!text) return;
            this._addMessage('user', text);
            $('#si-chatbot-text').val('');
            var self = this;
            this._rpc({
                route: '/chatbot/send',
                params: {message: text},
            }).then(function (result) {
                if (result.response) {
                    self._addMessage('assistant', result.response);
                } else {
                    self._addMessage('assistant', 'Oprostite, trenutno ne morem odgovoriti.');
                }
            }).catch(function () {
                self._addMessage('assistant', 'Napaka. Poskusite kasneje.');
            });
        },
        _addMessage: function (role, content) {
            var cls = role === 'user' ? 'si-chatbot-msg-user' : 'si-chatbot-msg-ai';
            var html = '<div class="' + cls + '">' + content + '</div>';
            $('#si-chatbot-messages').append(html);
            $('#si-chatbot-messages').scrollTop($('#si-chatbot-messages')[0].scrollHeight);
        },
        _loadHistory: function () {
            var self = this;
            this._rpc({
                route: '/chatbot/history',
            }).then(function (result) {
                if (result.messages) {
                    result.messages.forEach(function (msg) {
                        self._addMessage(msg.role, msg.content);
                    });
                }
            }).catch(function () {});
        },
    });
});
