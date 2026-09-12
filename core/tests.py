# -*- coding: utf-8 -*-
"""Ikkala tizim uchun uchdan-uchiga sinovlar.

Qamrov: rollar va ularning ruxsatlari, "Bosh ijtimoiy" arizalarining .docx
eksporti (yangi kategoriyalar bilan), "Reestr tizimi" xatlarining
Shablons/reeystr/*.docx dan yaratilishi hamda tuzatilgan baza xatoliklari.
"""
import io
import json
from pathlib import Path

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from docx import Document

from core.docx_export import ShablonTopilmadi, ariza_docx_yaratish
from core.models import Ariza, Tashkilot, XizmatHujjati, XodimProfil
from reestr.models import Xat

TASHKILOT_NOMI = "Andijon tuman “Inson” IXM"


def docx_matni(baytlar):
    return "\n".join(p.text for p in Document(io.BytesIO(baytlar)).paragraphs)


class RolTest(TestCase):
    def setUp(self):
        tashkilot = Tashkilot.objects.create(nomi=TASHKILOT_NOMI, rahbar="S.Mutalibov")
        self.bosh = User.objects.create_user("bosh", password="p")
        self.bosh.profil.rol = XodimProfil.ROL_BOSH_IJTIMOIY
        self.bosh.profil.tashkilot = tashkilot
        self.bosh.profil.save()

        self.reestr = User.objects.create_user("reestr", password="p")
        self.reestr.profil.rol = XodimProfil.ROL_REESTR
        self.reestr.profil.tashkilot = tashkilot
        self.reestr.profil.save()

    def test_signal_profilni_yangi_sukut_rol_bilan_yaratadi(self):
        self.assertEqual(User.objects.create_user("yangi").profil.rol, "bosh_ijtimoiy")

    def test_root_redirect_rolga_qarab_yonaltiradi(self):
        c = Client()
        c.login(username="bosh", password="p")
        self.assertRedirects(c.get("/"), "/ariza/")

        c2 = Client()
        c2.login(username="reestr", password="p")
        self.assertRedirects(c2.get("/"), "/reestr/")

    def test_bosh_ijtimoiy_reestrga_kira_olmaydi(self):
        c = Client()
        c.login(username="bosh", password="p")
        self.assertRedirects(c.get("/reestr/"), "/", target_status_code=302)

    def test_reestr_arizalarga_kira_olmaydi(self):
        c = Client()
        c.login(username="reestr", password="p")
        self.assertRedirects(c.get("/ariza/"), "/", target_status_code=302)


