// REG_HOST/API_BASE — haqiqiy tizim (sr-new.ihma.uz), faqat o'qish uchun.
// Reestr tizimi (o'zimizning Django ilovamiz) manzili esa kodda qattiq
// yozilmagan: u chrome.storage'da saqlanadi va popup orqali o'zgartiriladi.
const DEFAULT_LETTER_HOST = "https://xatihmauz.pythonanywhere.com";
const REG_HOST = "https://sr-new.ihma.uz";

// Xat yaratish sahifasi "/reestr/create/" (Django URL tuzilishi:
// config/urls.py -> "reestr/" -> reestr/urls.py -> "create/"). Sahifaga kirish
// login talab qiladi (reestr_talab) — foydalanuvchi allaqachon shu saytga
// tizimga kirgan bo'lishi kerak (xuddi sr-new.ihma.uz'da bo'lgani kabi).
const LETTER_CREATE_PATH = "/reestr/create";

// Django login sahifasi — bu yerga tushib qolsak, xodim tizimga kirmagan.
const LETTER_LOGIN_PATH = "/login";

async function getLetterHost() {
  try {
    const saqlangan = await chrome.storage.sync.get("letterHost");
    return (saqlangan.letterHost || DEFAULT_LETTER_HOST).replace(/\/+$/, "");
  } catch {
    return DEFAULT_LETTER_HOST;
  }
}

async function getLetterOrigin() {
  const u = new URL(await getLetterHost());
  return { hostname: u.hostname, port: u.port, protocol: u.protocol };
}

const REG_ORIGIN_URL = new URL(REG_HOST);
const REG_ORIGIN = { hostname: REG_ORIGIN_URL.hostname, port: REG_ORIGIN_URL.port };
const API_BASE = `${REG_HOST}/api`;

// sr-new.ihma.uz javob bermay qolsa, kengaytma cheksiz kutib qolmasligi kerak —
// har bir so'rov shu muddatdan keyin bekor qilinadi.
const API_TIMEOUT_MS = 20000;

function waitForTabComplete(tabId, timeoutMs = 20000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(listener);
      reject(new Error("Sahifa yuklanishi kutilgan vaqtda tugamadi"));
    }, timeoutMs);

    function listener(tabId_, changeInfo) {
      if (tabId_ === tabId && changeInfo.status === "complete") {
        clearTimeout(timer);
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    }
    chrome.tabs.onUpdated.addListener(listener);

    chrome.tabs.get(tabId, (tab) => {
      if (chrome.runtime.lastError) return;
      if (tab && tab.status === "complete") {
        clearTimeout(timer);
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    });
  });
}

// Generic: find an already-open tab matching `matchFn(tabUrl)`, or open a
// new one at `createUrl`. Either way, focuses/activates it and waits for it
// to finish loading before returning its id.
async function findOrOpenTab(matchFn, createUrl) {
  const tabs = await chrome.tabs.query({});
  const candidates = tabs.filter((t) => t.url && matchFn(t.url));

  // Multiple matching tabs can be open at once (leftovers from earlier
  // testing, an /admin tab on the same origin, etc). Prefer the one the
  // user is actually looking at right now, then the most recently used one
  // — never just "whichever chrome.tabs.query happened to list first".
  candidates.sort((a, b) => {
    if (a.active !== b.active) return a.active ? -1 : 1;
    return (b.lastAccessed || 0) - (a.lastAccessed || 0);
  });
  const match = candidates[0];

  if (match) {
    await chrome.tabs.update(match.id, { active: true });
    await chrome.windows.update(match.windowId, { focused: true });
    if (match.status !== "complete") {
      await waitForTabComplete(match.id);
    }
    return match.id;
  }

  const newTab = await chrome.tabs.create({ url: createUrl, active: true });
  await waitForTabComplete(newTab.id);
  return newTab.id;
}

// Extracts the applicationId from a "/applications/<id>" detail-page URL, or
// null if the URL isn't on that page. sr-new.ihma.uz is a client-routed SPA:
// the id lives in the PATH (unlike the old system, which used ?id=... on
// "/registration/details/view").
function parseRegistrationId(url) {
  try {
    const u = new URL(url);
    if (u.hostname !== REG_ORIGIN.hostname || u.port !== REG_ORIGIN.port) return null;
    const m = u.pathname.replace(/\/+$/, "").match(/^\/applications\/(\d+)$/);
    return m ? m[1] : null;
  } catch {
    return null;
  }
}

