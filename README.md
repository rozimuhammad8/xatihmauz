# IHMA hujjat tizimi

Andijon tumani "Inson" ijtimoiy xizmatlar markazi uchun rasmiy Word hujjatlarini
avtomatik tayyorlash tizimi. Ikki mustaqil bo'lim va bitta brauzer kengaytmasidan
iborat.

| Bo'lim | Rol | URL | Nima qiladi |
|---|---|---|---|
| **Bosh ijtimoiy** | `bosh_ijtimoiy` | `/ariza/` | "Saxovat va ko'mak" arizalariga javob xatlari + xizmat hujjatlari |
| **Reestr tizimi** | `reestr` | `/reestr/` | "Ijtimoiy himoya yagona reyestri" bo'yicha javob xatlari |
| **Chrome kengaytmasi** | — | — | `sr.ihma.uz` dan ma'lumot olib, reestr formasini avtomatik to'ldiradi |

Barcha hujjat matnlari [`Shablons/`](Shablons) papkasidagi `.docx` fayllarda —
ularni Wordda ochib tahrirlash mumkin, kodga tegish shart emas.

---

## Tez boshlash (ishlab chiqish)

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

copy .env.example .env          # Linux/macOS: cp .env.example .env
# .env ichida DJANGO_DEBUG=True va DJANGO_SECRET_KEY to'ldiring

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Maxfiy kalit yaratish:

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

### Xodim qo'shish

1. `/admin/` ga superuser bilan kiring
2. **Tashkilotlar** — markaz nomi va rahbar F.I.O ni kiriting (imzo blokida ishlatiladi)
3. **Foydalanuvchilar** — yangi xodim yarating, pastdagi *Xodim profili* blokida:
   - **Rol** — `Bosh ijtimoiy` yoki `Reestr tizimi`
   - **Tashkilot** — yuqorida yaratganingiz
   - **Ism / Familiya** — imzo blokidagi "Ijrochi: I.Familya" shundan olinadi

---

## Ishga tushirish (production)

### 1. Muhit

`.env` faylini to'ldiring:

```ini
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<yangi tasodifiy kalit>
DJANGO_ALLOWED_HOSTS=ihma.uz,www.ihma.uz
DJANGO_CSRF_TRUSTED_ORIGINS=https://ihma.uz,https://www.ihma.uz
DJANGO_HTTPS=True
```

`DJANGO_DEBUG=False` bo'lganda `DJANGO_SECRET_KEY` va `DJANGO_ALLOWED_HOSTS`
**majburiy** — ularsiz dastur ataylab ishga tushmaydi.

### 2. Tayyorlash

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

### 3. Server

```bash
# Linux / macOS
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3

# Windows
pip install waitress
waitress-serve --port=8000 config.wsgi:application
```

Statik fayllarni WhiteNoise uzatadi — nginx uchun alohida `location /static/`
sozlash shart emas.

### 4. Zaxira nusxa

Saqlanishi kerak bo'lgan uchta narsa:

```
db.sqlite3        # barcha arizalar, xatlar va hujjatlar
Shablons/         # tahrirlangan .docx shablonlar
.env              # sozlamalar (SECRET_KEY!)
```

---

## Kengaytmani o'rnatish

1. Chrome → `chrome://extensions` → **Developer mode** yoqing
2. **Load unpacked** → `extension/` papkasini tanlang
3. Kengaytma belgisini bosing → **Server manzili** bo'limini oching →
   Reestr tizimi manzilini yozing (masalan `https://ihma.uz`) → **Saqlash**

Manzil kengaytma ichida saqlanadi — fayllarni tahrirlash shart emas. Yangi
manzilga birinchi marta saqlaganda Chrome ruxsat so'raydi.

Ishlatish: `sr.ihma.uz` da arizani oching → kengaytma belgisini bosing →
**To'ldirish**. Shablon ariza holatiga (`statusId`) qarab avtomatik tanlanadi.
Xat avtomatik yuborilmaydi — tekshirib, o'zingiz saqlaysiz.

---

## Foydali buyruqlar

```bash
python manage.py test core              # barcha sinovlar (40 ta)
python manage.py reestr_shablon --force # reestr shablonlarini tiklash
python manage.py xizmat_shablon --force # xizmat shablonlarini tiklash
python manage.py xat_reestrga_kochir    # eski "xat" bazasini "reestr" ga ko'chirish
```

> `--force` qo'lda kiritilgan tahrirlarni o'chiradi.

### Eski versiyadan yangilash

`xat` ilovasi `reestr` deb qayta nomlangan. Eski bazangiz bo'lsa,
**migratsiyadan oldin**:

```bash
python manage.py xat_reestrga_kochir --dry-run   # nima o'zgarishini ko'rish
python manage.py xat_reestrga_kochir
python manage.py migrate
```

Buyruq o'zini tekshiradi — yangi bazada hech narsa qilmaydi.

---

## Loyiha tuzilmasi

```
xatihmauz/
├── config/            # sozlamalar, URL'lar, xato sahifalari
├── core/              # "Bosh ijtimoiy": arizalar + xizmat hujjatlari
│   ├── docx_utils.py    # ikkala tizim uchun umumiy .docx quroli
│   ├── docx_export.py   # ariza -> .docx
│   ├── xizmat_export.py # xizmat hujjati -> .docx
│   ├── reasons.py       # rad etish sabablari (VM 462-son)
│   ├── talabnoma.py     # tashkilot/yordam tavsiyalari (VM 539-son)
│   └── text_utils.py    # kiritishni o'zi to'g'rilash (sana, pul, kirilcha)
├── reestr/            # "Reestr tizimi": xatlar
│   ├── docx_templates.py # shablondan xat yasash
│   ├── docx_generator.py # zaxira: kodda xat qurish
│   └── letter_text.py    # brauzerdagi ko'rinish (.docx bilan bir xil matn)
└── Shablons/          # BARCHA .docx shablonlar (Ariza / reeystr / xizmat)
```

## Huquqiy asoslar

| Qaror | Nimada ishlatiladi |
|---|---|
| VM 2025-yil 23-iyul **462-son** | "Saxovat va ko'mak" arizalari va rad sabablari |
| VM 2026-yil 29-yanvar **35-son** | Reestr tizimi xatlaridagi Nizom iqtiboslari |
| VM 2023-yil 7-oktabr **539-son** | Talabnoma va undagi yordam turlari |
| O'RQ-445-son | Muddat so'rash xati (28-modda) va shikoyat huquqi |

> Shablonlardagi qaror raqamlari va bandlarini amaldagi tahrir bilan
> solishtirib turing — ular `.docx` fayllarda, Wordda tahrirlanadi.
