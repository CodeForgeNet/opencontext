const axios = require('axios');

/**
 * OpenContext (PCSL) SDK for AI application developers.
 */
class PCSLClient {
  /**
   * @param {Object} config
   * @param {string} config.serverUrl - User's PCSL server URL
   * @param {string} config.clientId - AI app's unique identifier
   */
  constructor(config) {
    this.serverUrl = config.serverUrl.replace(/\/$/, "");
    this.clientId = config.clientId;
    this.token = null;
  }

  /**
   * Request a scoped access token from the PCSL server.
   * @param {string[]} scopes - List of requested namespaces
   * @param {number} expiresIn - Token lifetime in seconds (default: 3600)
   * @returns {Promise<string>} - The JWT access token
   */
  async authorize(scopes, expiresIn = 3600) {
    const res = await axios.post(`${this.serverUrl}/pcsl/authorize`, {
      client_id: this.clientId,
      scopes: scopes,
      expires_in: expiresIn
    });
    this.token = res.data.access_token;
    return this.token;
  }

  /**
   * Fetch authorized context namespaces.
   * @returns {Promise<Object>} - The personal context object
   */
  async getContext() {
    if (!this.token) {
      throw new Error("Not authorized. Call authorize() first.");
    }
    const res = await axios.get(`${this.serverUrl}/pcsl/context`, {
      headers: { Authorization: `Bearer ${this.token}` }
    });
    return res.data.context;
  }

  /**
   * Helper to prepend context as a system message to a message array.
   * Useful for Chat Completion APIs (OpenAI, Anthropic).
   * @param {Array} messages - Existing messages
   * @returns {Promise<Array>} - Messages with context prepended
   */
  async injectIntoMessages(messages) {
    const context = await this.getContext();
    const contextMsg = {
      role: "system",
      content: `<pcsl_context>\n${JSON.stringify(context, null, 2)}\n</pcsl_context>`
    };
    return [contextMsg, ...messages];
  }

  /**
   * Suggest an update to a context namespace.
   * @param {string} namespace 
   * @param {string} key 
   * @param {any} value 
   */
  async suggestUpdate(namespace, key, value) {
    if (!this.token) {
      throw new Error("Not authorized. Call authorize() first.");
    }
    const res = await axios.post(`${this.serverUrl}/pcsl/update`, {
      namespace,
      key,
      value
    }, {
      headers: { Authorization: `Bearer ${this.token}` }
    });
    return res.data;
  }
}

/**
 * OpenAI integration helper.
 * @param {PCSLClient} pcslClient 
 * @param {Array} messages 
 */
async function withPCSL(pcslClient, messages) {
  return pcslClient.injectIntoMessages(messages);
}

module.exports = {
  PCSLClient,
  withPCSL
};
