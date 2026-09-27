// Shared helpers for every page. Loaded before Alpine so components below exist at init.

function csrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : "";
}

/** fetch() wrapper: sends JSON or FormData with the CSRF header, throws Error(message) on failure. */
async function api(url, { method = "GET", json, form } = {}) {
  const headers = { "X-CSRFToken": csrfToken(), Accept: "application/json" };
  let body;
  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  } else if (form) {
    body = form;
  }
  const res = await fetch(url, { method, headers, body, credentials: "same-origin" });
  let data = {};
  try { data = await res.json(); } catch (_) { /* empty or non-JSON body */ }
  if (!res.ok) {
    const err = new Error(data.error || `Request failed (${res.status})`);
    err.fields = data.fields || {};
    throw err;
  }
  return data;
}

function toast(message, type = "success") {
  window.dispatchEvent(new CustomEvent("toast", { detail: { message, type } }));
}

async function copyText(text, label = "Copied to clipboard") {
  try {
    await navigator.clipboard.writeText(text);
  } catch (_) {
    const ta = Object.assign(document.createElement("textarea"), { value: text });
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }
  toast(label);
}

function toasts(initial) {
  return {
    items: [],
    nextId: 1,
    init() {
      (initial || []).forEach(([type, message]) => this.push({ type, message }));
    },
    push({ message, type = "success" }) {
      const id = this.nextId++;
      this.items.push({ id, message, type, show: true });
      setTimeout(() => this.dismiss(id), type === "error" ? 6000 : 3500);
    },
    dismiss(id) {
      const item = this.items.find((t) => t.id === id);
      if (!item) return;
      item.show = false;
      setTimeout(() => (this.items = this.items.filter((t) => t.id !== id)), 250);
    },
  };
}

/** Live username availability check used on signup, onboarding and settings. */
function usernameField(initial = "", current = "") {
  return {
    username: initial,
    status: "idle", // idle | checking | ok | bad
    message: "",
    timer: null,
    check() {
      this.username = this.username.toLowerCase().replace(/^@/, "").replace(/[^a-z0-9_.]/g, "");
      clearTimeout(this.timer);
      if (!this.username || this.username === current) {
        this.status = "idle";
        this.message = "";
        return;
      }
      this.status = "checking";
      this.timer = setTimeout(async () => {
        try {
          const data = await api(`/api/username-available?u=${encodeURIComponent(this.username)}`);
          this.status = data.available ? "ok" : "bad";
          this.message = data.available ? "Available" : data.error;
        } catch (e) {
          this.status = "idle";
        }
      }, 300);
    },
  };
}
