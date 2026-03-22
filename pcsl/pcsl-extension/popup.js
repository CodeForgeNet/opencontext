// pcsl/pcsl-extension/popup.js

const STATUS_EL = document.getElementById('server-status');
const AUDIT_EL = document.getElementById('audit-log');
const URL_INPUT = document.getElementById('server-url-input');
const SAVE_BTN = document.getElementById('save-url');

let currentServerUrl = "http://localhost:8000";

// Load saved URL from storage
chrome.storage.local.get(['pcsl_server_url'], (result) => {
    if (result.pcsl_server_url) {
        currentServerUrl = result.pcsl_server_url;
        URL_INPUT.value = currentServerUrl;
    } else {
        URL_INPUT.value = currentServerUrl;
    }
    checkServer();
});

async function checkServer() {
    STATUS_EL.textContent = "Checking...";
    STATUS_EL.className = "status";
    
    // Get current URL from input
    currentServerUrl = URL_INPUT.value.trim().replace(/\/$/, '') || "http://localhost:8000";

    try {
        const resp = await fetch(`${currentServerUrl}/`);
        if (resp.status === 200) {
            STATUS_EL.textContent = "Server Online";
            STATUS_EL.className = "status online";
            fetchAudit();
        } else {
            STATUS_EL.textContent = "Server Error";
            STATUS_EL.className = "status offline";
        }
    } catch (e) {
        STATUS_EL.textContent = "Server Offline";
        STATUS_EL.className = "status offline";
    }
}

async function fetchAudit() {
    try {
        // First authorize as local-user for audit access
        const authRes = await fetch(`${currentServerUrl}/pcsl/authorize`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                client_id: "pcsl-extension-popup",
                scopes: ["identity", "preferences", "skills", "projects"],
                expires_in: 60
            })
        });
        const { access_token } = await authRes.json();

        const resp = await fetch(`${currentServerUrl}/pcsl/audit`, {
            headers: { "Authorization": `Bearer ${access_token}` }
        });
        const data = await resp.json();
        
        if (data.log && data.log.length > 0) {
            AUDIT_EL.innerHTML = data.log.reverse().slice(0, 10).map(entry => `
                <div style="border-bottom: 1px solid #444; padding: 4px 0;">
                    <b>${entry.client_id}</b>: ${entry.scopes.join(', ')}<br/>
                    <small>${new Date(entry.timestamp).toLocaleTimeString()}</small>
                </div>
            `).join('');
        } else {
            AUDIT_EL.textContent = "No logs yet.";
        }
    } catch (e) {
        AUDIT_EL.textContent = "Failed to load logs.";
    }
}

// Save URL button handler
SAVE_BTN.addEventListener('click', () => {
    const url = URL_INPUT.value.trim().replace(/\/$/, '');
    if (url) {
        chrome.storage.local.set({ pcsl_server_url: url }, () => {
            currentServerUrl = url;
            checkServer();
        });
    }
});

// Also check connection when clicking the existing button
document.getElementById('check-connection').addEventListener('click', checkServer);

// Initial check
checkServer();