class ArizaEksportTest(TestCase):
    def setUp(self):
        tashkilot = Tashkilot.objects.create(nomi=TASHKILOT_NOMI, rahbar="S.Mutalibov")
        self.user = User.objects.create_user(
            "bosh", password="p", first_name="Diyor", last_name="Atamirzayev"
        )
        self.user.profil.tuman = "Andijon"
        self.user.profil.tashkilot = tashkilot
        self.user.profil.save()
        self.client_ = Client()
        self.client_.login(username="bosh", password="p")

    def _ariza_yaratish(self, kategoriya, holat, **qoshimcha):
        data = dict(
            kategoriya=kategoriya, holat=holat, mfy="katta guzar", kucha="anisiy",
            fio="atamirzayev diyor", tashkilot="Ishonch telefoni", sana="2026-05-01",
            murojaat_raqami="1/26", ariza_raqami="55", **qoshimcha
        )
        javob = self.client_.post(reverse("core:ariza_create"), data)
        self.assertEqual(javob.status_code, 302)
        return Ariza.objects.latest("id")

    def test_yangi_kategoriyalar_eksport_qilinadi(self):
        holatlar = [
            ("davolanish", "davolanish xarajatlarini qoplash"),
            ("jarrohlik", "jarrohlik amaliyoti xarajatlarini qoplash"),
        ]
        for kategoriya, ibora in holatlar:
            with self.subTest(kategoriya=kategoriya):
                ariza = self._ariza_yaratish(
                    kategoriya, "tayinlangan",
                    ajratilgan_summa="1500000", kollegal_qaror="7845754",
                )
                buffer, _nom = ariza_docx_yaratish(ariza)
                matn = docx_matni(buffer.read())
                self.assertIn(ibora, matn)
                self.assertIn("1 500 000", matn)
                self.assertIn("Atamirzayev Diyor", matn)
                self.assertIn(f"{TASHKILOT_NOMI} direktori:", matn)
                self.assertIn("Ijrochi: D.Atamirzayev", matn)
                self.assertNotIn("{", matn)

    def test_rad_sabablari_alohida_abzatslarga_ajraladi(self):
        ariza = self._ariza_yaratish("davolanish", "rad")
        Ariza.objects.filter(pk=ariza.pk).update(
            rad_sabab_kodlari=["reestr", "tibbiy_hujjat"]
        )
        ariza.refresh_from_db()
        buffer, _nom = ariza_docx_yaratish(ariza)
        matn = docx_matni(buffer.read())
        self.assertIn("1) Sizning Ijtimoiy reestrda", matn)
        self.assertIn("2) Davolanish xarajatlarini tasdiqlovchi hujjatlar", matn)
        self.assertNotIn("{Appda belgilangan sabablar}", matn)

    def test_favqulodda_kategoriyasi_endi_qabul_qilinmaydi(self):
        self.client_.post(reverse("core:ariza_create"), dict(
            kategoriya="favqulodda", holat="rad", mfy="a", kucha="b", fio="c",
            tashkilot="d", sana="2026-05-01", murojaat_raqami="1", ariza_raqami="2",
        ))
        self.assertEqual(Ariza.objects.filter(kategoriya="favqulodda").count(), 0)

    def test_eski_favqulodda_yozuvi_tushunarli_xato_beradi(self):
        ariza = self._ariza_yaratish("davolanish", "rad")
        Ariza.objects.filter(pk=ariza.pk).update(kategoriya="favqulodda")
        ariza.refresh_from_db()
        with self.assertRaises(ShablonTopilmadi):
            ariza_docx_yaratish(ariza)

    def test_bosh_sabab_kodlari_yiqilmaydi(self):
        """Import/fixture orqali kelgan yozuvda qiymat None bo'lib qolishi
        mumkin — ilgari bu iteratsiyada TypeError berardi."""
        ariza = self._ariza_yaratish("davolanish", "rad")
        ariza.rad_sabab_kodlari = None
        self.assertEqual(ariza.rad_sabablari_royxati(), [])


