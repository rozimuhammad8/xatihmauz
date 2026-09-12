# Reestr tizimi shablonlari

Bu papkadagi `.docx` fayllar — "Reestr tizimi" rasmiy xatlarining manbasi.
Xat yaratilganda ilova shu fayllardan birini ochadi va ichidagi belgilarni
haqiqiy ma'lumot bilan almashtiradi. **Matnni o'zgartirish uchun faqat shu
fayllarni Wordda tahrirlash kifoya — Python kodiga tegish shart emas.**

| Fayl | Xat turi |
|---|---|
| `rad.docx` | Rad etish |
| `tasdiqlandi.docx` | Tasdiqlash |
| `tayinlandi.docx` | Tayinlash |
| `muddat.docx` | Muddat so'rash |
| `ariza_kiritilgan.docx` | Ariza kiritilgan |

## 1. Oddiy belgilar

Bularni xohlagan joyga qo'ying — ilova o'rniga qiymat yozadi. Belgi qanday
formatda tursa (qalin, kursiv, o'lcham), qiymat ham shunday chiqadi.

| Belgi | Nima yoziladi | Namuna |
|---|---|---|
| `{fio}` | Fuqaro F.I.O | Atamirzayev Diyor |
| `{mfy}` | MFY nomi | Katta Guzar |
| `{kucha}` | Ko'cha nomi | Anisiy |
| `{murojaat_manbasi}` | Murojaat qayerdan kelgani | Prezidentga ishonch telefoni |
| `{murojaat_sanasi}` | Murojaat sanasi | 2026-yil 16-iyul |
| `{murojaat_raqami}` | Murojaat raqami | 325650/26 |
| `{ariza_maqsadi}` | Ariza maqsadi (dastur nomi) | oziq-ovqat xarajatlarini qoplash |
| `{ariza_sanasi}` | Ariza sanasi | 2026-yil 3-iyun |
| `{ariza_id}` | Ariza ID raqami | 32065423 |
| `{qayta}` | "qayta " yoki bo'sh | qayta |
| `{tasdiq_davri}` | Tasdiqlash davri | 2026-yil mart |
| `{tolov_davri}` | To'lov davri | 2026-yil aprel oyi |
| `{hisob_raqami}` | Hisob raqami | 222222223545404 |
| `{tolov_summasi}` | To'lov summasi | 1 450 543.00 |
| `{tayinlash_qoshimcha}` | Tayinlash xatidagi qo'shimcha izoh | |
| `{qoshimcha_malumot}` | Muddat xatidagi qo'shimcha izoh | |
| `{tashkilot_nomi}` | Imzo blokidagi tashkilot | Andijon tuman "Inson" IXM |
| `{rahbar}` | Rahbar F.I.O | S.Mutalibov |
| `{ijrochi}` | Xatni tayyorlagan xodim | D.Atamirzayev |
| `{uy_soni}` | Ko'chmas mulklar soni | 2 |

## 2. Ro'yxatlar (ichida qalin qismi bor)

Bular bir nechta yozuvdan grammatik to'g'ri jumla yasaydi, shuning uchun
ichidagi rusum/raqam qalin chiqadi. Faqat `rad.docx` da ishlatiladi.

| Belgi | Natija |
|---|---|
| `{avto_royxati}` | 2021-yilda ishlab chiqarilgan davlat raqami **30 A 123 BC** bo'lgan **"Cobalt"** rusumli avtomashina |
| `{uy_royxati}` | Manzili ... kadastr raqami ... bo'lgan |
| `{rasmiy_matni}` | ... tomonidan ...ga ... so'm oylik daromad hisoblangan ... |

## 3. Shartli abzatslar

Abzats `{?belgi}` bilan **boshlansa**, sharti bajarilmaganda butun abzats
hujjatdan o'chiriladi. Bajarilsa — belgining o'zi yo'qoladi, abzats qoladi.

| Belgi | Qachon qoladi |
|---|---|
| `{?avtoRad}` | Avtomobil sababi tanlangan bo'lsa |
| `{?uyRad}` | Ko'chmas mulk sababi tanlangan bo'lsa |
| `{?rasmiyRad}` | Rasmiy daromad sababi tanlangan bo'lsa |
| `{?norasmiyRad}` | Norasmiy daromad sababi tanlangan bo'lsa |
| `{?uydaEmasRad}` | "Uyda bo'lmagan" sababi tanlangan bo'lsa |
| `{?tolov}` | To'lov summasi yoki hisob raqami kiritilgan bo'lsa |
| `{?tayinlashQoshimcha}` | Tayinlash izohi yozilgan bo'lsa |
| `{?qoshimchaMalumot}` | Muddat izohi yozilgan bo'lsa |

Yangi shartli abzats qo'shish uchun mavjud abzatslardan birini nusxalab,
boshiga kerakli `{?...}` belgisini qo'ying.

## 4. Foydali eslatmalar

- Word ba'zan belgini bo'lib tashlaydi (`{fi` + `o}`) — ilova buni hisobga
  oladi, lekin ishonch uchun belgini bir marta yozib, keyin ustiga
  formatlashni qo'llang.
- Belgi nomi noto'g'ri yozilsa (masalan `{fiо}` — ichida kirilcha "о"),
  u almashtirilmay, xatda o'zi ko'rinib qoladi. Shu bo'yicha tekshiring.
- Shablon fayli o'chib ketsa, tizim eski kod generatoriga qaytadi va
  xat baribir yaratiladi.

## 5. Boshlang'ich holatga qaytarish

```bash
python manage.py reestr_shablon --force
```

`--force` **qo'lda kiritilgan barcha tahrirlarni o'chiradi**. Faqat
yo'qolganlarini tiklash uchun `--force` siz ishlating, bitta shablon uchun:

```bash
python manage.py reestr_shablon rad --force
```
