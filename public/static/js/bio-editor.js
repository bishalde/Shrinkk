// Bio page editor: link list (drag to reorder), profile, socials, appearance, live preview.

function contrastText(hex) {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  return (r * 299 + g * 587 + b * 114) / 1000 >= 150 ? "#101010" : "#FFFFFF";
}

/** Mirror of services/themes.py resolve(); keep the two in sync. */
function resolveLook(appearance, cfg) {
  const preset = cfg.presets[appearance.theme] || cfg.presets.classic;
  const vars = { ...preset.vars };
  if (appearance.bg) {
    const text = contrastText(appearance.bg);
    vars["--bio-bg"] = appearance.bg;
    vars["--bio-text"] = text;
    vars["--bio-muted"] = text === "#101010" ? "rgba(16,16,16,.65)" : "rgba(255,255,255,.75)";
  }
  if (appearance.button_color) {
    vars["--bio-btn-bg"] = appearance.button_color;
    vars["--bio-btn-text"] = contrastText(appearance.button_color);
  }
  const font = appearance.font || preset.font;
  vars["--bio-radius"] = cfg.radii[appearance.radius || preset.radius];
  vars["--bio-font"] = cfg.fonts[font].family;
  return {
    style: appearance.button_style || preset.style,
    css: Object.entries(vars).map(([k, v]) => `${k}:${v}`).join(";"),
  };
}

const CROP_MAX_BYTES = 15 * 1024 * 1024;  // the original never leaves the browser, only the crop does
const CROP_MAX_ZOOM = 4;
const CROP_OUTPUT = 800;  // px; the server downsizes to 400 for the stored avatar

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

