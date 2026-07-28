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
        chat_history: [],
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
    if (id === "chat-history") renderChatHistory();
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
        renderChatHistory();
    }
}

function renderChatHistory() {
    const data = loadData();
    const list = document.getElementById("chat-history-list");
    const empty = document.getElementById("chat-history-empty");
    const history = data.chat_history || [];
    if (history.length === 0) {
        list.innerHTML = "";
        empty.style.display = "block";
        return;
    }
    empty.style.display = "none";
    list.innerHTML = history
        .map((msg) => {
            const t = msg.time ? new Date(msg.time).toLocaleString() : "";
            const isUser = msg.role === "user";
            return `<div class="history-msg ${isUser ? "history-user" : "history-bot"}">
                <div class="history-role">${isUser ? "You" : "AI"}</div>
                <div class="history-text">${escapeHtml(msg.content)}</div>
                <div class="history-time">${t}</div>
            </div>`;
        })
        .join("");
    const container = document.getElementById("chat-history-list");
    container.scrollTop = container.scrollHeight;
}

function clearChatHistory() {
    if (confirm("Clear all chat history?")) {
        const data = loadData();
        data.chat_history = [];
        saveData(data);
        renderChatHistory();
    }
}

function getAdminUrl() {
    return localStorage.getItem("admin_api_url") || "";
}

function setAdminUrl(url) {
    localStorage.setItem("admin_api_url", url);
}

async function loadAdminData() {
    const input = document.getElementById("admin-api-url");
    const url = input.value.trim();
    if (!url) {
        document.getElementById("admin-status").textContent = "Please enter the bot API URL.";
        return;
    }
    setAdminUrl(url);
    document.getElementById("admin-status").textContent = "Loading...";

    try {
        const res = await fetch(url + "/api/users");
        const users = await res.json();
        const list = document.getElementById("admin-users-list");
        const empty = document.getElementById("admin-empty");

        if (!users || users.length === 0) {
            list.innerHTML = "";
            empty.style.display = "block";
            empty.textContent = "No users found.";
            document.getElementById("admin-status").textContent = "";
            return;
        }

        empty.style.display = "none";
        list.innerHTML = users
            .map(
                (u) =>
                    `<div class="admin-user-item" onclick="loadUserHistory('${u.user_id}')">
                        <div class="admin-user-info">
                            <strong>User ${u.user_id}</strong>
                            <span>${u.message_count} messages | ${u.favorites} favorites</span>
                        </div>
                        <span class="admin-user-date">Since ${u.first_seen ? new Date(u.first_seen).toLocaleDateString() : "?"}</span>
                    </div>`
            )
            .join("");
        document.getElementById("admin-status").textContent = `Loaded ${users.length} users.`;
    } catch (err) {
        document.getElementById("admin-status").textContent = "Error: " + err.message;
    }
}

async function loadUserHistory(userId) {
    const url = getAdminUrl();
    if (!url) return;

    try {
        const res = await fetch(url + "/api/history/" + userId);
        const history = await res.json();
        const panel = document.getElementById("admin-history-panel");
        const title = document.getElementById("admin-history-title");
        const msgs = document.getElementById("admin-history-messages");

        title.textContent = "Chat History - User " + userId;
        panel.style.display = "block";

        if (!history || history.length === 0) {
            msgs.innerHTML = '<div class="empty-state">No messages.</div>';
            return;
        }

        msgs.innerHTML = history
            .map((msg) => {
                const isUser = msg.role === "user";
                const t = msg.time ? new Date(msg.time).toLocaleString() : "";
                return `<div class="history-msg ${isUser ? "history-user" : "history-bot"}">
                    <div class="history-role">${isUser ? "User" : "Bot"} (${t})</div>
                    <div class="history-text">${escapeHtml(msg.content)}</div>
                </div>`;
            })
            .join("");
    } catch (err) {
        document.getElementById("admin-status").textContent = "Error loading history: " + err.message;
    }
}

function closeAdminHistory() {
    document.getElementById("admin-history-panel").style.display = "none";
}

async function sendChat() {
    const input = document.getElementById("chat-input");
    const msg = input.value.trim();
    if (!msg) return;
    input.value = "";

    const chatDiv = document.getElementById("chat-messages");

    const professionalKeywords = [
        "skill", "project", "education", "experience", "service", "contact",
        "email", "phone", "portfolio", "github", "cv", "resume", "hire",
        "work", "develop", "code", "program", "web", "app", "design",
        "manager", "goal", "achievement", "about", "technology", "collaborate",
        "team", "plan", "build", "create", "framework", "language", "database",
        "frontend", "backend", "fullstack", "react", "node", "php", "sql",
        "html", "css", "javascript", "python", "university", "college",
        "diploma", "degree", "job", "career", "company", "client", "freelance",
        "project management", "agile", "scrum", "who are you", "tell me about",
        "what do you do", "what can you do", "profile", "interest", "career",
        "certificate", "qualification", "study", "graduate", "employ", "salary",
        "demo", "portfolio", "link", "url", "website",
    ];
    const isPersonal = !professionalKeywords.some((kw) =>
        msg.toLowerCase().includes(kw)
    );

    chatDiv.innerHTML += `<div class="chat-bubble user">${escapeHtml(msg)}</div>`;
    chatDiv.scrollTop = chatDiv.scrollHeight;

    const data = loadData();
    data.chat_count = (data.chat_count || 0) + 1;
    if (!data.chat_history) data.chat_history = [];
    data.chat_history.push({ role: "user", content: msg, time: new Date().toISOString() });
    saveData(data);
    addRecent("AI chat: " + msg.substring(0, 30));

    if (isPersonal) {
        chatDiv.innerHTML += `<div class="chat-bubble bot">For personal questions, please use the <strong>Telegram bot</strong> for a private response.</div>`;
        chatDiv.scrollTop = chatDiv.scrollHeight;
        const d = loadData();
        if (!d.chat_history) d.chat_history = [];
        d.chat_history.push({
            role: "assistant",
            content: "For personal questions, please use the Telegram bot for a private response.",
            time: new Date().toISOString(),
        });
        saveData(d);
        return;
    }

    chatDiv.innerHTML += `<div class="chat-bubble bot" id="loading-dots"><div class="loading-dots"><span></span><span></span><span></span></div></div>`;
    chatDiv.scrollTop = chatDiv.scrollHeight;

    try {
        const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: "Bearer " + getApiKey(),
            },
            body: JSON.stringify({
                model: "google/gemini-3.1-flash-lite",
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

        const d = loadData();
        if (!d.chat_history) d.chat_history = [];
        d.chat_history.push({ role: "assistant", content: reply, time: new Date().toISOString() });
        saveData(d);
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