class ReestrXatTest(TestCase):
    PAYLOAD = {
        "template": "rad",
        "fio": "atamirzayev diyor",
        "mfyNomi": "katta guzar",
        "street": "anisiy",
        "murojaatfrom": "Ishonch telefoni",
        "murojaatRaqami": "325650/26",
        "murojaatVaqti": "2026-07-16",
        "arizaMaqsadi": "oziq-ovqat xarajatlarini qoplash",
        "arizaVaqti": "2026-06-03",
        "arizaID": "32065423",
        "isQayta": True,
        "radSabablari": {
            "avtoRad": [{"avtoYil": "2021", "avtoModel": "cobalt", "avtoRaqam": "30A123BC"}]
        },
    }

    def setUp(self):
        tashkilot = Tashkilot.objects.create(nomi=TASHKILOT_NOMI, rahbar="S.Mutalibov")
        self.user = User.objects.create_user(
            "r", password="p", first_name="Diyor", last_name="Atamirzayev"
        )
        self.user.profil.rol = XodimProfil.ROL_REESTR
        self.user.profil.tashkilot = tashkilot
        self.user.profil.save()
        self.client_ = Client()
        self.client_.login(username="r", password="p")

    def _saqlash(self, **ozgarish):
        payload = dict(self.PAYLOAD, **ozgarish)
        return self.client_.post(
            reverse("reestr:create"), json.dumps(payload), content_type="application/json"
        )

    def _eksport_matni(self):
        xat = Xat.objects.latest("id")
        javob = self.client_.get(reverse("reestr:export", args=[xat.pk]))
        self.assertEqual(javob.status_code, 200)
        return docx_matni(javob.content)

    def test_xat_shablondan_toldiriladi(self):
        self.assertTrue(self._saqlash().json()["success"])
        matn = self._eksport_matni()
        self.assertIn(
            "Andijon tumani, Katta Guzar MFY, Anisiy ko'chasida yashovchi fuqaro "
            "Atamirzayev Diyorga",
            matn,
        )
        self.assertIn("2026-yil 16-iyul", matn)
        self.assertIn("2026-yil 3-iyun", matn)
        self.assertIn("32065423-ID", matn)
        self.assertIn("qayta o'rganilganda", matn)
        self.assertIn("30 A 123 BC", matn)
        self.assertIn("“Cobalt”", matn)
        self.assertIn(f"{TASHKILOT_NOMI} direktori:", matn)
        self.assertNotIn("{", matn)

    def test_sharti_bajarilmagan_abzatslar_ochiriladi(self):
        self._saqlash()
        matn = self._eksport_matni()
        self.assertIn("avtomashina", matn)
        self.assertNotIn("ko'chmas mulk", matn)
        self.assertNotIn("mahalla yettiligi", matn)

    def test_qayta_organilmagan_holat(self):
        self._saqlash(isQayta=False)
        matn = self._eksport_matni()
        self.assertIn("dastur tomonidan o'rganilganda", matn)
        self.assertNotIn("qayta o'rganilganda", matn)

    def test_tasdiqlash_xati(self):
        self._saqlash(
            template="tasdiqlandi", isQayta=False, radSabablari={},
            tasdiqMalumotlari={
                "is": True, "tasdiqSanasi": "2026, Mart", "tolovSanasi": "2026, Aprel",
                "hisobRaqami": "222222223545404", "tolovSum": "1450543.00",
            },
        )
        matn = self._eksport_matni()
        self.assertIn("2026-yil mart oyidan", matn)
        self.assertIn("2026-yil aprel oyi uchun", matn)
        self.assertIn("1 450 543.00", matn)
        self.assertIn("222222223545404", matn)
        self.assertNotIn("{", matn)

    def test_preview_ishlaydi(self):
        self._saqlash()
        xat = Xat.objects.latest("id")
        javob = self.client_.get(reverse("reestr:preview", args=[xat.pk]))
        self.assertEqual(javob.status_code, 200)
        self.assertContains(javob, "32065423")

    def test_boshqa_formatdagi_sana_ozi_togirlanadi(self):
        """16.07.2026 / 16-07-2026 kabi ko'rinishlar ham qabul qilinadi."""
        for kiritilgan in ("16.07.2026", "16/07/2026", "16-07-2026", "2026-07-16"):
            with self.subTest(sana=kiritilgan):
                Xat.objects.all().delete()
                javob = self._saqlash(murojaatVaqti=kiritilgan)
                self.assertEqual(javob.status_code, 200, javob.content[:200])
                self.assertEqual(
                    Xat.objects.latest("id").murojaat_vaqti.isoformat(), "2026-07-16"
                )

    def test_tushunib_bolmaydigan_sana_400_beradi(self):
        """Umuman sana bo'lmagan matn 500 emas, oddiy forma xatosi beradi."""
        javob = self._saqlash(murojaatVaqti="kecha ertalab")
        self.assertEqual(javob.status_code, 400)
        self.assertIn("Murojaat sanasi", " ".join(javob.json()["errors"]))
        self.assertEqual(Xat.objects.count(), 0)

    def test_kirilcha_matn_lotinchaga_ogiriladi(self):
        """So'rov to'g'ridan-to'g'ri (JS'siz) kelsa ham baza lotincha bo'lsin."""
        self._saqlash(fio="мурожаат этувчи", mfyNomi="катта гузар")
        xat = Xat.objects.latest("id")
        self.assertEqual(xat.fio, "Murojaat Etuvchi")
        self.assertEqual(xat.mfy_nomi, "Katta Guzar")

    def test_dashboard_statistikasi(self):
        self._saqlash()
        self._saqlash(template="muddat", radSabablari={}, qoshimchaMalumot="x")
        javob = self.client_.get(reverse("reestr:dashboard"))
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.context["jami"], 2)
        stats = {s["kod"]: s["soni"] for s in javob.context["template_stats"]}
        self.assertEqual(stats["rad"], 1)
        self.assertEqual(stats["muddat"], 1)
        self.assertContains(javob, "Reestr tizimi")

    @override_settings(REESTR_SHABLONLAR_DIR=Path("/bunday/papka/yoq"))
    def test_shablon_topilmasa_kod_generatoriga_qaytadi(self):
        self._saqlash()
        self.assertIn("32065423-ID", self._eksport_matni())


