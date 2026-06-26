const sidebar = document.getElementById("sidebar");
const menuBtn = document.getElementById("menuBtn");
const toast = document.getElementById("toast");
const saveAllBtn = document.getElementById("saveAllBtn");
const activityList = document.getElementById("activityList");

function showToast(message = "Saved successfully") {
  if (!toast) return;

  toast.textContent = message;
  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 2500);
}

function addActivity(message) {
  if (!activityList) return;

  const li = document.createElement("li");
  li.textContent = message;
  activityList.prepend(li);

  if (activityList.children.length > 10) {
    activityList.removeChild(activityList.lastElementChild);
  }
}

async function postData(url, data = {}) {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    if (result.success) {
      showToast(result.message || "Done");
      addActivity(result.message || "Dashboard updated.");
    } else {
      showToast(result.message || "Action failed");
      alert(result.message || "Action failed");
    }

    return result;

  } catch (error) {
    console.error(error);
    showToast("Connection failed");
    return null;
  }
}

if (menuBtn && sidebar) {
  menuBtn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
  });
}

document.querySelectorAll("[data-module]").forEach(toggle => {
  toggle.addEventListener("change", async () => {
    await postData("/api/save/modules", {
      [toggle.dataset.module]: toggle.checked
    });
  });
});

document.querySelectorAll("[data-action]").forEach(button => {
  button.addEventListener("click", async () => {
    const action = button.dataset.action;

    if (action === "Create Backup") {
      await postData("/api/backup/create", {});
      return;
    }

    await postData("/api/owner/action", {
      action: action,
      payload: {}
    });
  });
});

if (saveAllBtn) {
  saveAllBtn.addEventListener("click", async () => {
    const modules = {};

    document.querySelectorAll("[data-module]").forEach(toggle => {
      modules[toggle.dataset.module] = toggle.checked;
    });

    await postData("/api/save/modules", modules);
  });
}

async function loadStatus() {
  try {
    const response = await fetch("/api/status");
    const data = await response.json();

    if (data.success) {
      addActivity(`Status checked: ${data.status} | ${data.latency}`);
    }
  } catch (error) {
    console.error(error);
  }
}

setTimeout(loadStatus, 1000);

console.log("ZELROVA Dashboard JS Loaded");