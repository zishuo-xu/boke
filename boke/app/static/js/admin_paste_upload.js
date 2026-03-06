(function () {
  function setStatus(msg, isError) {
    const el = document.getElementById("autosave_status");
    if (!el) {
      return;
    }
    el.textContent = msg;
    el.classList.toggle("text-danger", !!isError);
    if (!isError) {
      el.classList.remove("text-danger");
    }
  }

  function insertMarkdownImage(url) {
    const md = `\n![](${url})\n`;
    const editor = window.__postEditor;
    if (!editor) {
      return;
    }

    if (editor.cm && typeof editor.cm.replaceSelection === "function") {
      editor.cm.replaceSelection(md);
      return;
    }

    if (typeof editor.insertValue === "function") {
      editor.insertValue(md);
      return;
    }

    const textarea = document.querySelector("textarea[name='content']");
    if (textarea) {
      textarea.value += md;
    }
  }

  async function uploadPastedFile(file) {
    const form = new FormData();
    form.append("editormd-image-file", file, file.name || "pasted-image.png");

    const resp = await fetch("/admin/media/upload", {
      method: "POST",
      body: form,
      credentials: "same-origin"
    });

    const data = await resp.json();
    if (!resp.ok || !data.success || !data.url) {
      throw new Error((data && data.message) || "粘贴图片上传失败");
    }
    return data.url;
  }

  async function onPasteEvent(event) {
    const items = event.clipboardData && event.clipboardData.items;
    if (!items || !items.length) {
      return;
    }

    for (const item of items) {
      if (item.kind === "file" && item.type.startsWith("image/")) {
        const file = item.getAsFile();
        if (!file) {
          continue;
        }

        event.preventDefault();
        setStatus("检测到粘贴图片，正在上传...", false);
        try {
          const url = await uploadPastedFile(file);
          insertMarkdownImage(url);
          setStatus("粘贴图片上传成功，已插入内容", false);
        } catch (err) {
          setStatus(err.message || "粘贴图片上传失败", true);
        }
        return;
      }
    }
  }

  function onCodeMirrorPaste(cm, event) {
    if (event) {
      onPasteEvent(event);
    }
  }

  function attachPasteListener() {
    const editor = window.__postEditor;
    if (!editor || !editor.cm) {
      setTimeout(attachPasteListener, 300);
      return;
    }
    editor.cm.on("paste", onCodeMirrorPaste);

    const wrapper = editor.cm.getWrapperElement && editor.cm.getWrapperElement();
    if (wrapper) {
      wrapper.addEventListener("paste", onPasteEvent);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attachPasteListener);
  } else {
    attachPasteListener();
  }
})();
