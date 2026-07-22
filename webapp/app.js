const STORAGE_KEY = "saleamlak_bot_data";
let screenHistory = ["main-menu"];
let tg = null;

try {
    if (window.Telegram && window.Telegram.WebApp) {
        tg = window.Telegram.WebApp;
        tg.expand();
        tg.ready();
        tg.setHeaderColor("#0f0f1a");
        tg.setBackgroundColor("#0f0f1a");
    }
} catch (e) {}

function loadData() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
    return {
        favorites: [],
        recent: [],
        settings: { notifications: true, language: "en" },
        chat_count: 0,
        first_seen: new Date().toISOString(),
    };
}

function saveData(data) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function addRecent(action) {
    const data = loadData();
    data.recent.unshift({ action, time: new Date().toISOString() });
    data.recent = data.recent.slice(0, 10);
    saveData(data);
}

function showScreen(id) {
    document.querySelectorAll(".screen").forEach((s) => s.classList.remove("active"));
    const target = document.getElementById(id);
    if (target) {
        target.classList.add("active");
        screenHistory.push(id);
    }
    if (id === "favorites") renderFavorites();
    if (id === "recent") renderRecent();
    if (id === "stats") renderStats();
    if (id === "settings") renderSettings();
    addRecent("Viewed: " + id);
}

function showSubScreen(id) {
    document.querySelectorAll(".screen").forEach((s) => s.classList.remove("active"));
    const target = document.getElementById(id);
    if (target) {
        target.classList.add("active");
        screenHistory.push(id);
    }
}

function goBack() {
    screenHistory.pop();
    const prev = screenHistory[screenHistory.length - 1] || "main-menu";
    document.querySelectorAll(".screen").forEach((s) => s.classList.remove("active"));
    const target = document.getElementById(prev);
    if (target) target.classList.add("active");
    if (prev === "favorites") renderFavorites();
    if (prev === "recent") renderRecent();
    if (prev === "stats") renderStats();
}

function renderFavorites() {
    const data = loadData();
    const list = document.getElementById("fav-list");
    const empty = document.getElementById("fav-empty");
    if (data.favorites.length === 0) {
        list.innerHTML = "";
        empty.style.display = "block";
        return;
    }
    empty.style.display = "none";
    list.innerHTML = data.favorites
        .map(
            (fav, i) =>
                `<div class="fav-item"><span>${fav}</span><button onclick="removeFavorite(${i})">✕</button></div>`
        )
        .join("");
}

function addFavorite() {
    const input = document.getElementById("fav-input");
    const val = input.value.trim();
    if (!val) return;
    const data = loadData();
    data.favorites.push(val);
    saveData(data);
    input.value = "";
    renderFavorites();
    addRecent("Added favorite: " + val);
}

function removeFavorite(index) {
    const data = loadData();
    data.favorites.splice(index, 1);
    saveData(data);
    renderFavorites();
}

function renderRecent() {
    const data = loadData();
    const list = document.getElementById("recent-list");
    const empty = document.getElementById("recent-empty");
    if (data.recent.length === 0) {
        list.innerHTML = "";
        empty.style.display = "block";
        return;
    }
    empty.style.display = "none";
    list.innerHTML = data.recent
        .map((r) => {
            const t = r.time ? new Date(r.time).toLocaleString() : "";
            return `<div class="recent-item">${r.action}<br><span class="time">${t}</span></div>`;
        })
        .join("");
}

function renderStats() {
    const data = loadData();
    document.getElementById("stat-chats").textContent = data.chat_count || 0;
    document.getElementById("stat-favs").textContent = data.favorites.length;
    document.getElementById("stat-recent").textContent = data.recent.length;
    document.getElementById("stat-first").textContent = data.first_seen
        ? new Date(data.first_seen).toLocaleDateString()
        : "-";
}

function renderSettings() {
    const data = loadData();
    document.getElementById("notif-toggle").checked = data.settings.notifications;
    document.getElementById("lang-btn").textContent = data.settings.language.toUpperCase();
}

function toggleSetting(key) {
    const data = loadData();
    if (key === "notifications") {
        data.settings.notifications = !data.settings.notifications;
    } else if (key === "language") {
        data.settings.language = data.settings.language === "en" ? "am" : "en";
    }
    saveData(data);
    renderSettings();
}

function clearAllData() {
    if (confirm("Are you sure you want to clear all your data?")) {
        localStorage.removeItem(STORAGE_KEY);
        renderFavorites();
        renderRecent();
        renderStats();
        renderSettings();
    }
}

async function sendChat() {
    const input = document.getElementById("chat-input");
    const msg = input.value.trim();
    if (!msg) return;
    input.value = "";

    const chatDiv = document.getElementById("chat-messages");
    chatDiv.innerHTML += `<div class="chat-bubble user">${escapeHtml(msg)}</div>`;
    chatDiv.innerHTML += `<div class="chat-bubble bot" id="loading-dots"><div class="loading-dots"><span></span><span></span><span></span></div></div>`;
    chatDiv.scrollTop = chatDiv.scrollHeight;

    const data = loadData();
    data.chat_count = (data.chat_count || 0) + 1;
    saveData(data);
    addRecent("AI chat: " + msg.substring(0, 30));

    try {
        const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: "Bearer " + getApiKey(),
            },
            body: JSON.stringify({
                model: "google/gemini-3.1-flash-lite-preview",
                messages: [
                    {
                        role: "system",
                        content: getSystemPrompt(),
                    },
                    { role: "user", content: msg },
                ],
                max_tokens: 1000,
                temperature: 0.7,
            }),
        });

        const json = await res.json();
        const reply =
            json.choices && json.choices[0]
                ? json.choices[0].message.content
                : "Sorry, I couldn't process that.";

        const loadingEl = document.getElementById("loading-dots");
        if (loadingEl) loadingEl.remove();

        chatDiv.innerHTML += `<div class="chat-bubble bot">${escapeHtml(reply)}</div>`;
    } catch (err) {
        const loadingEl = document.getElementById("loading-dots");
        if (loadingEl) loadingEl.remove();
        chatDiv.innerHTML += `<div class="chat-bubble bot">Error: ${escapeHtml(err.message)}</div>`;
    }

    chatDiv.scrollTop = chatDiv.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function getApiKey() {
    return "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";
}

function getSystemPrompt() {
    return `You are Saleamlak Aschalew's Personal AI Telegram Assistant. 
Answer questions about him using ONLY the information below. 
Be friendly, concise, and professional.

PROFILE:
- Name: Saleamlak Aschalew
- Title: Junior Project Manager & Web Developer
- About: I am a junior project manager with a strong interest in planning, teamwork, and digital projects.
- Email: whilegodsaleamlak@gmail.com
- Phone: +251 930 220 301, +251 944 015 457
- Address: Addis Ababa, Figa Traffic Lights
- Portfolio: https://saleamlak.vercel.app
- GitHub: https://github.com/saleamlak
- Education: Diploma (2023-2025) Misrak Polytechnic College, Degree (2026) GAGE University College Computer Science
- Skills: HTML/CSS 95%, JavaScript 85%, React 80%, Node.js 75%, PHP 75%, SQL 65%, MongoDB 65%, Git 85%, UI/UX 85%
- Projects: Gulit E-commerce, School Result Management, To Do List, Income Expense Tracker
- Experience: Junior PM at Tech Innovations Inc. (2025-Present), Lead Developer at Digital Solutions Corp. (2019-2022)
- Services: Creative Branding, Design Systems, Digital Platforms
- Career Goals: Grow into a professional project manager

Answer as Saleamlak's assistant. Be helpful and professional.`;
}