class XizmatHujjatiTest(TestCase):
    """Bildirgi / ogohlantirish / talabnoma — yaratish, eksport, ruxsatlar."""

    UMUMIY = {"mahalla": "mart", "xodim_fio": "yusupova yorqinoy xakimjon qiz"}
    BILDIRGI = dict(UMUMIY, turi="bildirgi", ish_boshlagan_sana="2024-10-03",
                    buzilish_sanasi="2026-yilning 19-20-avgust", ish_vaqti="09:00")
    OGOHLANTIRISH = dict(UMUMIY, turi="ogohlantirish", yigilish_sanasi="30-iyun",
                         rahbar_lavozimi="direktor o'rinbosari",
                         rahbar_fio="Abdullayev Sirojiddin Sadullayevich")
    TALABNOMA = dict(UMUMIY, turi="talabnoma",
                     qabul_qiluvchi="andijon tuman kambag'allikni qisqartirish va bandlik bo'limi",
                     fuqaro_fio="iminova dilnoza mamatkomilovna",
                     fuqaro_tugilgan_sana="2010-06-03",
                     yordam_turi="Mahalla xokim yordamchisiga yo'naltirish")

    def setUp(self):
        tashkilot = Tashkilot.objects.create(nomi=TASHKILOT_NOMI, rahbar="S.Mutalibov")
        self.user = User.objects.create_user(
            "bosh", password="p", first_name="Diyor", last_name="Atamirzayev"
        )
        self.user.profil.tashkilot = tashkilot
        self.user.profil.save()
        self.client_ = Client()
        self.client_.login(username="bosh", password="p")

    def _yaratish(self, data):
        javob = self.client_.post(reverse("core:xizmat_create"), data)
        self.assertEqual(javob.status_code, 302)
        return XizmatHujjati.objects.latest("id")

    def _eksport_matni(self, hujjat):
        javob = self.client_.get(reverse("core:xizmat_export", args=[hujjat.pk]))
        self.assertEqual(javob.status_code, 200)
        return docx_matni(javob.content)

    def test_bildirgi(self):
        hujjat = self._yaratish(self.BILDIRGI)
        matn = self._eksport_matni(hujjat)
        self.assertIn("Mart mahallasida", matn)
        self.assertIn("Yusupova Yorqinoy Xakimjon qiz", matn)
        self.assertIn("2024-yil 3-oktyabr", matn)
        self.assertIn("2026-yilning 19-20-avgust", matn)
        self.assertIn("09:00", matn)
        self.assertIn(f"{TASHKILOT_NOMI} direktori:", matn)
        self.assertIn("S.Mutalibov", matn)
        self.assertNotIn("{", matn)

    def test_ogohlantirish(self):
        hujjat = self._yaratish(self.OGOHLANTIRISH)
        matn = self._eksport_matni(hujjat)
        self.assertIn("OGOHLANTIRISH XATI", matn)
        self.assertIn("Mart MFY ijtimoiy xodimi", matn)
        self.assertIn("Joriy yilning 30-iyun kuni", matn)
        self.assertIn("direktor o'rinbosari Abdullayev Sirojiddin Sadullayevich", matn)
        self.assertNotIn("{", matn)

    def test_talabnoma(self):
        hujjat = self._yaratish(self.TALABNOMA)
        matn = self._eksport_matni(hujjat)
        self.assertIn("T A L A B N O M A", matn)
        self.assertIn("boshlig", matn)
        self.assertIn("Andijon tuman kambag'allikni qisqartirish va bandlik bo'limi", matn)
        self.assertIn("Iminova Dilnoza Mamatkomilovna", matn)
        self.assertIn("2010-yil 3-iyunda", matn)
        self.assertIn("Mahalla xokim yordamchisiga", matn)
        self.assertNotIn("{", matn)

    def test_turga_tegishli_maydonlar_majburiy(self):
        javob = self.client_.post(reverse("core:xizmat_create"), dict(self.UMUMIY, turi="talabnoma"))
        self.assertEqual(XizmatHujjati.objects.count(), 0)
        xabarlar = [str(m) for m in javob.wsgi_request._messages]
        self.assertTrue(any("majburiy" in x for x in xabarlar))

    def test_boshqa_turning_maydonlari_saqlanmaydi(self):
        """Bildirgi tanlangan bo'lsa, talabnoma maydonlari bazaga tushmasin."""
        hujjat = self._yaratish(dict(self.BILDIRGI, fuqaro_fio="Kerak Emas",
                                     qabul_qiluvchi="Kerak emas tashkilot"))
        self.assertEqual(hujjat.fuqaro_fio, "")
        self.assertEqual(hujjat.qabul_qiluvchi, "")

    def test_tahrirlash(self):
        hujjat = self._yaratish(self.BILDIRGI)
        self.client_.post(reverse("core:xizmat_edit", args=[hujjat.pk]),
                          dict(self.BILDIRGI, mahalla="sanoat"))
        hujjat.refresh_from_db()
        self.assertEqual(hujjat.mahalla, "Sanoat")

    def test_ochirish(self):
        hujjat = self._yaratish(self.BILDIRGI)
        self.client_.post(reverse("core:xizmat_delete", args=[hujjat.pk]))
        self.assertEqual(XizmatHujjati.objects.count(), 0)

    def test_begona_xodim_kora_olmaydi(self):
        hujjat = self._yaratish(self.BILDIRGI)
        User.objects.create_user("boshqa", password="p")
        c = Client()
        c.login(username="boshqa", password="p")
        self.assertEqual(c.get(reverse("core:xizmat_export", args=[hujjat.pk])).status_code, 403)
        self.assertEqual(c.post(reverse("core:xizmat_delete", args=[hujjat.pk])).status_code, 403)

    def test_reestr_xodimi_kira_olmaydi(self):
        reestrchi = User.objects.create_user("r", password="p")
        reestrchi.profil.rol = XodimProfil.ROL_REESTR
        reestrchi.profil.save()
        c = Client()
        c.login(username="r", password="p")
        self.assertRedirects(c.post(reverse("core:xizmat_create"), self.BILDIRGI),
                             "/", target_status_code=302)

    def test_dashboardda_tugma_va_royxat_bor(self):
        self._yaratish(self.BILDIRGI)
        javob = self.client_.get(reverse("core:dashboard"))
        self.assertContains(javob, "Yangi xizmat hujjati")
        self.assertContains(javob, "Xizmat hujjatlari")
        self.assertContains(javob, "Yusupova Yorqinoy Xakimjon qiz")
        self.assertEqual(len(javob.context["xizmat_hujjatlari"]), 1)


