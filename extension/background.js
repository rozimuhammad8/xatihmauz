// REG_HOST/API_BASE — haqiqiy tizim (sr-new.ihma.uz), faqat o'qish uchun.
// Reestr tizimi (o'zimizning Django ilovamiz) manzili har doim shu — endi
// sozlanmaydi (avval popup orqali o'zgartirish mumkin edi, lekin bu ikki
// faylda ikkita mustaqil DEFAULT_LETTER_HOST doimiysi orqali amalga
// oshirilgan edi va ular mos kelmay qolgan holat haqiqiy xatoga sabab
// bo'lgan — shuning uchun endi bitta qattiq yozilgan manzil ishlatiladi).
const LETTER_HOST = "https://xatihmauz.pythonanywhere.com";
const REG_HOST = "https://sr-new.ihma.uz";

// Xat yaratish sahifasi "/reestr/create/" (Django URL tuzilishi:
// config/urls.py -> "reestr/" -> reestr/urls.py -> "create/"). Sahifaga kirish
// login talab qiladi (reestr_talab) — foydalanuvchi allaqachon shu saytga
// tizimga kirgan bo'lishi kerak (xuddi sr-new.ihma.uz'da bo'lgani kabi).
const LETTER_CREATE_PATH = "/reestr/create";

// Django login sahifasi — bu yerga tushib qolsak, xodim tizimga kirmagan.
const LETTER_LOGIN_PATH = "/login";

const LETTER_ORIGIN_URL = new URL(LETTER_HOST);
const LETTER_ORIGIN = {
  hostname: LETTER_ORIGIN_URL.hostname,
  port: LETTER_ORIGIN_URL.port,
  protocol: LETTER_ORIGIN_URL.protocol,
};

const REG_ORIGIN_URL = new URL(REG_HOST);
const REG_ORIGIN = { hostname: REG_ORIGIN_URL.hostname, port: REG_ORIGIN_URL.port };
const API_BASE = `${REG_HOST}/api`;

// sr-new.ihma.uz javob bermay qolsa, kengaytma cheksiz kutib qolmasligi kerak —
// har bir so'rov shu muddatdan keyin bekor qilinadi.
const API_TIMEOUT_MS = 20000;

