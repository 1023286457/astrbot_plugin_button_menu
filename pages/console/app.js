const bridge = window.AstrBotPluginView || window.AstrBotPluginPage;
const app = document.getElementById("app");
const toastRoot = document.getElementById("toast-root");

const state = {
  config: null,
  layout: null,
  bots: [],
  page: 1,
  dirty: false,
  saving: false,
};

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "html") node.innerHTML = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (key === "checked") node.checked = Boolean(value);
    else node.setAttribute(key, value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function icon(name, size = 13) {
  const paths = {
    plus: '<path d="M12 5v14M5 12h14"/>',
    save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><path d="M17 21v-8H7v8M7 3v5h8"/>',
    up: '<path d="m18 15-6-6-6 6"/>',
    down: '<path d="m6 9 6 6 6-6"/>',
    trash: '<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v5M14 11v5"/>',
    refresh: '<path d="M20 11a8.1 8.1 0 0 0-15.5-3M4 4v4h4M4 13a8.1 8.1 0 0 0 15.5 3M20 20v-4h-4"/>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  };
  return el("span", {
    class: "icon",
    html: `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${paths[name] || paths.menu}</svg>`,
  });
}

function toast(message, type = "success") {
  const node = el("div", { class: `toast ${type}` }, String(message));
  toastRoot.appendChild(node);
  setTimeout(() => {
    node.style.opacity = "0";
    setTimeout(() => node.remove(), 180);
  }, 3200);
}

async function apiGet(endpoint) {
  if (!bridge) throw new Error("AstrBot 页面 bridge 未加载");
  return bridge.apiGet(endpoint);
}

async function apiPost(endpoint, body) {
  if (!bridge) throw new Error("AstrBot 页面 bridge 未加载");
  return bridge.apiPost(endpoint, body);
}

function clamp(value, low, high) {
  return Math.max(low, Math.min(high, Number(value) || low));
}

function calcLayout(config) {
  const buttons = config.buttons || [];
  const columns = clamp(config.columns, 1, 5);
  const requested = clamp(config.page_size, 1, 20);
  let pageSize = Math.min(requested, columns * 5);
  let pages = Math.max(1, Math.ceil(buttons.length / pageSize));
  if (pages > 1) {
    pageSize = Math.min(pageSize, columns * 4);
    pages = Math.max(1, Math.ceil(buttons.length / pageSize));
  }
  const chunks = [];
  for (let index = 0; index < buttons.length; index += pageSize) {
    chunks.push(buttons.slice(index, index + pageSize));
  }
  if (!chunks.length) chunks.push([]);
  return { columns, requested_page_size: requested, page_size: pageSize, pages, total: buttons.length, chunks };
}

function markDirty() {
  state.dirty = true;
  const status = document.getElementById("save-state");
  if (status) status.textContent = "有未保存修改";
}

function updatePreview() {
  state.layout = calcLayout(state.config);
  state.page = Math.max(1, Math.min(state.page, state.layout.pages));
  renderPreview();
}

function renderPreview() {
  const box = document.getElementById("preview-card");
  if (!box) return;
  const config = state.config;
  const layout = state.layout;
  const page = state.page;
  const items = layout.chunks[page - 1] || [];
  const descriptions = config.show_description
    ? items.filter((item) => item.description).slice(0, 4)
    : [];
  const grid = el("div", { class: "qq-grid", style: `grid-template-columns:repeat(${layout.columns},minmax(0,1fr))` });
  for (const item of items) {
    const hint = item.type === "image" ? "[图片]" : item.type === "link" ? item.url || "[链接]" : item.text || "";
    grid.append(
      el("div", { class: "qq-button", title: `${hint}${item.description ? ` · ${item.description}` : ""}` }, item.label || "未命名"),
    );
  }
  if (!items.length) grid.append(el("div", { class: "qq-empty" }, "还没有按钮，先在左侧添加"));
  const nav = [];
  if (layout.pages > 1) {
    const prev = el("button", { class: "qq-nav-button", type: "button", onclick: () => { state.page = Math.max(1, page - 1); renderPreview(); } }, "上一页");
    const next = el("button", { class: "qq-nav-button", type: "button", onclick: () => { state.page = Math.min(layout.pages, page + 1); renderPreview(); } }, "下一页");
    prev.disabled = page <= 1;
    next.disabled = page >= layout.pages;
    nav.push(prev, next);
  }
  const children = [
    el("h2", { class: "qq-heading" }, config.title || "未命名菜单"),
    config.subtitle ? el("p", { class: "qq-subtitle" }, config.subtitle) : null,
    descriptions.length
      ? el("p", { class: "qq-description" }, descriptions.map((item) => `${item.label}：${item.description}`).join(" · "))
      : null,
    grid,
    nav.length ? el("div", { class: "qq-nav" }, ...nav) : null,
    config.footer ? el("p", { class: "qq-footer" }, config.footer) : null,
  ];
  box.replaceChildren(...children.filter(Boolean));
  const count = document.getElementById("preview-count");
  if (count) count.textContent = `共 ${layout.total} 个按钮 · 第 ${page}/${layout.pages} 页 · 每页 ${layout.page_size} 个`;
  const pagerInfo = document.getElementById("pager-info");
  if (pagerInfo) pagerInfo.textContent = `${page} / ${layout.pages}`;
  const prevButton = document.getElementById("preview-prev");
  const nextButton = document.getElementById("preview-next");
  if (prevButton) prevButton.disabled = page <= 1;
  if (nextButton) nextButton.disabled = page >= layout.pages;
}

function field(label, key, attrs = {}) {
  const input = el("input", {
    type: attrs.type || "text",
    min: attrs.min,
    max: attrs.max,
    value: state.config[key] ?? "",
    placeholder: attrs.placeholder || "",
    oninput: (event) => {
      state.config[key] = attrs.type === "number" ? Number(event.target.value) : event.target.value;
      markDirty();
      updatePreview();
    },
  });
  return el("div", { class: attrs.full ? "field full" : "field" }, el("label", {}, label), input);
}

function renderBotOptions() {
  const list = document.getElementById("bot-list");
  if (!list) return;
  const selected = new Set(state.config.enabled_bots || []);
  if (!state.bots.length) {
    list.replaceChildren(el("div", { class: "empty-buttons" }, "当前没有检测到 QQ 官方机器人，请先在 AstrBot 中配置平台。"));
    return;
  }
  list.replaceChildren(
    ...state.bots.map((bot) =>
      el(
        "label",
        { class: `bot-row ${state.config.bot_mode === "all" ? "is-disabled" : ""}` },
        el("input", {
          type: "checkbox",
          checked: state.config.bot_mode === "all" || selected.has(bot.id),
          disabled: state.config.bot_mode === "all",
          onchange: (event) => {
            if (event.target.checked) selected.add(bot.id);
            else selected.delete(bot.id);
            state.config.enabled_bots = [...selected];
            markDirty();
          },
        }),
        el("span", { class: "bot-name" }, bot.name || bot.id),
        el("span", { class: "bot-id" }, bot.id),
      ),
    ),
  );
}

function setBotMode(mode) {
  state.config.bot_mode = mode;
  if (mode === "selected" && !(state.config.enabled_bots || []).length) {
    state.config.enabled_bots = state.bots.map((bot) => bot.id);
  }
  markDirty();
  renderShell();
}

function actionInput(item, index) {
  if (item.type === "link") {
    return el("input", {
      value: item.url || "",
      maxlength: 1000,
      placeholder: "链接地址，例如 https://example.com",
      "aria-label": "链接地址",
      oninput: (event) => { item.url = event.target.value; markDirty(); updatePreview(); },
    });
  }
  if (item.type === "image") {
    const input = el("input", {
      type: "file",
      accept: "image/png,image/jpeg",
      style: "display:none",
      onchange: (event) => {
        const file = event.target.files?.[0];
        if (!file) return;
        if (file.size > 5 * 1024 * 1024) {
          toast("图片不能超过 5MB", "error");
          return;
        }
        const reader = new FileReader();
        reader.onload = () => {
          item.image = String(reader.result || "");
          markDirty();
          renderButtonRows();
          updatePreview();
        };
        reader.readAsDataURL(file);
      },
    });
    const preview = item.image
      ? el("img", { class: "action-image-preview", src: item.image, alt: "" })
      : el("span", { class: "action-image-empty" }, "未选择");
    return el(
      "div",
      { class: "action-image" },
      input,
      el("button", { class: "btn btn-ghost btn-sm", type: "button", onclick: () => input.click() }, item.image ? "更换图片" : "上传图片"),
      preview,
    );
  }
  return el("input", {
    value: item.text || "",
    maxlength: 2000,
    placeholder: "点击按钮后发送的文字",
    "aria-label": "发送文字",
    oninput: (event) => { item.text = event.target.value; markDirty(); updatePreview(); },
  });
}

function renderButtonRows() {
  const list = document.getElementById("button-list");
  const total = document.getElementById("button-total");
  if (total) total.textContent = `${state.config.buttons.length} 个`;
  if (!list) return;
  list.replaceChildren();
  if (!state.config.buttons.length) {
    list.append(el("div", { class: "empty-buttons" }, "还没有按钮，点下方「新增按钮」开始配置"));
    return;
  }
  state.config.buttons.forEach((item, index) => {
    list.append(
      el(
        "div",
        { class: "button-row" },
        el("input", {
          value: item.label,
          maxlength: 20,
          placeholder: "按钮文字",
          "aria-label": "按钮文字",
          oninput: (event) => { item.label = event.target.value; markDirty(); updatePreview(); },
        }),
        el(
          "select",
          {
            class: "action-type",
            "aria-label": "按钮动作",
            onchange: (event) => {
              item.type = event.target.value;
              markDirty();
              renderButtonRows();
              updatePreview();
            },
          },
          el("option", { value: "text", selected: item.type === "text" }, "发送文字"),
          el("option", { value: "image", selected: item.type === "image" }, "发送图片"),
          el("option", { value: "link", selected: item.type === "link" }, "发送链接"),
        ),
        actionInput(item, index),
        el("input", {
          value: item.description,
          maxlength: 60,
          placeholder: "说明（可选）",
          "aria-label": "按钮说明",
          oninput: (event) => { item.description = event.target.value; markDirty(); updatePreview(); },
        }),
        el(
          "div",
          { class: "row-tools" },
          el("button", { class: "icon-btn", type: "button", title: "上移", onclick: () => moveButton(index, -1) }, icon("up", 12)),
          el("button", { class: "icon-btn", type: "button", title: "下移", onclick: () => moveButton(index, 1) }, icon("down", 12)),
          el("button", { class: "icon-btn danger", type: "button", title: "删除", onclick: () => removeButton(index) }, icon("trash", 12)),
        ),
      ),
    );
  });
}

function moveButton(index, delta) {
  const target = index + delta;
  if (target < 0 || target >= state.config.buttons.length) return;
  const buttons = state.config.buttons;
  [buttons[index], buttons[target]] = [buttons[target], buttons[index]];
  markDirty();
  renderButtonRows();
  updatePreview();
}

function removeButton(index) {
  state.config.buttons.splice(index, 1);
  markDirty();
  renderButtonRows();
  updatePreview();
}

function addButton() {
  state.config.buttons.push({
    label: "新按钮",
    type: "text",
    text: "你好",
    url: "",
    image: "",
    description: "",
  });
  markDirty();
  renderButtonRows();
  updatePreview();
}

function renderShell() {
  const config = state.config;
  app.replaceChildren(
    el(
      "div",
      { class: "shell" },
      el(
        "header",
        { class: "topbar" },
        el(
          "div",
          { class: "brand" },
          el("div", { class: "brand-icon" }, "≡"),
          el("div", {}, el("h1", {}, "Astrbot菜单配置"), el("p", {}, "配置 /Astrbot菜单 按钮、发送内容、生效机器人与分页预览")),
        ),
        el(
          "div",
          { class: "top-actions" },
          el("span", { class: "status" }, el("span", { class: "status-dot" }), el("span", { id: "save-state" }, "已保存")),
          el("button", { class: "btn btn-ghost", type: "button", onclick: () => reload() }, icon("refresh"), "刷新"),
          el("button", { class: "btn btn-primary", id: "save-button", type: "button", onclick: () => save() }, icon("save"), "保存配置"),
        ),
      ),
      el(
        "main",
        { class: "layout" },
        el(
          "div",
          { class: "stack" },
          el(
            "section",
            { class: "card" },
            el("h2", { class: "card-title" }, "基础信息"),
            el(
              "div",
              { class: "field-grid" },
              field("菜单标题", "title", { placeholder: "例如：机器人菜单" }),
              field("副标题", "subtitle", { placeholder: "例如：请选择功能" }),
              field("底部提示", "footer", { full: true, placeholder: "显示在菜单底部" }),
            ),
          ),
          el(
            "section",
            { class: "card" },
            el("h2", { class: "card-title" }, "分页布局", el("span", {}, "每行最多 5 个，翻页时自动预留导航行")),
            el(
              "div",
              { class: "field-grid" },
              field("每行按钮数", "columns", { type: "number", min: 1, max: 5 }),
              field("每页按钮数", "page_size", { type: "number", min: 1, max: 20 }),
            ),
            el(
              "label",
              { class: "toggle-row" },
              el("input", { type: "checkbox", checked: config.show_description, onchange: (event) => { config.show_description = event.target.checked; markDirty(); updatePreview(); } }),
              el("span", {}, "预览里显示按钮说明（菜单正文也会附带）"),
            ),
          ),
          el(
            "section",
            { class: "card" },
            el("h2", { class: "card-title" }, "生效机器人", el("span", {}, "只有选中的机器人响应 /菜单")),
            el(
              "div",
              { class: "segmented-mini" },
              el(
                "button",
                { type: "button", class: config.bot_mode === "all" ? "is-active" : "", onclick: () => setBotMode("all") },
                "全部机器人",
              ),
              el(
                "button",
                { type: "button", class: config.bot_mode === "selected" ? "is-active" : "", onclick: () => setBotMode("selected") },
                "仅选中的机器人",
              ),
            ),
            el("div", { class: "bot-list", id: "bot-list" }),
          ),
          el(
            "section",
            { class: "card" },
            el("h2", { class: "card-title" }, "按钮列表", el("span", { id: "button-total" }, `${config.buttons.length} 个`)),
            el("div", { class: "button-list", id: "button-list" }),
            el(
              "div",
              { style: "margin-top:10px;display:flex;gap:8px;justify-content:flex-end" },
              el("button", { class: "btn btn-ghost btn-sm", type: "button", onclick: () => addButton() }, icon("plus", 12), "新增按钮"),
            ),
          ),
        ),
        el(
          "aside",
          { class: "card preview-card" },
          el("div", { class: "preview-head" }, el("div", {}, el("h2", {}, "菜单分页预览"), el("p", {}, "按钮位置和真实 QQ 键盘一致")), el("span", { class: "preview-count", id: "preview-count" })),
          el("div", { class: "qq-card", id: "preview-card" }),
          el(
            "div",
            { class: "pager" },
            el("button", { id: "preview-prev", type: "button", onclick: () => { state.page = Math.max(1, state.page - 1); renderPreview(); } }, "上一页"),
            el("button", { id: "preview-next", type: "button", onclick: () => { state.page = Math.min(state.layout.pages, state.page + 1); renderPreview(); } }, "下一页"),
            el("span", { id: "pager-info" }),
          ),
        ),
      ),
    ),
  );
  renderButtonRows();
  renderBotOptions();
  updatePreview();
}

async function load() {
  try {
    if (bridge?.ready) await bridge.ready();
    const data = await apiGet("config");
    state.config = data.config;
    state.layout = data.layout;
    state.bots = data.bots || [];
    state.page = 1;
    state.dirty = false;
    renderShell();
  } catch (error) {
    app.replaceChildren(el("div", { class: "loading" }, `读取配置失败：${error.message || error}`));
  }
}

async function reload() {
  if (state.dirty && !window.confirm("当前有未保存修改，刷新会丢失，继续？")) return;
  await load();
}

async function save() {
  if (state.saving) return;
  state.saving = true;
  const button = document.getElementById("save-button");
  if (button) { button.disabled = true; button.textContent = "保存中…"; }
  try {
    const data = await apiPost("save", state.config);
    state.config = data.config;
    state.layout = data.layout;
    state.bots = data.bots || state.bots;
    state.dirty = false;
    state.page = Math.min(state.page, state.layout.pages);
    renderShell();
    const status = document.getElementById("save-state");
    if (status) status.textContent = "已保存";
    toast("菜单配置已保存");
  } catch (error) {
    toast(error.message || "保存失败", "error");
  } finally {
    state.saving = false;
    if (button) { button.disabled = false; button.textContent = "保存配置"; }
  }
}

window.addEventListener("beforeunload", (event) => {
  if (!state.dirty) return;
  event.preventDefault();
  event.returnValue = "";
});

load();
