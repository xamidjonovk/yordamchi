# Tekshiruv holati — 0.5.1

Sana: **2026-11-07**, vaqt zonasi **Asia/Tashkent**. Barcha yangi sinovlar shaxsiy Telegram/VPS nusxasidan alohida bajarildi.

## Bajarilgan tekshiruvlar

| Tekshiruv | Natija |
|---|---|
| Backend va himoya testlari | **92 passed, 1 skipped**; Windows’da POSIX audio ijrosi testi o‘tkazib yuboriladi |
| Toza Windows installer | Alohida instance’da app, Python, native ovoz kutubxonalari va Hermes haqiqatan o‘rnatildi; yakuniy installer muvaffaqiyatli tugadi |
| Hermes CLI | Pinned `bf0203a794a07aac3ff764972ab9087baa4e4f4e` o‘rnatildi; `auth add --help`, OAuth va `--no-browser` imkoniyati tekshirildi |
| OpenAI va Anthropic OAuth boshlanishi | Haqiqiy CLI har ikkala provayderning rasmiy login havolasini chiqardi; OpenAI vaqtinchalik qurilma kodi ham olindi. Login tasdiqlanmasdan oqimlar bekor qilindi |
| Sozlash ustasi, Chromium | Installer havolasi ustani avtomatik ochdi; 5 qadam, provayder almashishi, Telegram kod/2FA maydonlari va maxfiy maydonlarni tozalash tekshirildi |
| Panel, 1440 / 768 / 390 px | Profil, bilimlar, suhbat, kalendar, vazifa yaratish, sintetik muhim xabarlar; JS xatosi va gorizontal overflow topilmadi |
| API va reja | Haqiqiy mahalliy API orqali profil, ovoz rejimi, reja, bekor qilish va inbox; xizmat ishlaganda ikkinchi yozuvchidan himoya tekshirildi |
| Telegram login holati | Kod/2FA/egani tekshirish, qayta urinish, timeout va lock tozalash unit testlari; noto‘g‘ri egadan keyin tuzatish mumkin |
| Maxfiy saqlash | Credentiallar muvaffaqiyatli ulanishdan keyin yoziladi; xato kalit avvalgisini almashtirmaydi; brauzerga raw OAuth log/token qaytmaydi |
| Hisob yo‘nalishi | Tanlangan provayder va model saqlanadi; boshqa provayderga yashirin pulli fallback yo‘q; yakunlash uchun haqiqiy model javobi talab qilinadi |
| Paketlar | Wheel, sdist va faqat ruxsat etilgan fayllardan ZIP yig‘iladi |
| Mustaqil dizayn ko‘rigi | Installer havolasi, provayder holati, Telegram qayta urinish va yo‘riqnoma muammolari tuzatilib qayta ko‘rildi |

UI sinovlarida tashqi OAuth/Telegram javoblari simulyatsiya qilinadi; mahalliy API va ma’lumot ombori haqiqiy. Yuqoridagi alohida OAuth boshlanish sinovi esa haqiqiy Hermes CLI bilan bajarilgan. Screenshotlardagi xabar va rejalar sun’iy misollar.

## Maxfiylik va tarqatish chegarasi

Public repo **yangi, toza Git tarixi** bilan yaratilgan. Eski private tarix public qilinmagan. Manba, public Git tarixi va release fayllari credential andozalari hamda mavjud mahalliy maxfiy qiymatlar bilan solishtiriladi; tekshiruvchi qiymatlarning o‘zini chiqarmaydi.

`.env`, OAuth loginlari, Telegram sessiyasi, shaxsiy konfiguratsiya, inbox, bilimlar va installer sinov muhiti release’ga kirmaydi. Commit muallifi umumiy loyiha nomi bilan yoziladi. Avvalgi private tarixdagi shaxsiy identifikatorlar tufayli uni public repoga ko‘chirish mumkin emas.

Bu tekshiruv tashqi fork/cache yoki tasvir ichidagi har qanday yozuv yo‘qligiga mutlaq kafolat bermaydi. O‘zingiz qo‘shgan fayllarni keyinchalik ham tekshiring.

## Amaliy cheklovlar

- Haqiqiy foydalanuvchi obunasi bilan login va pulli model javobi bu QA’da bajarilmadi. Usta ichidagi **AI javobini sinash** buni o‘z hisobingizda tekshiradi.
- Haqiqiy Telegram kodi/2FA, xabar yetkazish, jonli qo‘ng‘iroq va mikrofon sifati yangi versiyada end-to-end sinalmadi. O‘zingiz ulaganingizdan keyin sinang.
- To‘liq yangi native installer mahalliy Windows’da tekshirildi. Linux/macOS installerining haqiqiy yangi qurilmadagi o‘rnatilishi shu mashinada tekshirilmagan. Uch tizimli CI app testlari alohida ko‘rsatiladi.
- Claude OAuth uchun Hermes talab qiladigan **Max va qo‘shimcha foydalanish kreditlari** kerak. Brauzer ovozi va Gemini sarfi/provayder imkoniyatlari README’da ajratilgan.
- Screen reader bilan to‘liq qo‘lda audit qilinmagan. Dizayn yordamchisining launcheri ishlamagani sabab haqiqiy screenshotlar va mustaqil ko‘rik ishlatilgan.

Qayta tekshirish: `python -m pytest -q`, `python scripts/privacy_scan.py`, `python scripts/verify-web-ui.py`, `python scripts/verify-onboarding-ui.py`. Browser tekshiruvlari uchun dev kutubxonalari va Playwright Chromium kerak. Haqiqiy foydalanuvchi loginini testlarga bermang.