class MatnFormatlashTest(TestCase):
    def test_fio_qoshimchasi_kichik_qoladi(self):
        from core.text_utils import smart_title_case
        from reestr.docx_generator import to_title_case

        holatlar = [
            ("yusupova yorqinoy xakimjon qiz", "Yusupova Yorqinoy Xakimjon qiz"),
            ("ALIYEV VALI VALIJON O'G'LI", "Aliyev Vali Valijon o'g'li"),
            ("iminova dilnoza mamatkomilovna", "Iminova Dilnoza Mamatkomilovna"),
            ("katta guZ'Ar", "Katta Guz'ar"),
        ]
        for kirish, kutilgan in holatlar:
            with self.subTest(kirish=kirish):
                self.assertEqual(smart_title_case(kirish), kutilgan)
                # Ikkala tizim ham bir xil natija berishi shart
                self.assertEqual(to_title_case(kirish), kutilgan)


class TalabnomaTavsiyalariTest(TestCase):
    """VM 539-son qarori asosidagi tashkilot/yordam tavsiyalari."""

    def setUp(self):
        self.user = User.objects.create_user("bosh", password="p")
        self.client_ = Client()
        self.client_.login(username="bosh", password="p")

    def test_royxat_izchil(self):
        from core.talabnoma import (
            TASHKILOTLAR, barcha_yordamlar, tashkilot_nomlari, yordamlar_xaritasi,
        )
        self.assertTrue(TASHKILOTLAR)
        nomlar = [t["nomi"] for t in TASHKILOTLAR]
        self.assertEqual(len(nomlar), len(set(nomlar)), "tashkilot nomlari takrorlanmasin")
        for t in TASHKILOTLAR:
            with self.subTest(tashkilot=t["kod"]):
                self.assertTrue(t["nomi"] and t["izoh"] and t["yordamlar"])
        self.assertEqual(len(tashkilot_nomlari()), len(TASHKILOTLAR))
        self.assertEqual(set(yordamlar_xaritasi()), set(nomlar))
        hammasi = barcha_yordamlar()
        self.assertEqual(len(hammasi), len(set(hammasi)), "yordamlar takrorlanmasin")

    def test_dashboardda_tavsiyalar_bor(self):
        from core.talabnoma import TASHKILOTLAR
        javob = self.client_.get(reverse("core:dashboard"))
        self.assertContains(javob, 'id="talabnomaTashkilotlari"')
        self.assertContains(javob, 'id="talabnomaYordamlari"')
        self.assertContains(javob, 'id="talabnoma-data"')
        self.assertContains(javob, TASHKILOTLAR[0]["nomi"])
        # Xarita JSON sifatida sahifada bo'lishi kerak
        xarita = json.loads(javob.context["talabnoma_xaritasi_json"])
        self.assertIn(TASHKILOTLAR[0]["nomi"], xarita)

    def test_tavsiyadan_tashqari_matn_ham_saqlanadi(self):
        """Ro'yxat majburiy emas — erkin matn ham qabul qilinishi kerak."""
        javob = self.client_.post(reverse("core:xizmat_create"), dict(
            turi="talabnoma", mahalla="sanoat", xodim_fio="Test Xodim",
            qabul_qiluvchi="ro'yxatda umuman yo'q tashkilot",
            fuqaro_fio="Test Fuqaro", fuqaro_tugilgan_sana="2010-06-03",
            yordam_turi="Ro'yxatda yo'q yordam turi",
        ))
        self.assertEqual(javob.status_code, 302)
        hujjat = XizmatHujjati.objects.latest("id")
        self.assertEqual(hujjat.qabul_qiluvchi, "Ro'yxatda umuman yo'q tashkilot")
        self.assertEqual(hujjat.yordam_turi, "Ro'yxatda yo'q yordam turi")


