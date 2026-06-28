const sidebar = document.getElementById("sidebar");
const menuBtn = document.getElementById("menuBtn");
const toast = document.getElementById("toast");
const saveAllBtn = document.getElementById("saveAllBtn");

function showToast(message = "Done") {
  if (!toast) {
    console.log(message);
    return;
  }

  toast.textContent = message;
  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 2500);
}

async function apiPost(url, data = {}) {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data)
    });

    const json = await res.json();

    if (json.success) {
      showToast(json.message || "Done");
    } else {
      showToast(json.message || "Failed");
    }

    return json;
  } catch (err) {
    console.error(err);
    showToast("Connection failed");
    return null;
  }
}

async function apiGet(url) {
  try {
    const res = await fetch(url);
    return await res.json();
  } catch (err) {
    console.error(err);
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
    await apiPost("/api/save/modules", {
      [toggle.dataset.module]: toggle.checked
    });
  });
});

document.querySelectorAll("[data-action]").forEach(button => {
  button.addEventListener("click", async () => {
    const action = button.dataset.action;

    if (action === "Create Backup") {
      await apiPost("/api/backup/create", {});
      return;
    }

    await apiPost("/api/owner/action", {
      action,
      payload: {}
    });
  });
});

document.querySelectorAll("[data-leave-server]").forEach(button => {
  button.addEventListener("click", async () => {
    const serverId = button.dataset.leaveServer;

    if (!confirm(`ZELROVA ko server ${serverId} se leave karwana hai?`)) {
      return;
    }

    await apiPost("/api/owner/leave-server", {
      server_id: serverId
    });
  });
});

async function musicControl(action, payload = {}) {
  return await apiPost("/api/music/control", {
    action,
    payload
  });
}

window.zelrovaMusic = {
  pause: () => musicControl("pause"),
  resume: () => musicControl("resume"),
  skip: () => musicControl("skip"),
  stop: () => musicControl("stop"),
  loop: () => musicControl("loop"),
  shuffle: () => musicControl("shuffle"),
  volume: value => musicControl("volume", { value })
};

async function refreshMusicStatus() {
  const data = await apiGet("/api/music/status");
  if (!data || !data.success) return;

  const music = data.music || {};

  const title = document.getElementById("musicTitle");
  const status = document.getElementById("musicStatus");
  const queue = document.getElementById("musicQueue");
  const volume = document.getElementById("musicVolume");
  const thumb = document.getElementById("musicThumb");

  if (title) {
    title.textContent = music.current ? music.current.title : "Nothing Playing";
  }

  if (status) {
    status.textContent = music.status || "idle";
  }

  if (volume) {
    volume.textContent = `${music.volume || 75}%`;
  }

  if (thumb && music.current && music.current.thumbnail) {
    thumb.src = music.current.thumbnail;
  }

  if (queue) {
    queue.innerHTML = "";

    const items = music.queue || [];

    if (!items.length) {
      queue.innerHTML = "<li>Queue empty</li>";
    } else {
      items.slice(0, 10).forEach((track, index) => {
        const li = document.createElement("li");
        li.textContent = `${index + 1}. ${track.title}`;
        queue.appendChild(li);
      });
    }
  }
}

document.querySelectorAll("[data-music]").forEach(button => {
  button.addEventListener("click", async () => {
    const action = button.dataset.music;
    await musicControl(action);
    setTimeout(refreshMusicStatus, 700);
  });
});

const volumeSlider = document.getElementById("musicVolumeSlider");
if (volumeSlider) {
  volumeSlider.addEventListener("change", async () => {
    await musicControl("volume", {
      value: Number(volumeSlider.value)
    });
    setTimeout(refreshMusicStatus, 700);
  });
}

async function refreshDashboardStats() {
  const data = await apiGet("/api/dashboard-data");
  if (!data || !data.stats) return;

  document.querySelectorAll("[data-stat]").forEach(el => {
    const key = el.dataset.stat;
    if (data.stats[key] !== undefined) {
      el.textContent = data.stats[key];
    }
  });
}

if (saveAllBtn) {
  saveAllBtn.addEventListener("click", async () => {
    showToast("Saved");
  });
}

refreshMusicStatus();
refreshDashboardStats();

setInterval(refreshMusicStatus, 10000);
setInterval(refreshDashboardStats, 20000);