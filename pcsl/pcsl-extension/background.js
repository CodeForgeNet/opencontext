// pcsl/pcsl-extension/background.js

let PCSL_SERVER = "http://localhost:8000";

async function fetchContext(scopes = ["preferences", "skills", "projects"]) {
  const { pcsl_server_url } = await chrome.storage.local.get(['pcsl_server_url']);
  const PCSL_SERVER = pcsl_server_url || "http://localhost:8000";
  
  try {
    // 1. Authorize
    const authRes = await fetch(`${PCSL_SERVER}/pcsl/authorize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        client_id: "pcsl-extension",
        scopes: scopes,
        expires_in: 3600
      })
    });

    if (!authRes.ok) throw new Error("Auth failed");
    const { access_token } = await authRes.json();

    // 2. Get Context
    const ctxRes = await fetch(`${PCSL_SERVER}/pcsl/context`, {
      headers: { "Authorization": `Bearer ${access_token}` }
    });

    if (!ctxRes.ok) throw new Error("Context fetch failed");
    const { context } = await ctxRes.json();
    return context;
  } catch (error) {
    console.error("[PCSL-Background] Error:", error);
    return null;
  }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "GET_CONTEXT") {
    fetchContext(msg.scopes).then(ctx => sendResponse({ context: ctx }));
    return true; // Keep channel open for async
  }
});