// `checkAlreadyComplete=true` (standart) — agar tab AVVALDAN "complete"
// holatida bo'lsa, darhol qaytadi (findOrOpenTab uchun to'g'ri: allaqachon
// yuklangan tabni qayta kutish shart emas). `false` esa shu tekshiruvni
// o'tkazib yuboradi va faqat KEYINGI "complete" hodisasini kutadi — bu
// chrome.tabs.reload() dan KEYIN kerak: reload chaqirilgan zahoti tab
// holatini so'rasak, u hali ESKI "complete" holatida qolgan bo'lishi mumkin
// (yangi yuklanish hali "loading"ga o'tmagan), shu sababli darhol (noto'g'ri)
// qaytib ketardi — aynan shu sabab tokenni yangilash birinchi urinishda
// ishlamay qoldi.
function waitForTabComplete(tabId, timeoutMs = 20000, checkAlreadyComplete = true) {
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

    if (!checkAlreadyComplete) return;

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

// sr-new.ihma.uz'ning access-token cookie'si taxminan 8 soatdan keyin
// tugaydi, lekin sahifaning o'zi buni FAQAT to'liq qayta yuklanganda
// (RefreshToken so'rovi orqali) yangilaydi — SPA ichidagi navigatsiya bunga
// yetarli emas. Foydalanuvchi ariza sahifasini ochib qo'yib, uzoq vaqtdan
// keyin (masalan ertasi kuni) "To'ldirish"ni bossa, u hali ham "tizimga
// kirgan" ko'rinadi (sahifa hech narsa demaydi), lekin cookie'dagi token
// aslida eskirgan bo'ladi — natijada "sessiya tugagan" xatosi chiqadi,
// garchi foydalanuvchi chiqib ketmagan bo'lsa ham. Shuning uchun tokenni
// o'qishdan OLDIN o'sha tab avtomatik qayta yuklanadi — bu sessiya
// tugagan-tugamaganidan qat'i nazar zararsiz (agar hali tugamagan bo'lsa,
// reload shunchaki tokenni yangilab qo'yadi).
function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function refreshRegistrationTab(id) {
  const tabs = await chrome.tabs.query({});
  const match = tabs.find((t) => t.url && parseRegistrationId(t.url) === String(id));
  if (!match) return; // tab topilmadi (yopilgan bo'lishi mumkin) — token o'zi sinaladi
  await chrome.tabs.reload(match.id);
  try {
    // checkAlreadyComplete=false: reload chaqirilgan zahoti tab hali ham
    // ESKI "complete" holatida ko'rinishi mumkin — shu sabab bilan avval
    // shu tekshiruv tufayli funksiya darhol (haqiqiy yuklanishni kutmasdan)
    // qaytib ketardi.
    await waitForTabComplete(match.id, 20000, false);
  } catch {
    return;
  }
  // Sahifa brauzer darajasida "yuklandi" (complete) holatiga yetgach ham,
  // RefreshToken so'rovining o'zi sahifaning ishga tushirish skripti orqali
  // ASINXRON amalga oshadi (birinchi sinovda aynan shu sabab ishlamay
  // qoldi — cookie hali yangilanmagan paytda o'qib qo'yilgan edi). Shuning
  // uchun qisqa qo'shimcha kutish beriladi.
  await delay(1500);
}

// sr-new.ihma.uz keeps its access token in an httpOnly "Authorization"
// cookie (unlike the old system, which kept a plain, JS-readable token in
// sessionStorage) — so it can't be read via a content script anymore. The
// chrome.cookies API can read it directly, from the background service
// worker, without needing any tab open at all.
//
// ihma.uz'da bir nechta sub-domen bor (sr.ihma.uz, sr-new.ihma.uz, va
// boshqalar), har biri o'zining "Authorization" nomli cookie'sini
// o'rnatishi mumkin. Agar ulardan biri cookie'sini butun ".ihma.uz"
// domeniga (sub-domenidan mustaqil) o'rnatgan bo'lsa, u sr-new.ihma.uz'ga
// so'rov yuborilganda ham qo'shilib ketishi mumkin edi. Shuning uchun
// olingan cookie'ning domeni ANIQ "sr-new.ihma.uz" ekanligi tekshiriladi —
// boshqacha bo'lsa, tokendan foydalanish o'rniga aniq xato ko'rsatiladi
// (chrome.cookies.getAll() bu Chrome versiyasida url-filter bilan doim
// bo'sh natija qaytargani uchun ishlatilmadi — get() esa ishonchli ishlaydi,
// faqat domenni qo'lda tasdiqlash kerak).
async function getAuthTokenFromCookie() {
  const cookie = await chrome.cookies.get({ url: `${REG_HOST}/`, name: "Authorization" });
  if (!cookie || !cookie.value) {
    throw new Error(
      "sr-new.ihma.uz sessiyasi topilmadi. O'sha saytda avval tizimga kiring."
    );
  }
  if (cookie.domain !== REG_ORIGIN.hostname) {
    throw new Error(
      `Token noto'g'ri domenga tegishli (${cookie.domain}, kutilgan: ` +
      `${REG_ORIGIN.hostname}) — ehtimol ihma.uz'ning boshqa sahifasi bilan ` +
      "aralashib qoldi. sr-new.ihma.uz sahifasini qayta yuklab ko'ring."
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

function findOrOpenLetterTab() {
  return findOrOpenTab((url) => {
    try {
      const u = new URL(url);
      if (u.hostname !== LETTER_ORIGIN.hostname || u.port !== LETTER_ORIGIN.port) return false;
      // Only the actual create/edit form page has the template selector —
      // exclude other pages on the same origin (dashboard, login, ariza app).
      const path = u.pathname.replace(/\/+$/, "") || "/";
      return path === LETTER_CREATE_PATH;
    } catch {
      return false;
    }
  }, `${LETTER_HOST}${LETTER_CREATE_PATH}/`);
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
  function setCheck(id, value) {
    const el = document.getElementById(id);
    if (!el || !value) return false;
    el.checked = true;
    el.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  const filled = {
    arizaID: false, arizaMaqsadi: false, arizaVaqti: false, isQayta: false,
    tizimSababi: false, yangiAvtoRad: false, kopAvtoRad: false, kochmasMulkRad: false, daromadRad: false,
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

  // "Rad etish" — checkboxlar orqali (qarang: runRadFill/CRITERION_TO_CHECKBOX).
  // Matnning o'zi Django tomonida qattiq yozilgan, shuning uchun bu yerda
  // faqat mos katakcha belgilanadi.
  filled.yangiAvtoRad = setCheck("yangiAvtoRad", payload.yangiAvtoRad);
  filled.kopAvtoRad = setCheck("kopAvtoRad", payload.kopAvtoRad);
  filled.kochmasMulkRad = setCheck("kochmasMulkRad", payload.kochmasMulkRad);
  filled.daromadRad = setCheck("daromadRad", payload.daromadRad);

  // "To'lov to'xtatilgan" — bitta tayyor sabab matni (tizim o'zi hisoblab
  // bergan xulosa) erkin matn maydoniga qo'yiladi (qarang: runToxtatilganFill).
  if (payload.tizimSababi !== undefined) {
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

  // 401 va 403 ikki xil sabab: 401 — token haqiqatan yaroqsiz/eskirgan
  // (qaytadan kirish kerak). 403 — token yaroqli, lekin shu hisobda o'sha
  // amal (masalan "Moslik baholash" bo'limini ko'rish) uchun ruxsat yo'q —
  // bu sessiya emas, balki ROL/RUXSAT masalasi (sr-new.ihma.uz'da
  // administratorga murojaat qilish kerak). Ikkalasini bitta "sessiya
  // tugagan" deb ko'rsatish chalg'ituvchi edi — xodim hali tizimga kirgan
  // bo'lsa ham shu xabarni ko'rib chalkashib qolgan holat aynan shu edi.
  if (res.status === 401) {
    throw new Error(
      "sr-new.ihma.uz sessiyasi tugagan. O'sha sahifada qaytadan tizimga kiring."
    );
  }
  if (res.status === 403) {
    throw new Error(
      `sr-new.ihma.uz sizning hisobingizga bu amal uchun ruxsat bermadi ` +
      `(${new URL(url).pathname}). Bu sessiya tugashi emas — hisobingizda ` +
      `kerakli bo'limga (masalan "Moslik baholash") kirish huquqi yo'qligi ` +
      `mumkin. sr-new.ihma.uz administratoriga murojaat qiling.`
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

// Joriy (isCurrent) baholash xulosasini (Eligibility/GetBySummary) o'qiydi —
// "rad" va "toxtatilgan" ikkalasi ham shu manbadan foydalanadi, faqat undan
// olingan ma'lumotni har biri boshqacha ishlatadi (pastga qarang).
async function fetchCurrentSummary(id, token) {
  const revisions = await apiFetch(
    `${API_BASE}/Eligibility/GetRevisionsByApplication?applicationId=${encodeURIComponent(id)}`,
    token
  );
  const current = (revisions || []).find((r) => r.isCurrent) || (revisions || [])[0];
  if (!current) return null;
  return apiFetch(
    `${API_BASE}/Eligibility/GetBySummary?applicationId=${encodeURIComponent(id)}&summaryId=${current.id}`,
    token
  );
}

// household.checks[] dagi (passed:false) kriteriy kodini Django formasidagi
// checkbox id'siga moslashtiradi. Har bir checkbox uchun ANIQ matn
// reestr/docx_generator.py (SABAB_YANGI_AVTO/SABAB_KOP_AVTO/...) da qattiq
// yozilgan — o'sha matnlar sr-new.ihma.uz'ning bir qancha haqiqiy rad
// etilgan arizasidan (rejectReasonText) olingan, so'zma-so'z bir xil chiqadi.
const CRITERION_TO_CHECKBOX = {
  HH_NEW_VEHICLES_CHECK: "yangiAvtoRad",
  HH_VEHICLES_CHECK: "kopAvtoRad",
  HH_PROPERTIES_CHECK: "kochmasMulkRad",
  HH_INCOME_CHECK: "daromadRad",
};

// "Rad etish" — erkin matn emas, checkboxlar orqali ishlaydi: sr-new.ihma.uz
// javobidagi har bir mos tushgan (passed:false) kriteriy uchun mos
// checkbox belgilanadi, matnning o'zi Django tomonida allaqachon tayyor
// (qarang: CRITERION_TO_CHECKBOX yuqorida). "Uyda bo'lmagan" avtomatik
// aniqlanmaydi — xodim o'zi belgilaydi (sr-new'da bunga mos kriteriy yo'q).
async function runRadFill(id, letterTabId, registration, statusCode, token) {
  const payload = {
    ...commonLetterPayload(registration),
    isQayta: statusCode === "RECHECK_REJECTED",
    yangiAvtoRad: false,
    kopAvtoRad: false,
    kochmasMulkRad: false,
    daromadRad: false,
  };

  try {
    const summary = await fetchCurrentSummary(id, token);
    const checks = (summary && summary.household && summary.household.checks) || [];
    checks.forEach((c) => {
      const field = CRITERION_TO_CHECKBOX[c.code];
      if (field && c.passed === false) payload[field] = true;
    });
  } catch (err) {
    // Sabablarni olib bo'lmasa ham, umumiy maydonlar (ariza raqami/maqsadi/
    // sanasi) baribir to'ldiriladi — xodim kerakli katakchani qo'lda
    // belgilaydi (popup shu holatni alohida ko'rsatadi).
  }

  const fillReport = await fillLetterCommonFields(letterTabId, payload);
  return { template: "rad", payload, fillReport };
}

// "To'lov to'xtatilgan" — sr-new.ihma.uz'da hali doimiy kriteriy-checkbox
// xaritasi yo'q (sabablar juda xilma-xil: bandlik, so'rovnoma va h.k.),
// shuning uchun bu shablon hamon tizimning tayyor jumlasini
// (assessment.rejectReasonText) to'g'ridan-to'g'ri erkin matn maydoniga
// qo'yadi (qarang: reestr/templates/reestr/create.html "toxtatilganFields").
async function runToxtatilganFill(id, letterTabId, registration, token) {
  const payload = { ...commonLetterPayload(registration), tizimSababi: "" };

  try {
    const summary = await fetchCurrentSummary(id, token);
    payload.tizimSababi = (summary && summary.assessment && summary.assessment.rejectReasonText) || "";
  } catch (err) {
    // Sabab matnini olib bo'lmasa ham, umumiy maydonlar baribir to'ldiriladi.
  }

  const fillReport = await fillLetterCommonFields(letterTabId, payload);
  return { template: "toxtatilgan", payload, fillReport };
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
  await refreshRegistrationTab(id);
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

  if (template === "rad") {
    return runRadFill(id, letterTabId, registration, statusCode, token);
  }
  if (template === "toxtatilgan") {
    return runToxtatilganFill(id, letterTabId, registration, token);
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
