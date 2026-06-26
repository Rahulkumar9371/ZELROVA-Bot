const ZELROVA = {
    refreshTime: 10000,
    currentGuildId: null,
    apiBase: "",
};

function qs(selector) {
    return document.querySelector(selector);
}

function qsa(selector) {
    return document.querySelectorAll(selector);
}

function setText(selector, value) {
    const el = qs(selector);
    if (el) el.textContent = value;
}

function formatNumber(num) {
    return Number(num || 0).toLocaleString();
}

function formatDate(value) {
    if (!value) return "Unknown";
    try {
        return new Date(value).toLocaleString();
    } catch {
        return "Unknown";
    }
}

async function apiGet(url) {
    const res = await fetch(url);
    return await res.json();
}

async function apiPost(url, data = {}) {
    const res = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    });

    return await res.json();
}

function toast(message, type = "success") {
    let box = qs("#toast-box");

    if (!box) {
        box = document.createElement("div");
        box.id = "toast-box";
        box.className = "toast-box";
        document.body.appendChild(box);
    }

    const item = document.createElement("div");
    item.className = `toast toast-${type}`;
    item.textContent = message;

    box.appendChild(item);

    setTimeout(() => {
        item.remove();
    }, 3500);
}

async function loadGlobalStats() {
    try {
        const data = await apiGet("/api/stats");

        setText("[data-stat='total_servers']", formatNumber(data.total_servers));
        setText("[data-stat='live_servers']", formatNumber(data.live_servers));
        setText("[data-stat='total_members']", formatNumber(data.total_members));
        setText("[data-stat='trusted_servers']", formatNumber(data.trusted_servers));
        setText("[data-stat='updated_at']", formatDate(data.updated_at));

        renderTopServers(data.top_servers || []);
        renderTrustedServers(data.top_trusted_servers || []);
    } catch (err) {
        console.error(err);
    }
}

function renderTopServers(servers) {
    const box = qs("#top-servers-list");
    if (!box) return;

    if (!servers.length) {
        box.innerHTML = `<div class="empty">No server ranking available.</div>`;
        return;
    }

    box.innerHTML = servers.map((server, index) => `
        <div class="server-rank-card">
            <div class="rank-number">#${index + 1}</div>
            <div class="server-rank-main">
                <strong>${escapeHtml(server.name || "Unknown Server")}</strong>
                <span>Owner: ${escapeHtml(server.owner_name || "Unknown")}</span>
                <span>Members: ${formatNumber(server.member_count)}</span>
            </div>
            <div class="trust-score">${server.trust?.score || 0}</div>
        </div>
    `).join("");
}

function renderTrustedServers(servers) {
    const box = qs("#trusted-servers-list");
    if (!box) return;

    if (!servers.length) {
        box.innerHTML = `<div class="empty">No trusted servers yet.</div>`;
        return;
    }

    box.innerHTML = servers.map((server, index) => `
        <div class="trusted-card">
            <div>
                <strong>${escapeHtml(server.name || "Unknown Server")}</strong>
                <p>Top ${index + 1} trusted server</p>
            </div>
            <span>${server.trust?.score || 0}%</span>
        </div>
    `).join("");
}

async function loadSelectedGuild() {
    const root = qs("[data-guild-id]");
    if (!root) return;

    const guildId = root.getAttribute("data-guild-id");
    if (!guildId) return;

    ZELROVA.currentGuildId = guildId;

    try {
        const data = await apiGet(`/api/server/${guildId}`);
        if (!data.ok) return;

        const server = data.server;

        setText("[data-server='name']", server.name || "Unknown Server");
        setText("[data-server='owner']", server.owner_name || "Unknown Owner");
        setText("[data-server='members']", formatNumber(server.member_count));
        setText("[data-server='trust']", server.trust?.score || 0);
        setText("[data-server='rank']", server.trust?.rank || "N/A");
        setText("[data-server='joined']", formatDate(server.bot_joined_at));
        setText("[data-server='live']", server.is_live ? "Live" : "Offline");

        fillSettings(server.settings || {});
    } catch (err) {
        console.error(err);
    }
}

function fillSettings(settings) {
    qsa("[data-setting]").forEach((input) => {
        const path = input.getAttribute("data-setting");
        const value = getNested(settings, path);

        if (input.type === "checkbox") {
            input.checked = Boolean(value);
        } else if (value !== undefined && value !== null) {
            input.value = value;
        }
    });
}

function collectSettings() {
    const settings = {};

    qsa("[data-setting]").forEach((input) => {
        const path = input.getAttribute("data-setting");

        let value;
        if (input.type === "checkbox") {
            value = input.checked;
        } else if (input.type === "number") {
            value = Number(input.value || 0);
        } else {
            value = input.value;
        }

        setNested(settings, path, value);
    });

    return settings;
}

async function saveDashboardSettings() {
    if (!ZELROVA.currentGuildId) {
        toast("Server select nahi hai.", "error");
        return;
    }

    const settings = collectSettings();

    try {
        const data = await apiPost(
            `/api/dashboard/${ZELROVA.currentGuildId}/save`,
            { settings }
        );

        if (data.ok) {
            toast("Dashboard settings saved.");
            await loadSelectedGuild();
        } else {
            toast(data.error || "Save failed.", "error");
        }
    } catch (err) {
        console.error(err);
        toast("Save error.", "error");
    }
}

async function syncDashboard() {
    if (!ZELROVA.currentGuildId) {
        toast("Server select nahi hai.", "error");
        return;
    }

    try {
        const data = await apiPost(`/api/dashboard/${ZELROVA.currentGuildId}/sync`);

        if (data.ok) {
            toast("Dashboard synced.");
            await loadSelectedGuild();
            await loadGlobalStats();
        } else {
            toast("Sync failed.", "error");
        }
    } catch (err) {
        console.error(err);
        toast("Sync error.", "error");
    }
}

function setupButtons() {
    qsa("[data-action='save-dashboard']").forEach((btn) => {
        btn.addEventListener("click", saveDashboardSettings);
    });

    qsa("[data-action='sync-dashboard']").forEach((btn) => {
        btn.addEventListener("click", syncDashboard);
    });

    qsa("[data-tab]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const tab = btn.getAttribute("data-tab");
            switchTab(tab);
        });
    });
}

function switchTab(tabName) {
    qsa("[data-tab]").forEach((btn) => {
        btn.classList.toggle("active", btn.getAttribute("data-tab") === tabName);
    });

    qsa("[data-tab-panel]").forEach((panel) => {
        panel.classList.toggle("active", panel.getAttribute("data-tab-panel") === tabName);
    });
}

function getNested(obj, path) {
    return path.split(".").reduce((acc, key) => {
        if (acc && Object.prototype.hasOwnProperty.call(acc, key)) {
            return acc[key];
        }
        return undefined;
    }, obj);
}

function setNested(obj, path, value) {
    const keys = path.split(".");
    let current = obj;

    keys.forEach((key, index) => {
        if (index === keys.length - 1) {
            current[key] = value;
        } else {
            current[key] = current[key] || {};
            current = current[key];
        }
    });
}

function escapeHtml(text) {
    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

document.addEventListener("DOMContentLoaded", async () => {
    setupButtons();

    await loadGlobalStats();
    await loadSelectedGuild();

    setInterval(loadGlobalStats, ZELROVA.refreshTime);
});