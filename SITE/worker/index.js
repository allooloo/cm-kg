// allooloo.io — one Worker: static assets + www redirect. The contact form posts to Formspree (standing rule, 2026-09-10).
const APEX = 'allooloo.io';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname === 'www.' + APEX) {
      url.hostname = APEX;
      return Response.redirect(url.toString(), 301);
    }
    if (url.pathname === '/contact') return Response.redirect('https://' + APEX + '/#contact', 302);
    return env.ASSETS.fetch(request);
  }
};
