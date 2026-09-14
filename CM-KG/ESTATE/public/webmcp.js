// START_ME_UP_5 §4 check 12 — the one page script by ruling (CEO, Sept 13 2026): it registers this surface's contact form as its one WebMCP tool.
// Nothing else is scripted on any Allooloo surface. No cookies, no storage, no network call of its own; the form still posts to the endpoint of record.
(function () {
  var f = document.getElementById('contact'); if (!f) return;
  var host = location.hostname;
  var tool = {
    name: 'contact_us',
    description: 'Send a message to Allooloo Technologies Corp. through the contact form of record on ' + host + ' (a reply-to email and a message; read and answered by the operator).',
    inputSchema: { type: 'object', properties: { email: { type: 'string', description: 'reply-to email address' }, message: { type: 'string', description: 'the message' } }, required: ['email', 'message'] },
    annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: false },
    execute: function (input) {
      var e = f.querySelector('[name=email]'), m = f.querySelector('[name=message]');
      if (e) e.value = (input && input.email) || ''; if (m) m.value = (input && input.message) || '';
      if (f.requestSubmit) f.requestSubmit(); else f.submit();
      return { status: 'submitted', site: host };
    }
  };
  var mc = navigator.modelContext; if (!mc) return;
  if (typeof mc.registerTool === 'function') mc.registerTool(tool);
  else if (typeof mc.provideContext === 'function') mc.provideContext({ tools: [tool] });
})();
