/*
 * ITR Learn & Simulate
 * static/js/ai_assistant.js
 *
 * Modern AI Assistant chat interface with Markdown rendering,
 * responsive bubbles, quick question execution, and smooth scrolling.
 */

"use strict";

/* =========================================
   DOM ELEMENTS
========================================= */

const chatMessages    = document.getElementById("chatMessages");
const chatInput       = document.getElementById("chatInput");
const sendButton      = document.getElementById("sendButton");
const clearButton     = document.getElementById("clearChat");
const typingIndicator = document.getElementById("typingIndicator");
const chatWelcome     = document.getElementById("chatWelcome");

/* =========================================
   CONVERSATION HISTORY
========================================= */

let conversationHistory = [];
let isSending = false;

/* =========================================
   MARKDOWN PARSER
========================================= */

function formatMarkdown(text) {
    if (!text) return "";

    // 1. Escape HTML
    let escaped = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // 2. Code blocks (```lang ... ```)
    escaped = escaped.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, function(match, lang, code) {
        return `<pre class="chat-pre"><code>${code.trim()}</code></pre>`;
    });

    // 3. Inline code (`code`)
    escaped = escaped.replace(/`([^`\n]+)`/g, '<code class="chat-code">$1</code>');

    // 4. Horizontal rules (--- or ***)
    escaped = escaped.replace(/^(?:---|—{3,}|\*\*\*|___)\s*$/gm, '<hr class="chat-divider">');

    // 5. Headings (###, ##, #)
    escaped = escaped.replace(/^### (.*$)/gm, '<h4 class="chat-h4">$1</h4>');
    escaped = escaped.replace(/^## (.*$)/gm, '<h3 class="chat-h3">$1</h3>');
    escaped = escaped.replace(/^# (.*$)/gm, '<h2 class="chat-h2">$1</h2>');

    // 6. Bold (**text**) & Italic (*text* or _text_)
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
    escaped = escaped.replace(/_([^_\n]+)_/g, '<em>$1</em>');

    // 7. Parse lists and paragraphs line by line
    const lines = escaped.split('\n');
    let inUl = false;
    let inOl = false;
    let output = [];

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        let trimmed = line.trim();

        let bulletMatch = trimmed.match(/^[\*\-]\s+(.*)$/);
        let numberMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);

        if (bulletMatch) {
            if (inOl) { output.push('</ol>'); inOl = false; }
            if (!inUl) { output.push('<ul class="chat-list">'); inUl = true; }
            output.push(`<li>${bulletMatch[1]}</li>`);
        } else if (numberMatch) {
            if (inUl) { output.push('</ul>'); inUl = false; }
            if (!inOl) { output.push('<ol class="chat-list">'); inOl = true; }
            output.push(`<li>${numberMatch[2]}</li>`);
        } else {
            if (inUl) { output.push('</ul>'); inUl = false; }
            if (inOl) { output.push('</ol>'); inOl = false; }

            if (trimmed === '') {
                // blank line
            } else if (trimmed.startsWith('<h') || trimmed.startsWith('<pre') || trimmed.startsWith('<hr')) {
                output.push(trimmed);
            } else {
                output.push(`<p>${trimmed}</p>`);
            }
        }
    }

    if (inUl) output.push('</ul>');
    if (inOl) output.push('</ol>');

    return output.join('\n');
}

/* =========================================
   RENDER MESSAGE
========================================= */

function renderMessage(role, text) {
    // Hide welcome card once a conversation starts
    if (chatWelcome) {
        chatWelcome.style.display = "none";
    }

    const wrapper = document.createElement("div");
    wrapper.className = "chat-message chat-" + role;

    // Meta header with icon and name
    const meta = document.createElement("div");
    meta.className = "chat-meta";
    if (role === "user") {
        meta.innerHTML = `<span class="meta-avatar">👤</span><span class="meta-name">You</span>`;
    } else {
        meta.innerHTML = `<span class="meta-avatar">🤖</span><span class="meta-name">AI Assistant</span>`;
    }

    // Message Bubble
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";

    if (role === "user") {
        // User message: plain text with line breaks preserved
        const p = document.createElement("p");
        p.textContent = text;
        p.style.margin = "0";
        p.style.whiteSpace = "pre-wrap";
        bubble.appendChild(p);
    } else {
        // Assistant message: rich markdown
        bubble.innerHTML = formatMarkdown(text);
    }

    wrapper.appendChild(meta);
    wrapper.appendChild(bubble);

    // Insert before typing indicator if present
    if (typingIndicator && typingIndicator.parentNode === chatMessages) {
        chatMessages.insertBefore(wrapper, typingIndicator);
    } else {
        chatMessages.appendChild(wrapper);
    }

    // Smooth scroll to bottom
    scrollToBottom();
}

function scrollToBottom() {
    if (chatMessages) {
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: "smooth"
        });
    }
}

/* =========================================
   TYPING INDICATOR
========================================= */

function showTyping() {
    if (chatWelcome) {
        chatWelcome.style.display = "none";
    }
    if (typingIndicator) {
        typingIndicator.style.display = "flex";
        chatMessages.appendChild(typingIndicator);
        scrollToBottom();
    }
}

function hideTyping() {
    if (typingIndicator) {
        typingIndicator.style.display = "none";
    }
}

/* =========================================
   SEND MESSAGE TO FLASK BACKEND
========================================= */

async function sendMessage(customText) {
    if (isSending) return;

    const message = (customText !== undefined ? customText : (chatInput ? chatInput.value : "")).trim();
    if (!message) return;

    isSending = true;

    // Render user message
    renderMessage("user", message);
    conversationHistory.push({ role: "user", text: message });

    // Reset input
    if (chatInput) {
        chatInput.value = "";
        chatInput.style.height = "auto";
    }
    if (sendButton) sendButton.disabled = true;

    showTyping();

    try {
        const response = await fetch("/api/ai-assistant", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        hideTyping();

        if (data.success) {
            renderMessage("assistant", data.response);
            conversationHistory.push({
                role: "assistant",
                text: data.response
            });
        } else {
            renderMessage(
                "assistant",
                "⚠️ " + (data.error || "The AI Assistant is temporarily unavailable. Please try again.")
            );
        }

    } catch (error) {
        hideTyping();
        renderMessage(
            "assistant",
            "⚠️ Network error. Please check your connection and try again."
        );
        console.error("AI Assistant error:", error);

    } finally {
        isSending = false;
        if (sendButton) sendButton.disabled = false;
        if (chatInput) chatInput.focus();
    }
}

/* =========================================
   EVENT LISTENERS
========================================= */

if (sendButton) {
    sendButton.addEventListener("click", function() {
        sendMessage();
    });
}

if (chatInput) {
    chatInput.addEventListener("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Dynamic auto-grow
    chatInput.addEventListener("input", function() {
        this.style.height = "auto";
        const newHeight = Math.min(this.scrollHeight, 130);
        this.style.height = Math.max(newHeight, 36) + "px";
    });
}

if (clearButton) {
    clearButton.addEventListener("click", function() {
        if (confirm("Clear conversation history?")) {
            // Remove all message elements except typingIndicator and welcome
            const messages = chatMessages.querySelectorAll(".chat-message:not(#typingIndicator)");
            messages.forEach(msg => msg.remove());
            conversationHistory = [];

            if (chatWelcome) {
                chatWelcome.style.display = "flex";
            }
            hideTyping();
        }
    });
}

/* =========================================
   QUICK QUESTIONS
========================================= */

document.querySelectorAll(".quick-question").forEach(function(btn) {
    btn.addEventListener("click", function() {
        const q = this.getAttribute("data-question") || this.textContent.trim();
        if (q) {
            sendMessage(q);
        }
    });
});
