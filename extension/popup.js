const detectedEl = document.getElementById("detected");
const fillBtn = document.getElementById("fillBtn");
const statusEl = document.getElementById("status");

let lastId = null;

function showStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.className = isError ? "error" : "ok";
}

const TEMPLATE_NOMLARI = {
  rad: "Rad etish",
  toxtatilgan: "To'lov to'xtatilgan",
  tasdiqlandi: "Tasdiqlash",
  tayinlandi: "Tayinlash",
  arizaKiritilgan: "Ariza kiritilgan",
};

// "Rad etish" uchun avtomatik belgilanadigan checkbox'lar — matnning o'zi
// Django tomonida qattiq yozilgan (qarang: reestr/docx_generator.py).
const RAD_SABAB_NOMLARI = {
  yangiAvtoRad: "Yangi avtomobil",
  kopAvtoRad: "Bir nechta avtomobil",
  kochmasMulkRad: "Ortiqcha ko'chmas mulk",
  daromadRad: "Rasmiy daromad",
};

function describeFillResult(message) {
  const nom = TEMPLATE_NOMLARI[message.template];
  if (!nom) {
    return {
      text: `"${message.template}" shabloni uchun hali qo'llab-quvvatlanmaydi.`,
      isError: true,
    };
  }

  const f = message.fillReport;
  const filled = (f && f.filled) || {};
  const parts = [];
  if (filled.arizaID) parts.push("Ariza raqami");
  if (filled.arizaMaqsadi) parts.push("Ariza Maqsadi");
  if (filled.arizaVaqti) parts.push("Ariza sanasi");
  if (filled.isQayta) parts.push("Holat");
  if (filled.tizimSababi) parts.push("Sabab matni");
  const radSabablari = Object.keys(RAD_SABAB_NOMLARI).filter((k) => filled[k]);
  radSabablari.forEach((k) => parts.push(RAD_SABAB_NOMLARI[k]));

  if (!parts.length) {
    return { text: `Reestr tizimi (${nom}) ochildi, lekin hech qanday mos ma'lumot topilmadi.`, isError: true };
  }

  let ogohlantirish = "";
  if (message.template === "rad" && !radSabablari.length) {
    ogohlantirish = " Avtomatik aniqlangan sabab topilmadi — kerakli katakchani (masalan \"Uyda bo'lmagan\") qo'lda belgilang.";
  }
  if (message.template === "toxtatilgan" && !filled.tizimSababi) {
    ogohlantirish = " Sabab matni topilmadi — qo'lda kiriting.";
  }
  if (message.template === "tasdiqlandi") {
    ogohlantirish = " To'lov ma'lumotlarini qo'lda kiriting (hali avtomatik to'ldirilmaydi).";
  }

  return {
    text: `Reestr tizimi (${nom}) to'ldirildi: ${parts.join(", ")}. Tekshirib chiqing va o'zingiz yuboring.${ogohlantirish}`,
    isError: false,
  };
}

/* ---------------- SERVER MANZILI ----------------
   Manzil kodda qattiq yozilmagan: kengaytma uni chrome.storage'dan oladi.
   Shu sababli ilova serverga chiqarilganda fayllarni tahrirlash shart emas. */
const DEFAULT_LETTER_HOST = "http://127.0.0.1:8000";
const hostInput = document.getElementById("hostInput");
const hostSaveBtn = document.getElementById("hostSaveBtn");
const hostStatus = document.getElementById("hostStatus");

function hostStatusKorsat(matn, xatomi) {
  hostStatus.textContent = matn;
  hostStatus.style.color = xatomi ? "#c0392b" : "";
}

async function hostniYuklash() {
  const { letterHost } = await chrome.storage.sync.get("letterHost");
  hostInput.value = letterHost || DEFAULT_LETTER_HOST;
}

hostSaveBtn.addEventListener("click", async () => {
  const xom = hostInput.value.trim().replace(/\/+$/, "");
  let origin;
  try {
    const u = new URL(xom);
    if (!/^https?:$/.test(u.protocol)) throw new Error("protokol");
    origin = `${u.protocol}//${u.host}/*`;
  } catch {
    hostStatusKorsat("Manzil noto'g'ri. Masalan: https://ihma.uz", true);
    return;
  }

  // Yangi manzilga so'rov yuborish uchun foydalanuvchidan ruxsat so'raladi.
  let ruxsat = true;
  try {
    ruxsat = await chrome.permissions.request({ origins: [origin] });
  } catch {
    ruxsat = true;   // ruxsat allaqachon manifestda bo'lsa
  }
  if (!ruxsat) {
    hostStatusKorsat("Ruxsat berilmadi — manzil saqlanmadi.", true);
    return;
  }

  await chrome.storage.sync.set({ letterHost: xom });
  hostStatusKorsat("Saqlandi: " + xom, false);
});

// Asks the background service worker which applicationId is currently open
// on a sr-new.ihma.uz/applications/<id> tab. No manual id entry anymore —
// the user is expected to already have that ariza open.
function detectApplicationId() {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ type: "GET_ACTIVE_APPLICATION_ID" }, (response) => {
      void chrome.runtime.lastError;
      resolve(response && response.id ? response.id : null);
    });
  });
}

async function init() {
  // Clear any "done" badge left from a background run.
  chrome.action.setBadgeText({ text: "" });

  const id = await detectApplicationId();
  lastId = id;

  if (!id) {
    detectedEl.textContent =
      "❌ Ariza sahifasi topilmadi. Avval sr-new.ihma.uz'da kerakli arizani oching (/applications/<id>).";
    fillBtn.disabled = true;
  } else {
    detectedEl.innerHTML = `✅ Aniqlangan ID: <span class="id">${id}</span>`;
    fillBtn.disabled = false;
  }

  const stored = await chrome.storage.local.get([
    "lastAutofillId",
    "lastAutofillResult",
    "lastAutofillError",
  ]);

  // If a previous background run finished for this exact id, show it
  // immediately — this is what survives the popup being auto-closed when a
  // tab steals window focus.
  if (id && stored.lastAutofillId === id) {
    if (stored.lastAutofillResult) {
      const { text, isError } = describeFillResult(stored.lastAutofillResult);
      showStatus(text, isError);
    } else if (stored.lastAutofillError) {
      showStatus("Xatolik: " + stored.lastAutofillError, true);
    }
  }
}

fillBtn.addEventListener("click", () => {
  if (!lastId) return;
  const id = lastId;

  fillBtn.disabled = true;
  showStatus(
    "Ariza holati tekshirilmoqda, mos shablon avtomatik aniqlanmoqda va to'ldirilmoqda... (popup yopilib qolsa ham davom etadi, qayta oching)"
  );

  // The actual work happens in the background service worker so it keeps
  // running even if this popup gets closed (Chrome auto-closes popups when
  // window focus shifts to the tab being opened/activated).
  chrome.runtime.sendMessage({ type: "RUN_AUTOFILL", id }, () => {
    void chrome.runtime.lastError;
    fillBtn.disabled = false;
  });
});

chrome.runtime.onMessage.addListener((message) => {
  if (!message || message.id !== lastId) return;

  if (message.type === "AUTOFILL_DONE") {
    fillBtn.disabled = false;
    const { text, isError } = describeFillResult(message);
    showStatus(text, isError);
  } else if (message.type === "AUTOFILL_ERROR") {
    fillBtn.disabled = false;
    showStatus("Xatolik: " + message.error, true);
  }
});

hostniYuklash();
init();
