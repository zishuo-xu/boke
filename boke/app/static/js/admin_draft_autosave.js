(function () {
  function pick(name) {
    return document.querySelector(name);
  }

  function value(el) {
    return el ? el.value : "";
  }

  function getContent() {
    if (window.__postEditor && typeof window.__postEditor.getMarkdown === "function") {
      return window.__postEditor.getMarkdown();
    }
    return value(pick("textarea[name='content']"));
  }

  async function autosave() {
    const statusEl = pick("#autosave_status");
    const payload = {
      post_id: value(pick("#post_id")) || null,
      draft_key: value(pick("#draft_key")),
      title: value(pick("#title")),
      content: getContent(),
      summary: value(pick("#summary")),
      status: value(pick("#status")) || "0",
      category_id: value(pick("#category_id")) || null,
      tags: value(pick("#tags"))
    };

    if (!payload.title && !payload.content) {
      if (statusEl) {
        statusEl.textContent = "内容为空，未自动保存";
      }
      return;
    }

    try {
      const resp = await fetch("/admin/posts/autosave", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!resp.ok) {
        throw new Error("save failed");
      }
      const data = await resp.json();
      if (statusEl) {
        const ts = (data.updated_at || "").replace("T", " ").slice(0, 19);
        statusEl.textContent = ts ? `已自动保存 ${ts}` : "已自动保存";
      }
    } catch (err) {
      if (statusEl) {
        statusEl.textContent = "自动保存失败，将稍后重试";
      }
    }
  }

  function init() {
    if (!pick("#autosave_status")) {
      return;
    }

    setTimeout(autosave, 6000);
    setInterval(autosave, 15000);
    window.addEventListener("beforeunload", autosave);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
