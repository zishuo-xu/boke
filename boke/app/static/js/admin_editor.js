(function () {
  function initEditor() {
    if (!window.editormd) {
      return;
    }

    const container = document.getElementById("post-editor");
    if (!container) {
      return;
    }

    window.__postEditor = window.editormd("post-editor", {
      width: "100%",
      height: 640,
      path: "https://cdn.jsdelivr.net/npm/editor.md@1.5.0/lib/",
      watch: true,
      syncScrolling: "single",
      saveHTMLToTextarea: false,
      emoji: true,
      taskList: true,
      tex: false,
      flowChart: false,
      sequenceDiagram: false,
      htmlDecode: "style,script,iframe",
      toolbarIcons: function () {
        return [
          "undo",
          "redo",
          "|",
          "bold",
          "del",
          "italic",
          "quote",
          "ucwords",
          "uppercase",
          "lowercase",
          "|",
          "h1",
          "h2",
          "h3",
          "|",
          "list-ul",
          "list-ol",
          "hr",
          "|",
          "link",
          "reference-link",
          "image",
          "code",
          "preformatted-text",
          "code-block",
          "table",
          "datetime",
          "|",
          "watch",
          "preview",
          "fullscreen",
          "|",
          "clear",
          "search"
        ];
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initEditor);
  } else {
    initEditor();
  }
})();
