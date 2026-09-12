# Shablons

Tizimdagi barcha Word (.docx) shablonlari shu papkada, uch bo'limga ajratilgan.
Har bir fayl ichida `{belgi}` ko'rinishidagi o'rinbosarlar bor — ilova ularni
haqiqiy ma'lumot bilan almashtiradi. **Matnni o'zgartirish uchun faylni Wordda
ochib tahrirlash kifoya, kodga tegish shart emas.**

| Papka | Tizim | Nimalar bor |
|---|---|---|
| [`Ariza/`](Ariza) | Bosh ijtimoiy | "Saxovat va ko'mak" arizalariga javob xatlari — 6 ta kategoriya × 2 holat = 12 ta fayl |
| [`reeystr/`](reeystr) | Reestr tizimi | Rad etish, tasdiqlash, tayinlash, muddat so'rash, ariza kiritilgan — 5 ta fayl |
| [`xizmat/`](xizmat) | Bosh ijtimoiy | Bildirgi, ogohlantirish, talabnoma — 3 ta fayl |

`reeystr/` va `xizmat/` papkalarida o'z `README.md` fayli bor — u yerda har bir
belgining ma'nosi jadval ko'rinishida yozilgan.

## Qaysi belgilar bor

**Ariza/** shablonlarida: `{tuman}`, `{mfy}`, `{kucha}`, `{fio}`, `{sana}`,
`{murojaat_raqami}`, `{ariza_raqami}`, `{tashkilot}`, `{ajratilgan_summa}`
va rad xatlarida `{Appda belgilangan sabablar}` — bu belgi turgan abzats
tanlangan har bir sabab uchun alohida abzatsga bo'linadi.

**reeystr/** va **xizmat/** — o'sha papkalardagi README ga qarang.

## Qayta yasash

`reeystr/` va `xizmat/` papkalaridagi fayllarni boshlang'ich holatiga
qaytarish mumkin:

```bash
python manage.py reestr_shablon --force
python manage.py xizmat_shablon --force
```

`--force` **qo'lda kiritilgan tahrirlarni o'chiradi**. `Ariza/` papkasidagi
fayllar qo'lda tayyorlangan — ular uchun bunday buyruq yo'q, ehtiyot bo'ling.