// Looks across all open tabs for one already sitting on an application
// detail page and returns its applicationId. Multiple such tabs can be open
// at once — prefer the one the user is actually looking at right now, then
// the most recently used one (same tie-break as findOrOpenTab).
async function findOpenRegistrationApplicationId() {
  const tabs = await chrome.tabs.query({});
  const matches = tabs
    .map((t) => ({ tab: t, id: t.url ? parseRegistrationId(t.url) : null }))
    .filter((m) => m.id);

  if (!matches.length) return null;

  matches.sort((a, b) => {
    if (a.tab.active !== b.tab.active) return a.tab.active ? -1 : 1;
    return (b.tab.lastAccessed || 0) - (a.tab.lastAccessed || 0);
  });

  return matches[0].id;
}

// sr-new.ihma.uz keeps its access token in an httpOnly "Authorization"
// cookie (unlike the old system, which kept a plain, JS-readable token in
// sessionStorage) — so it can't be read via a content script anymore. The
// chrome.cookies API can read it directly, from the background service
// worker, without needing any tab open at all.
async function getAuthTokenFromCookie() {
  const cookie = await chrome.cookies.get({ url: `${REG_HOST}/`, name: "Authorization" });
  if (!cookie || !cookie.value) {
    throw new Error(
      "sr-new.ihma.uz sessiyasi topilmadi. O'sha saytda avval tizimga kiring."
    );
  }
  return cookie.value;
}

// Runs inside the letter page. Clicks the template card matching `template`
// so the page's own selectTemplate() runs (shows the right fields section,
// same as if the user had clicked it). Returns whether a matching card was
// found, so the caller can surface an error if the page markup ever changes.
function clickTemplateCard(template) {
  const card = document.querySelector(`.tpl-opt[data-template="${template}"]`);
  if (card) card.click();
  return !!card;
}

async function findOrOpenLetterTab() {
  const host = await getLetterHost();
  const origin = await getLetterOrigin();
  return findOrOpenTab((url) => {
    try {
      const u = new URL(url);
      if (u.hostname !== origin.hostname || u.port !== origin.port) return false;
      // Only the actual create/edit form page has the template selector —
      // exclude other pages on the same origin (dashboard, login, ariza app).
      const path = u.pathname.replace(/\/+$/, "") || "/";
      return path === LETTER_CREATE_PATH;
    } catch {
      return false;
    }
  }, `${host}${LETTER_CREATE_PATH}/`);
}

// Tab yuklangach, haqiqatan xat formasida turibmizmi? Django login talab
// qilsa, /login/ ga yo'naltiradi — bunda "shablon kartasi topilmadi" degan
// chalg'ituvchi xato o'rniga aniq sabab aytiladi.
async function ensureLetterPageReady(tabId) {
  const tab = await chrome.tabs.get(tabId);
  let path = "";
  try {
    path = new URL(tab.url || "").pathname.replace(/\/+$/, "") || "/";
  } catch {
    path = "";
  }
  if (path.startsWith(LETTER_LOGIN_PATH)) {
    throw new Error(
      "Reestr tizimiga kirilmagan. Ochilgan sahifada login qiling va qaytadan urinib ko'ring."
    );
  }
  if (path !== LETTER_CREATE_PATH) {
    throw new Error(
      `Xat yaratish sahifasi ochilmadi (${tab.url || "manzil noma'lum"}). ` +
      "Popup'dagi server manzili to'g'riligini tekshiring."
    );
  }
}

function normalizeDateForInput(value) {
  if (!value) return "";
  const s = String(value).trim();
  let m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) return `${m[1]}-${m[2]}-${m[3]}`;
  m = s.match(/^(\d{1,2})[.\/-](\d{1,2})[.\/-](\d{4})/);
  if (m) {
    const d = m[1].padStart(2, "0");
    const mo = m[2].padStart(2, "0");
    return `${m[3]}-${mo}-${d}`;
  }
  return "";
}