function bioEditor(init) {
  return {
    tab: "links",
    cfg: init.themeConfig,
    networks: init.networks,
    profile: init.profile,
    links: init.links,
    otherLinks: init.otherLinks,
    socials: { ...init.socials },
    socialErrors: {},
    appearance: { ...init.appearance },
    newLink: { title: "", original_url: "" },
    adding: false,
    uploading: false,
    crop: { show: false, src: null, img: null, w: 0, h: 0, zoom: 1, x: 0, y: 0, drag: null },
    status: "saved", // saving | saved | error

    init() {
      this.saveProfile = debounce(() => this.persist("/api/bio/profile", {
        display_name: this.profile.display_name, bio: this.profile.bio,
      }), 600);
      this.saveSocials = debounce(async () => {
        try {
          this.status = "saving";
          await api("/api/bio/socials", { method: "POST", json: { socials: this.socials } });
          this.socialErrors = {};
          this.status = "saved";
        } catch (e) {
          this.socialErrors = e.fields;
          this.status = "error";
        }
      }, 700);
      this.saveAppearance = debounce(() => this.persist("/api/bio/appearance", { appearance: this.appearance }), 400);
    },

    get look() { return resolveLook(this.appearance, this.cfg); },

    get previewSocials() {
      return Object.entries(this.socials)
        .filter(([k, v]) => v && v.trim() && this.networks[k] && !this.socialErrors[k])
        .map(([k]) => ({ key: k, ...this.networks[k] }));
    },

    get visibleLinks() { return this.links.filter((l) => l.is_active && !l.expired); },

    async persist(url, json) {
      this.status = "saving";
      try {
        await api(url, { method: "POST", json });
        this.status = "saved";
      } catch (e) {
        this.status = "error";
        toast(e.message, "error");
      }
    },

    // --- links -----------------------------------------------------------
    initSortable(el) {
      if (!window.Sortable) return;
      Sortable.create(el, {
        handle: "[data-drag]",
        animation: 160,
        ghostClass: "opacity-40",
        onEnd: (evt) => {
          const from = evt.oldDraggableIndex, to = evt.newDraggableIndex;
          if (from === to) return;
          // Undo Sortable's DOM move and let Alpine re-render from the reordered array.
          evt.item.remove();
          const items = [...el.querySelectorAll(":scope > li")];
          el.insertBefore(evt.item, items[from] || null);
          const [moved] = this.links.splice(from, 1);
          this.links.splice(to, 0, moved);
          this.persist("/api/bio/order", { ids: this.links.map((l) => l.id) });
        },
      });
    },

    async addLink() {
      if (!this.newLink.original_url.trim()) return;
      this.adding = true;
      try {
        const link = await api("/api/links", {
          method: "POST",
          json: { ...this.newLink, on_profile: true },
        });
        this.links.push(link);
        this.newLink = { title: "", original_url: "" };
        toast("Link added to your page");
      } catch (e) {
        toast(e.message, "error");
      } finally {
        this.adding = false;
      }
    },

    async addExisting(id) {
      if (!id) return;
      try {
        const link = await api(`/api/links/${id}`, { method: "PATCH", json: { on_profile: true } });
        this.otherLinks = this.otherLinks.filter((l) => l.id !== id);
        this.links.push(link);
      } catch (e) { toast(e.message, "error"); }
    },

    async removeFromPage(link) {
      try {
        const updated = await api(`/api/links/${link.id}`, { method: "PATCH", json: { on_profile: false } });
        this.links = this.links.filter((l) => l.id !== link.id);
        this.otherLinks.unshift(updated);
        toast("Removed from your page (the short link still works)");
      } catch (e) { toast(e.message, "error"); }
    },

    async patchLink(link, json) {
      try {
        Object.assign(link, await api(`/api/links/${link.id}`, { method: "PATCH", json }));
      } catch (e) { toast(e.message, "error"); }
    },

    // --- avatar ----------------------------------------------------------
    // Picking a photo opens a crop dialog; only the cropped square is uploaded.
    pickAvatar(event) {
      const file = event.target.files[0];
      event.target.value = "";
      if (!file) return;
      if (!file.type.startsWith("image/")) { toast("Upload a JPG, PNG, WebP or GIF image.", "error"); return; }
      if (file.size > CROP_MAX_BYTES) { toast("Images must be 15 MB or smaller.", "error"); return; }
      const src = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        Object.assign(this.crop, { show: true, src, img, w: img.naturalWidth, h: img.naturalHeight, zoom: 1 });
        this.$nextTick(() => {
          const box = this.$refs.cropBox.clientWidth;
          const s = this.cropScale();
          this.crop.x = (box - this.crop.w * s) / 2;
          this.crop.y = (box - this.crop.h * s) / 2;
        });
      };
      img.onerror = () => { URL.revokeObjectURL(src); toast("That file couldn't be read as an image.", "error"); };
      img.src = src;
    },

    // Scale at which the image exactly covers the crop box, times the zoom slider.
    cropScale() {
      const box = this.$refs.cropBox.clientWidth;
      return Math.max(box / this.crop.w, box / this.crop.h) * this.crop.zoom;
    },

    cropStyle() {
      if (!this.crop.src) return "";
      const s = this.cropScale();
      return `width:${this.crop.w * s}px;height:${this.crop.h * s}px;transform:translate(${this.crop.x}px,${this.crop.y}px)`;
    },

    // Keep the image covering the whole box so the result never has empty corners.
    clampCrop() {
      const box = this.$refs.cropBox.clientWidth;
      const s = this.cropScale();
      this.crop.x = Math.min(0, Math.max(box - this.crop.w * s, this.crop.x));
      this.crop.y = Math.min(0, Math.max(box - this.crop.h * s, this.crop.y));
    },

    setCropZoom(zoom) {
      const center = this.$refs.cropBox.clientWidth / 2;
      const before = this.cropScale();
      this.crop.zoom = Math.min(CROP_MAX_ZOOM, Math.max(1, zoom));
      const ratio = this.cropScale() / before;
      this.crop.x = center - (center - this.crop.x) * ratio;  // zoom around the middle of the box
      this.crop.y = center - (center - this.crop.y) * ratio;
      this.clampCrop();
    },

    cropDragStart(e) {
      e.currentTarget.setPointerCapture(e.pointerId);
      this.crop.drag = { px: e.clientX, py: e.clientY, x: this.crop.x, y: this.crop.y };
    },
    cropDragMove(e) {
      const d = this.crop.drag;
      if (!d) return;
      this.crop.x = d.x + e.clientX - d.px;
      this.crop.y = d.y + e.clientY - d.py;
      this.clampCrop();
    },
    cropDragEnd() { this.crop.drag = null; },

    cropNudge(dx, dy) {
      this.crop.x += dx;
      this.crop.y += dy;
      this.clampCrop();
    },

    closeCrop() {
      if (this.crop.src) URL.revokeObjectURL(this.crop.src);
      Object.assign(this.crop, { show: false, src: null, img: null, drag: null });
    },

    async saveCrop() {
      const box = this.$refs.cropBox.clientWidth;
      const ratio = CROP_OUTPUT / box;
      const s = this.cropScale();
      const canvas = document.createElement("canvas");
      canvas.width = canvas.height = CROP_OUTPUT;
      const ctx = canvas.getContext("2d");
      ctx.imageSmoothingQuality = "high";
      ctx.drawImage(this.crop.img, this.crop.x * ratio, this.crop.y * ratio, this.crop.w * s * ratio, this.crop.h * s * ratio);
      // Browsers without WebP encoding fall back to PNG, which the server also accepts.
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/webp", 0.92));
      this.closeCrop();
      if (!blob) { toast("Couldn't crop that image. Try another one.", "error"); return; }
      const form = new FormData();
      form.append("avatar", blob, blob.type === "image/webp" ? "avatar.webp" : "avatar.png");
      this.uploading = true;
      try {
        const data = await api("/api/bio/avatar", { method: "POST", form });
        this.profile.avatar_url = data.avatar_url;
        toast("Photo updated");
      } catch (e) { toast(e.message, "error"); }
      finally { this.uploading = false; }
    },

    async removeAvatar() {
      try {
        await api("/api/bio/avatar", { method: "DELETE" });
        this.profile.avatar_url = null;
      } catch (e) { toast(e.message, "error"); }
    },

    // --- appearance --------------------------------------------------------
    pickTheme(key) {
      this.appearance = { theme: key };
      this.saveAppearance();
    },
    setLook(key, value) {
      if (value === null) delete this.appearance[key];
      else this.appearance[key] = value;
      this.appearance = { ...this.appearance };
      this.saveAppearance();
    },
    presetLook(key) { return resolveLook({ theme: key }, this.cfg); },
  };
}
