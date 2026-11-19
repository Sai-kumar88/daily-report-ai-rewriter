// Daily Report AI - Minimal Frontend Controller
document.addEventListener("DOMContentLoaded", () => {
  const reportInput = document.getElementById("reportInput");
  const charCounter = document.getElementById("charCounter");
  const rewriteBtn = document.getElementById("rewriteBtn");
  const clearBtn = document.getElementById("clearBtn");
  const copyBtn = document.getElementById("copyBtn");
  const spinner = document.getElementById("btnSpinner");
  const btnText = document.getElementById("btnText");
  const statusNotice = document.getElementById("statusNotice");
  const statusIcon = document.getElementById("statusIcon");
  const statusText = document.getElementById("statusText");
  const undoBtn = document.getElementById("undoBtn");

  let originalText = "";

  // Update character count and toggle button state
  const updateCharCount = () => {
    const length = reportInput.value.length;
    charCounter.textContent = `${length} / 2000`;

    if (length > 2000) {
      charCounter.style.color = "var(--error-text)";
      rewriteBtn.disabled = true;
    } else {
      charCounter.style.color = "var(--text-muted)";
      rewriteBtn.disabled = length < 3;
    }

    if (length === 0) {
      copyBtn.style.display = "none";
      hideNotice();
    }
  };

  // Show status / alert banner
  const showNotice = (message, type = "success", canUndo = false) => {
    statusNotice.className = `status-notice ${type}`;
    statusNotice.style.display = "flex";
    statusIcon.textContent = type === "success" ? "✓" : type === "warning" ? "⚠️" : "✕";
    statusText.textContent = message;
    undoBtn.style.display = canUndo ? "inline-block" : "none";
  };

  // Hide status / alert banner
  const hideNotice = () => {
    statusNotice.className = "status-notice";
    statusNotice.style.display = "none";
    undoBtn.style.display = "none";
  };

  // Rewrite action handler
  const handleRewrite = async () => {
    const inputContent = reportInput.value.trim();

    if (!inputContent || inputContent.length < 3) {
      showNotice("Please enter at least 3 characters before rewriting.", "warning");
      reportInput.focus();
      return;
    }

    if (inputContent.length > 2000) {
      showNotice("Description must not exceed 2000 characters.", "error");
      return;
    }

    originalText = inputContent;
    hideNotice();

    rewriteBtn.disabled = true;
    spinner.style.display = "inline-block";
    btnText.textContent = "Rewriting...";

    try {
      const response = await fetch("/api/rewrite-daily-report", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
        body: JSON.stringify({ description: inputContent }),
      });

      const data = await response.json();

      if (!response.ok) {
        let errorMsg = data.detail || data.message || "Failed to rewrite report.";
        if (response.status === 503) {
          errorMsg = "NVIDIA API key error. Please verify NVIDIA_API_KEY in .env.";
        }
        showNotice(errorMsg, "error");
        return;
      }

      // Replace text directly in the box
      reportInput.value = data.rewritten;
      updateCharCount();
      copyBtn.style.display = "inline-flex";

      if (data.status === "needs_clarification") {
        showNotice("Needs clarification: Please provide more specific details.", "warning", true);
      } else {
        showNotice("Rewritten in professional English.", "success", true);
      }
    } catch (err) {
      console.error("Rewrite network failure:", err);
      showNotice("Connection error. Make sure the server is running on port 8080.", "error");
    } finally {
      rewriteBtn.disabled = reportInput.value.length < 3;
      spinner.style.display = "none";
      btnText.textContent = "Rewrite";
    }
  };

  // Event Listeners
  reportInput.addEventListener("input", updateCharCount);

  reportInput.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      handleRewrite();
    }
  });

  rewriteBtn.addEventListener("click", handleRewrite);

  clearBtn.addEventListener("click", () => {
    reportInput.value = "";
    originalText = "";
    updateCharCount();
    hideNotice();
    reportInput.focus();
  });

  undoBtn.addEventListener("click", () => {
    if (originalText) {
      reportInput.value = originalText;
      updateCharCount();
      hideNotice();
      reportInput.focus();
    }
  });

  copyBtn.addEventListener("click", async () => {
    const textToCopy = reportInput.value.trim();
    if (!textToCopy) return;

    try {
      await navigator.clipboard.writeText(textToCopy);
      const originalLabel = copyBtn.textContent;
      copyBtn.textContent = "Copied!";
      setTimeout(() => {
        copyBtn.textContent = originalLabel;
      }, 2000);
    } catch (err) {
      console.error("Clipboard copy failed:", err);
    }
  });

  updateCharCount();
});
