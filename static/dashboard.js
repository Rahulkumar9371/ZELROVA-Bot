/* ==========================================================
   ZELROVA BOT DASHBOARD JS
   Version 1.0 Foundation
========================================================== */

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
  }, 2600);
}

function addActivity(message) {
  if (!activityList) return;

  const li = document.createElement("li");
  li.textContent = message;

  activityList.prepend(li);

  if (activityList.children.length > 8) {
    activityList.removeChild(activityList.lastElementChild);
  }
}

async function postData(url, data) {
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
      showToast(result.message || "Saved successfully");
      addActivity(result.message || "Dashboard updated.");
    } else {
      showToast("Something went wrong");
    }

    return result;
  } catch (error) {
    console.error(error);
    showToast("Server connection failed");
    return null;
  }
}

if (menuBtn && sidebar) {
  menuBtn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
  });
}

document.querySelectorAll(".side-nav a").forEach(link => {
  link.addEventListener("click", () => {
    document.querySelector(".side-nav a.active")?.classList.remove("active");
    link.classList.add("active");

    if (window.innerWidth <= 900) {
      sidebar.classList.remove("open");
    }
  });
});

document.querySelectorAll("[data-module]").forEach(toggle => {
  toggle.addEventListener("change", async () => {
    const moduleName = toggle.dataset.module;
    const enabled = toggle.checked;

    await postData("/api/save/modules", {
      [moduleName]: enabled
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
      action: action
    });
  });
});

document.querySelectorAll(".theme-card").forEach(theme => {
  theme.addEventListener("click", async () => {
    const themeName = theme.textContent.trim();

    await postData("/api/save/server-config", {
      theme: themeName
    });

    addActivity(`Theme changed to ${themeName}.`);
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

async function loadLiveStatus() {
  try {
    const response = await fetch("/api/status");
    const status = await response.json();

    if (status.success) {
      addActivity(`Live status checked: ${status.status}`);
    }
  } catch (error) {
    console.error(error);
  }
}

function animateCards() {
  const cards = document.querySelectorAll(".glass-card, .stat-card, .module-card");

  cards.forEach((card, index) => {
    card.style.animationDelay = `${index * 0.04}s`;
  });
}

animateCards();

setTimeout(loadLiveStatus, 1200);