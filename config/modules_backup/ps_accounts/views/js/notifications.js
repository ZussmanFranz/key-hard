document.addEventListener("DOMContentLoaded", async function() {
  function i() {
    const r = "ps_accounts/views/js/notifications.js", t = document.querySelectorAll("script");
    let n = null;
    if (t.forEach((e) => {
      e.src.includes(r) && (n = e);
    }), n) {
      const e = n.src;
      return new URL(e).searchParams;
    }
    return null;
  }
  async function s(r) {
    return await fetch(r, {
      method: "GET"
    }).then((t) => t.json()).then((t) => t).catch((t) => (console.error("Error:", t), null));
  }
  function a(r, t) {
    r.forEach((n) => {
      const e = document.createElement("div");
      e.innerHTML = n == null ? void 0 : n.html, t.prepend(e);
    });
  }
  const c = document.querySelector("#main-div .content-div, #main #content");
  if (!c) return;
  const o = i();
  o && a(await s(o.get("ctx") || ""), c);
});
