// pcsl/pcsl-extension/content.js

console.log("[PCSL] Personal Context Sovereignty Layer - Extension Active");

// Robustness Decision: Using MutationObserver for Send Button specifically for Claude/ChatGPT
const OBSERVER_CONFIG = { childList: true, subtree: true, attributes: true, attributeFilter: ['aria-disabled'] };

function findSendButton() {
    // 1. Claude.ai specific
    const claudeBtn = document.querySelector('button[aria-label="Send Message"]:not([aria-disabled="true"])');
    if (claudeBtn) return claudeBtn;

    // 2. ChatGPT specific
    const gptBtn = document.querySelector('button[data-testid="send-button"]:not([disabled])');
    if (gptBtn) return gptBtn;

    // 3. Generic fallback
    return document.querySelector('button[aria-label*="Send" i]:not([disabled])');
}

// Intercepting at the Network level for total robustness
// This is Phase 2 advanced robustness
function injectNetworkWrapper() {
    const script = document.createElement('script');
    script.textContent = `
        (function() {
            const originalFetch = window.fetch;
            window.fetch = async function(...args) {
                const url = args[0];
                const options = args[1];

                // Only intercept POST requests to AI APIs
                if (options && options.method === 'POST' && 
                   (url.includes('claude.ai/api') || url.includes('openai.com/backend-api/conversation'))) {
                    
                    console.log("[PCSL-Bridge] Intercepting AI POST request to: ", url);
                    
                    // We check if the body already contains the context marker
                    // If not, we could inject it here.
                    // But for security, we'll wait for the explicit 'context' keyword from the user if configured.
                }

                return originalFetch.apply(this, args);
            };
        })();
    `;
    (document.head || document.documentElement).appendChild(script);
    script.remove();
}

// Observe the DOM for the send button and attach listeners
const observer = new MutationObserver((mutations) => {
    const sendBtn = findSendButton();
    if (sendBtn && !sendBtn.dataset.pcslListener) {
        console.log("[PCSL] Found Send Button, attaching observer hook.");
        
        sendBtn.addEventListener('mousedown', async () => {
             const textarea = document.querySelector('textarea, [contenteditable="true"]');
             if (!textarea) return;

             console.log("[PCSL] Send triggered, fetching context...");

             chrome.runtime.sendMessage({
                 type: "GET_CONTEXT",
                 scopes: ["identity", "preferences", "skills", "projects"]
             }, (response) => {
                 if (response && response.context) {
                     const prefix = `[PCSL CONTEXT: ${JSON.stringify(response.context)}]\n\n`;
                     if (textarea.tagName === "TEXTAREA") {
                         textarea.value = prefix + textarea.value;
                     } else {
                         textarea.innerText = prefix + textarea.innerText;
                     }
                     console.log("[PCSL] Context injected.");
                 }
             });
        }, true);
        
        sendBtn.dataset.pcslListener = "true";
    }
});

observer.observe(document.body, OBSERVER_CONFIG);
injectNetworkWrapper();