class XatoliklargaChidamlilikTest(TestCase):
    """Hujjat yaratishda muammo bo'lsa ham dastur uzilmasligi kerak."""

    def setUp(self):
        tashkilot = Tashkilot.objects.create(nomi=TASHKILOT_NOMI, rahbar="S.Mutalibov")
        self.user = User.objects.create_user("bosh", password="p")
        self.user.profil.tashkilot = tashkilot
        self.user.profil.save()
        self.client_ = Client()
        self.client_.login(username="bosh", password="p")

    def _ariza(self, **qoshimcha):
        data = {
            "kategoriya": "davolanish", "holat": "rad", "mfy": "a", "kucha": "b",
            "fio": "c", "tashkilot": "d", "sana": "2026-05-01",
            "murojaat_raqami": "1", "ariza_raqami": "2",
        }
        data.update(qoshimcha)
        self.client_.post(reverse("core:ariza_create"), data)
        return Ariza.objects.latest("id")

    def test_shablon_yoq_bolsa_500_emas_xabar(self):
        ariza = self._ariza()
        Ariza.objects.filter(pk=ariza.pk).update(kategoriya="favqulodda")
        javob = self.client_.get(reverse("core:ariza_export", args=[ariza.pk]), follow=True)
        self.assertEqual(javob.status_code, 200)
        xabarlar = [str(m) for m in javob.context["messages"]]
        self.assertTrue(any("shablon" in x.lower() for x in xabarlar), xabarlar)

    @override_settings(XIZMAT_SHABLONLAR_DIR=Path("/bunday/papka/yoq"))
    def test_xizmat_shabloni_yoq_bolsa_500_emas_xabar(self):
        hujjat = XizmatHujjati.objects.create(
            turi="bildirgi", mahalla="Mart", xodim_fio="Test Xodim",
            buzilish_sanasi="19-avgust", ish_vaqti="09:00", created_by=self.user,
        )
        javob = self.client_.get(reverse("core:xizmat_export", args=[hujjat.pk]), follow=True)
        self.assertEqual(javob.status_code, 200)
        xabarlar = [str(m) for m in javob.context["messages"]]
        self.assertTrue(any("topilmadi" in x.lower() for x in xabarlar), xabarlar)

    def test_fayl_nomida_taqiqlangan_belgilar_bolmaydi(self):
        ariza = self._ariza()
        Ariza.objects.filter(pk=ariza.pk).update(fio='Test "Fuqaro" / Ism')
        javob = self.client_.get(reverse("core:ariza_export", args=[ariza.pk]))
        self.assertEqual(javob.status_code, 200)
        fayl_nomi = javob["Content-Disposition"].split('filename="')[1].rstrip('"')
        for belgi in '\/:*?<>|':
            self.assertNotIn(belgi, fayl_nomi)
        self.assertNotIn('"', fayl_nomi)
        self.assertTrue(fayl_nomi.endswith(".docx"))

    def test_sana_turli_formatda_qabul_qilinadi(self):
        for kiritilgan in ("2026-05-01", "01.05.2026", "01/05/2026"):
            with self.subTest(sana=kiritilgan):
                ariza = self._ariza(sana=kiritilgan)
                self.assertEqual(ariza.sana.isoformat(), "2026-05-01")

    def test_summa_turli_formatda_qabul_qilinadi(self):
        for kiritilgan in ("1500000", "1 500 000", "1500000.00", "1.500.000,00"):
            with self.subTest(summa=kiritilgan):
                self.client_.post(reverse("core:ariza_create"), dict(
                    kategoriya="davolanish", holat="tayinlangan", mfy="a", kucha="b",
                    fio="c", tashkilot="d", sana="2026-05-01", murojaat_raqami="1",
                    ariza_raqami="2", ajratilgan_summa=kiritilgan,
                    kollegal_qaror="7845754",
                ))
                self.assertEqual(Ariza.objects.latest("id").ajratilgan_summa, "1 500 000")

    def test_kirilcha_ariza_lotinchaga_ogiriladi(self):
        ariza = self._ariza(fio="мурожаат этувчи", mfy="катта гузар")
        self.assertEqual(ariza.fio, "Murojaat Etuvchi")
        self.assertEqual(ariza.mfy, "Katta Guzar")

    def test_xato_sahifasi_ozbekcha(self):
        from config.xatolar import MATNLAR
        from django.test import RequestFactory
        from config.xatolar import xato_404
        javob = xato_404(RequestFactory().get("/yoq/"))
        self.assertEqual(javob.status_code, 404)
        self.assertIn(MATNLAR[404][0], javob.content.decode())


