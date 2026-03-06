(function () {
  function pick(sel) {
    return document.querySelector(sel);
  }

  function setStatus(message, isError) {
    const el = pick("#quick_category_status");
    if (!el) {
      return;
    }
    el.textContent = message;
    el.classList.toggle("text-danger", !!isError);
    el.classList.toggle("text-muted", !isError);
  }

  async function onQuickAdd() {
    const input = pick("#quick_category_name");
    const select = pick("#category_id");
    const btn = pick("#quick_category_add_btn");
    if (!input || !select || !btn) {
      return;
    }

    const name = (input.value || "").trim();
    if (!name) {
      setStatus("请输入分类名称", true);
      return;
    }

    btn.disabled = true;
    setStatus("正在新增分类...", false);

    try {
      const resp = await fetch("/admin/categories/quick-add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name, sort: 0 })
      });
      const data = await resp.json();

      if (resp.ok && data.ok && data.category) {
        const option = document.createElement("option");
        option.value = String(data.category.id);
        option.textContent = data.category.name;
        option.selected = true;
        select.appendChild(option);
        input.value = "";
        setStatus(`已新增并选中分类：${data.category.name}`, false);
        return;
      }

      if (resp.status === 409 && data.category) {
        select.value = String(data.category.id);
        setStatus("分类已存在，已为你自动选中", false);
        return;
      }

      setStatus((data && data.message) || "新增分类失败", true);
    } catch (err) {
      setStatus("新增分类失败，请稍后重试", true);
    } finally {
      btn.disabled = false;
    }
  }

  function init() {
    const btn = pick("#quick_category_add_btn");
    const input = pick("#quick_category_name");
    if (!btn || !input) {
      return;
    }

    btn.addEventListener("click", onQuickAdd);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        onQuickAdd();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
