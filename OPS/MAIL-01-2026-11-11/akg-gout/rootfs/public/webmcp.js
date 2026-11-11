// agent-kg.ai — the one page script (CEO ruling 2026-09-14): WebMCP registration of the contact form, nothing else.
// Registers office_contact with navigator.modelContext so an agent can use the form of record. Stores nothing.
(function () {
  try {
    var mc = navigator.modelContext;
    if (!mc) return;
    var tool = {
      name: "office_contact",
      description: "Send a message to the Agentic Private Office of Matthew Keddy through its contact form of record; a person reads it. Fields: email (reply-to), message.",
      inputSchema: {
        type: "object",
        properties: {
          email: { type: "string", description: "Reply-to email address" },
          message: { type: "string", description: "The message" }
        },
        required: ["email", "message"]
      },
      execute: async function (input) {
        var r = await fetch("https://formspree.io/f/xrpgnoob", {
          method: "POST",
          headers: { "Accept": "application/json", "Content-Type": "application/json" },
          body: JSON.stringify({ email: input.email, message: input.message, site: "agent-kg.ai" })
        });
        return { status: r.status, ok: r.ok };
      }
    };
    if (typeof mc.registerTool === "function") mc.registerTool(tool);
    else if (typeof mc.provideContext === "function") mc.provideContext({ tools: [tool] });
  } catch (e) { /* non-fatal */ }
})();