class SahifalarOchiladiTest(TestCase):
    """Har bir sahifa haqiqatan ochilishini tekshiradi.

    Shablon sintaksis xatosi (masalan izoh ichidagi tasodifiy teg) faqat
    sahifa render qilinganda bilinadi — view mantig'ini sinash buni
    ushlamaydi. Shuning uchun barcha sahifalar ro'yxati alohida yuriladi.
    """

    def setUp(self):
        tashkilot = Tashkilot.objects.create(nomi=TASHKILOT_NOMI, rahbar="S.Mutalibov")
        self.bosh = User.objects.create_user("bosh", password="p")
        self.bosh.profil.tashkilot = tashkilot
        self.bosh.profil.save()
        self.reestrchi = User.objects.create_user("re", password="p")
        self.reestrchi.profil.rol = XodimProfil.ROL_REESTR
        self.reestrchi.profil.tashkilot = tashkilot
        self.reestrchi.profil.save()

        self.ariza = Ariza.objects.create(
            kategoriya="davolanish", holat="rad", tuman="Andijon", mfy="Mart",
            kucha="Anisiy", fio="Test Fuqaro", tashkilot="Ishonch",
            sana="2026-05-01", murojaat_raqami="1/26", ariza_raqami="55",
            created_by=self.bosh,
        )
        self.hujjat = XizmatHujjati.objects.create(
            turi="bildirgi", mahalla="Mart", xodim_fio="Test Xodim",
            ish_boshlagan_sana="2024-10-03", buzilish_sanasi="19-avgust",
            ish_vaqti="09:00", created_by=self.bosh,
        )
        self.xat = Xat.objects.create(
            template="rad", fio="Test Fuqaro", mfy_nomi="Mart", street="Anisiy",
            murojaatfrom="Ishonch", murojaat_raqami="1/26",
            murojaat_vaqti="2026-07-16", ariza_maqsadi="oziq-ovqat",
            ariza_vaqti="2026-06-03", ariza_id="32065423",
            rad_sabablari={"norasmiyRad": True}, created_by=self.reestrchi,
        )

    def test_bosh_ijtimoiy_sahifalari(self):
        c = Client()
        c.login(username="bosh", password="p")
        manzillar = [
            ("core:dashboard", []),
            ("core:ariza_detail", [self.ariza.pk]),
            ("core:ariza_export", [self.ariza.pk]),
            ("core:xizmat_detail", [self.hujjat.pk]),
            ("core:xizmat_export", [self.hujjat.pk]),
        ]
        for nom, args in manzillar:
            with self.subTest(sahifa=nom):
                self.assertEqual(c.get(reverse(nom, args=args)).status_code, 200)

    def test_reestr_sahifalari(self):
        c = Client()
        c.login(username="re", password="p")
        manzillar = [
            ("reestr:dashboard", []),
            ("reestr:create_page", []),       # shablon sintaksisi shu yerda tekshiriladi
            ("reestr:edit_page", [self.xat.pk]),
            ("reestr:preview", [self.xat.pk]),
            ("reestr:export", [self.xat.pk]),
        ]
        for nom, args in manzillar:
            with self.subTest(sahifa=nom):
                self.assertEqual(c.get(reverse(nom, args=args)).status_code, 200)

    def test_login_sahifasi(self):
        self.assertEqual(Client().get("/login/").status_code, 200)

    def test_admin_sahifalari(self):
        User.objects.create_superuser("admin", password="p")
        c = Client()
        c.login(username="admin", password="p")
        for manzil in ("/admin/", "/admin/core/ariza/", "/admin/core/xizmathujjati/",
                       "/admin/core/tashkilot/", "/admin/reestr/xat/"):
            with self.subTest(manzil=manzil):
                self.assertEqual(c.get(manzil).status_code, 200)


