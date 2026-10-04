// START_ME_UP_5 §4 check 12 — the one page script by ruling (CEO, Sept 13 2026): it registers this surface's contact form as its one WebMCP tool.
// Nothing else is scripted on any Allooloo surface. No cookies, no storage, no network call of its own; the form still posts to the endpoint of record.
// Surface refurb (Site Book Addendum A §6, CEO Sept 28 2026): the tint and copy functions are folded into this one file. Still no cookies, no storage, no query string, no network call.
(function () {
  // The tint: the header button sets data-theme on <html> for this page view only. Nothing is remembered; a new page load returns to the device setting.
  var t = document.querySelector('[data-tint]');
  if (t) t.addEventListener('click', function () {
    var r = document.documentElement, cur = r.getAttribute('data-theme');
    var dark = cur ? cur === 'dark' : !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
    r.setAttribute('data-theme', dark ? 'light' : 'dark'); t.setAttribute('aria-pressed', dark ? 'false' : 'true');
  });
  // Copy: a button with data-copy="<id>" copies that element's text to the clipboard.
  var cs = document.querySelectorAll('[data-copy]');
  for (var i = 0; i < cs.length; i++) cs[i].addEventListener('click', function (e) {
    var el = document.getElementById(e.currentTarget.getAttribute('data-copy')); if (!el || !navigator.clipboard) return;
    navigator.clipboard.writeText(el.textContent.trim());
  });
})();
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