// ============================================================
// AUTOFILL (Django xat formasini to'ldirish, /reestr/create/)
// Runs inside the target page. Must be self-contained apart from the
// `payload` argument.
// ============================================================
function fillLetterForm(payload) {
  function setVal(id, value) {
    const el = document.getElementById(id);
    if (!el || value === undefined || value === null || value === "") return false;
    el.value = value;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  const filled = {
    arizaID: false, arizaMaqsadi: false, arizaVaqti: false, isQayta: false, tizimSababi: false,
  };

  filled.arizaID = setVal("arizaID", payload.arizaID);
  filled.arizaMaqsadi = setVal("arizaMaqsadi", payload.arizaMaqsadi);
  filled.arizaVaqti = setVal("arizaVaqti", payload.arizaVaqti);

  if (payload.isQayta === true || payload.isQayta === false) {
    const radio = document.getElementById(payload.isQayta ? "isQaytaHa" : "isQaytaYoq");
    if (radio) {
      radio.checked = true;
      radio.dispatchEvent(new Event("change", { bubbles: true }));
      filled.isQayta = true;
    }
  }

  // "Rad etish" / "To'lov to'xtatilgan" — bitta tayyor sabab matni (tizim
  // o'zi hisoblab bergan xulosa), eski itemized ko'chmas mulk/avto/rasmiy
  // daromad ro'yxatlari o'rniga (qarang: reestr/templates/reestr/create.html
  // "Tizim tomonidan aniqlangan sabab" bo'limi).
  if (payload.tizimSababi) {
    const toggle = document.getElementById("tizimSababiToggle");
    if (toggle && !toggle.checked) {
      toggle.checked = true;
      toggle.dispatchEvent(new Event("change", { bubbles: true }));
    }
    filled.tizimSababi = setVal("tizimSababiMatni", payload.tizimSababi);
  }

  return { filled };
}

async function fillLetterCommonFields(letterTabId, letterPayload) {
  const fillInjection = await chrome.scripting.executeScript({
    target: { tabId: letterTabId },
    world: "MAIN",
    func: fillLetterForm,
    args: [letterPayload],
  });
  return fillInjection && fillInjection[0] && fillInjection[0].result;
}

// ============================================================
// sr-new.ihma.uz API OQIMI
// ============================================================
async function apiFetch(url, token, { method = "GET", body } = {}) {
  // AbortController'siz javob bermayotgan server kengaytmani muzlatib
  // qo'yardi: badge "..." da qotib qolar, foydalanuvchi nima bo'layotganini
  // bilmasdi.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

  let res;
  try {
    res = await fetch(url, {
      method,
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error(
        `Server ${API_TIMEOUT_MS / 1000} soniyada javob bermadi. ` +
        "Internet aloqasini yoki sr-new.ihma.uz ishlayotganini tekshiring."
      );
    }
    throw new Error(`Serverga ulanib bo'lmadi: ${err.message}`);
  } finally {
    clearTimeout(timer);
  }

  if (res.status === 401 || res.status === 403) {
    throw new Error(
      "sr-new.ihma.uz sessiyasi tugagan. O'sha sahifada qaytadan tizimga kiring."
    );
  }
  if (!res.ok) {
    throw new Error(`API xatolik: HTTP ${res.status} (${new URL(url).pathname})`);
  }

  try {
    return await res.json();
  } catch {
    throw new Error(`Server tushunarsiz javob qaytardi: ${new URL(url).pathname}`);
  }
}

// Uchala "oddiy" shablon (Tasdiqlash/Tayinlash/Ariza kiritilgan) ham faqat
// "Asosiy ma'lumotlar" (Ariza raqami/maqsadi/sanasi) talab qiladi —
// Application/Get javobi buni to'g'ridan-to'g'ri beradi, alohida
// dastur/nom qidiruvi kerak emas (eski tizimda SocialProgramme ro'yxatidan
// programmeId orqali qidirilardi).
function commonLetterPayload(registration) {
  return {
    arizaID: registration.id != null ? String(registration.id) : "",
    arizaMaqsadi: registration.programmeName || "",
    arizaVaqti: normalizeDateForInput(registration.applicationDate),
  };
}

async function runCommonFieldsFill(template, letterTabId, registration) {
  const payload = commonLetterPayload(registration);
  const fillReport = await fillLetterCommonFields(letterTabId, payload);
  return { template, payload, fillReport };
}

// "Rad etish" va "To'lov to'xtatilgan" — ikkalasi ham bitta tayyor sabab
// matnini (tizimning moslik baholash xulosasi, assessment.rejectReasonText)
// oladi va Django formasidagi "Tizim tomonidan aniqlangan sabab" maydoniga
// qo'yadi. Eski itemized (ko'chmas mulk/avto/rasmiy daromad) ro'yxatlari
// endi qurilmaydi — sr-new.ihma.uz'da bunga mos ~20 xil manba bor va
// ularning huquqiy tasnifi aniq emas, shuning uchun tizim o'zi tayyorlagan
// bitta jumla ishlatiladi (qarang: reestr/shablon_qurish.py qur_rad).
async function runRadFill(template, id, letterTabId, registration, statusCode, token) {
  const payload = {
    ...commonLetterPayload(registration),
    isQayta: statusCode === "RECHECK_REJECTED",
    tizimSababi: "",
  };

  try {
    const revisions = await apiFetch(
      `${API_BASE}/Eligibility/GetRevisionsByApplication?applicationId=${encodeURIComponent(id)}`,
      token
    );
    const current = (revisions || []).find((r) => r.isCurrent) || (revisions || [])[0];
    if (current) {
      const summary = await apiFetch(
        `${API_BASE}/Eligibility/GetBySummary?applicationId=${encodeURIComponent(id)}&summaryId=${current.id}`,
        token
      );
      payload.tizimSababi = (summary && summary.assessment && summary.assessment.rejectReasonText) || "";
    }
  } catch (err) {
    // Sabab matnini olib bo'lmasa ham, umumiy maydonlar (ariza raqami/
    // maqsadi/sanasi) baribir to'ldiriladi — xodim sabab matnini qo'lda
    // yozadi (popup shu holatni alohida ko'rsatadi).
  }

  const fillReport = await fillLetterCommonFields(letterTabId, payload);
  return { template, payload, fillReport };
}

// sr-new'dan kelgan holatga qarab qaysi xat shabloni mosligini aniqlaydi.
// Status kodlari (Reference/GetStatuses) eski tizimdagi bilan bir xil:
//   "APPROVED"          -> "tasdiqlandi"
//   "WAITING LIST"       -> "tayinlandi"
//   "PENDING APPROVAL"   -> "arizaKiritilgan"
//   "PAYMENT_SUSPENDED"  -> "toxtatilgan" (yangi: to'lov to'xtatilgan)
//   "REJECTED" / "RECHECK_REJECTED" (yoki ichida "REJECT" so'zi bo'lgan
//   boshqa variant) -> "rad"
// Hech biri mos kelmasa, eng neytral variant — "arizaKiritilgan" qaytariladi.
function decideTemplate(statusCode) {
  const code = String(statusCode || "").trim().toUpperCase();
  if (code === "APPROVED") return "tasdiqlandi";
  if (code === "WAITING LIST") return "tayinlandi";
  if (code === "PENDING APPROVAL") return "arizaKiritilgan";
  if (code === "PAYMENT_SUSPENDED") return "toxtatilgan";
  if (code.includes("REJECT")) return "rad";
  return "arizaKiritilgan";
}

// Entry point for the "To'ldirish" button. Self-sufficient given just the
// id: opens/finds the letter-create page, asks sr-new.ihma.uz what the
// ariza's real outcome is, clicks the matching template card on the page
// itself (so the user sees the same selection they'd have made by hand),
// then fills it from the matching source.
async function runSmartFill(id) {
  const token = await getAuthTokenFromCookie();
  const registration = await apiFetch(
    `${API_BASE}/Application/Get?id=${encodeURIComponent(id)}`,
    token
  );
  const statuses = await apiFetch(`${API_BASE}/Reference/GetStatuses`, token);
  const codeById = {};
  (statuses || []).forEach((s) => { codeById[s.id] = s.code; });
  const statusCode = codeById[registration.statusId] || "";
  const template = decideTemplate(statusCode);

  const letterTabId = await findOrOpenLetterTab();
  await ensureLetterPageReady(letterTabId);

  const cardInjection = await chrome.scripting.executeScript({
    target: { tabId: letterTabId },
    func: clickTemplateCard,
    args: [template],
  });
  const cardFound = cardInjection && cardInjection[0] && cardInjection[0].result;
  if (!cardFound) {
    throw new Error(
      `Shablon kartasi topilmadi (data-template="${template}"). ` +
      "Sahifani yangilab, qaytadan urinib ko'ring."
    );
  }

  if (template === "rad" || template === "toxtatilgan") {
    return runRadFill(template, id, letterTabId, registration, statusCode, token);
  }
  return runCommonFieldsFill(template, letterTabId, registration);
}

// ============================================================
// MESSAGE ROUTING
// ============================================================
function notifyPopup(message) {
  chrome.runtime.sendMessage(message, () => {
    // No popup listening right now — ignore "Receiving end does not exist".
    void chrome.runtime.lastError;
  });
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message) return;

  if (message.type === "GET_ACTIVE_APPLICATION_ID") {
    findOpenRegistrationApplicationId().then((id) => {
      sendResponse({ id });
    });
    return true;
  }

  if (message.type === "RUN_AUTOFILL") {
    chrome.action.setBadgeText({ text: "..." });
    chrome.action.setBadgeBackgroundColor({ color: "#f39c12" });

    runSmartFill(message.id)
      .then((result) => {
        chrome.storage.local.set({
          lastAutofillId: message.id,
          lastAutofillResult: result,
          lastAutofillError: null,
        });
        chrome.action.setBadgeText({ text: "OK" });
        chrome.action.setBadgeBackgroundColor({ color: "#2e7d32" });
        notifyPopup({ type: "AUTOFILL_DONE", id: message.id, ...result });
      })
      .catch((err) => {
        chrome.storage.local.set({
          lastAutofillId: message.id,
          lastAutofillResult: null,
          lastAutofillError: err.message,
        });
        chrome.action.setBadgeText({ text: "!" });
        chrome.action.setBadgeBackgroundColor({ color: "#c0392b" });
        notifyPopup({ type: "AUTOFILL_ERROR", id: message.id, error: err.message });
      });

    sendResponse({ started: true });
    return true;
  }
});