class KollegalQarorTest(TestCase):
    """Tayinlangan xatlarda mahalla yettiligi qarori raqami."""

    def setUp(self):
        tashkilot = Tashkilot.objects.create(nomi=TASHKILOT_NOMI, rahbar="S.Mutalibov")
        self.user = User.objects.create_user("bosh", password="p")
        self.user.profil.tashkilot = tashkilot
        self.user.profil.save()
        self.client_ = Client()
        self.client_.login(username="bosh", password="p")

    def _post(self, **qoshimcha):
        data = {
            "kategoriya": "oziq_ovqat", "holat": "tayinlangan", "mfy": "mart",
            "kucha": "anisiy", "fio": "test fuqaro", "tashkilot": "Ishonch",
            "sana": "2026-05-01", "murojaat_raqami": "1/26", "ariza_raqami": "55",
            "ajratilgan_summa": "1500000", "kollegal_qaror": "7845754",
        }
        data.update(qoshimcha)
        return self.client_.post(reverse("core:ariza_create"), data)

    def test_barcha_tayinlangan_shablonlarda_chiqadi(self):
        from core.reasons import KATEGORIYALAR
        for kod, nom in KATEGORIYALAR:
            with self.subTest(kategoriya=nom):
                self._post(kategoriya=kod, kollegal_qaror="7845754")
                ariza = Ariza.objects.latest("id")
                buffer, _ = ariza_docx_yaratish(ariza)
                matn = docx_matni(buffer.read())
                self.assertIn("Kollegal qaror raqami-7845754", matn)
                self.assertNotIn("{kollegal_qaror}", matn)

    def test_tayinlanganda_majburiy(self):
        javob = self._post(kollegal_qaror="")
        self.assertEqual(Ariza.objects.count(), 0)
        xabarlar = [str(m) for m in javob.wsgi_request._messages]
        self.assertTrue(any("kollegal qaror" in x.lower() for x in xabarlar), xabarlar)

    def test_rad_holatida_talab_qilinmaydi_va_tozalanadi(self):
        javob = self._post(holat="rad", ajratilgan_summa="", kollegal_qaror="123",
                           rad_sabablari=["reestr"])
        self.assertEqual(javob.status_code, 302)
        ariza = Ariza.objects.latest("id")
        self.assertEqual(ariza.kollegal_qaror, "")

    def test_raqam_probelsiz_saqlanadi(self):
        self._post(kollegal_qaror="784 57 54")
        self.assertEqual(Ariza.objects.latest("id").kollegal_qaror, "7845754")

    def test_dashboardda_korinadi(self):
        self._post()
        javob = self.client_.get(reverse("core:dashboard"))
        self.assertContains(javob, "Kollegal qaror raqami")
        self.assertContains(javob, "7845754")
