# Xizmat hujjatlari shablonlari

Bu papkadagi `.docx` fayllar — "Bosh ijtimoiy" bo'limidagi **xizmat
hujjatlari**ning manbasi. Ular fuqaroga emas, xodim yoki boshqa tashkilotga
yoziladi. Matnni o'zgartirish uchun faylni Wordda ochib tahrirlash kifoya.

| Fayl | Hujjat | Kimga |
|---|---|---|
| `bildirgi.docx` | Bildirgi (intizom yuzasidan) | Viloyat boshqarmasi boshlig'iga |
| `ogohlantirish.docx` | Ogohlantirish xati (zoom yig'ilishi) | Ijtimoiy xodimning o'ziga |
| `talabnoma.docx` | Talabnoma | Boshqa tashkilotga (bandlik bo'limi va h.k.) |

## Belgilar

Har bir belgi ilova tomonidan qiymatga almashtiriladi. Belgi qanday formatda
tursa (qalin, kursiv), qiymat ham shunday chiqadi.

**Uchala hujjatda ham:**

| Belgi | Nima yoziladi |
|---|---|
| `{mahalla}` | Mahalla / MFY nomi |
| `{xodim}` | Ijtimoiy xodim F.I.O |
| `{tashkilot_nomi}` | Imzo blokidagi tashkilot nomi |
| `{rahbar}` | Rahbar F.I.O |
| `{ijrochi}` | Hujjatni tayyorlagan xodim (I.Familya) |

**Faqat `bildirgi.docx` da:**

| Belgi | Nima yoziladi | Namuna |
|---|---|---|
| `{ish_boshlagan_sana}` | Xodim lavozimga kirgan sana | 2024-yil 3-oktyabr |
| `{buzilish_sanasi}` | Qoidabuzarlik sanasi (erkin matn) | 2026-yilning 19-20-avgust |
| `{ish_vaqti}` | Ish boshlanish vaqti | 09:00 |

**Faqat `ogohlantirish.docx` da:**

| Belgi | Nima yoziladi | Namuna |
|---|---|---|
| `{yigilish_sanasi}` | Yig'ilish sanasi | 30-iyun |
| `{rahbar_lavozimi}` | Yig'ilishni o'tkazgan rahbar lavozimi | direktor o'rinbosari |
| `{rahbar_fio}` | O'sha rahbarning F.I.O | Abdullayev Sirojiddin Sadullayevich |

**Faqat `talabnoma.docx` da:**

| Belgi | Nima yoziladi | Namuna |
|---|---|---|
| `{qabul_qiluvchi}` | Qaysi tashkilotga ("boshlig'iga" so'zisiz) | Andijon tuman kambag'allikni qisqartirish va bandlik bo'limi |
| `{fuqaro}` | Fuqaro F.I.O | Iminova Dilnoza Mamatkomilovna |
| `{tugilgan_sana}` | Fuqaro tug'ilgan sana | 2010-yil 3-iyun |
| `{yordam_turi}` | So'ralayotgan yordam turi | Mahalla xokim yordamchisiga yo'naltirish |

## Boshlang'ich holatga qaytarish

Shablonlar `yangi shablonlar/` papkasidagi haqiqiy namunalardan yasaladi:

```bash
python manage.py xizmat_shablon --force
```

`--force` **qo'lda kiritilgan tahrirlarni o'chiradi**. Buyruq har bir
almashtirishni sanab tekshiradi — namuna matni o'zgargan bo'lsa, jim
qolmasdan xato beradi.
