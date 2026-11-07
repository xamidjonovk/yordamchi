# Tekshiruv holati

Sana: **2026-11-07**, vaqt zonasi **Asia/Tashkent**. Tekshiruvlar ishlab turgan Telegram nusxasidan alohida, yangi vaqtinchalik instance’larda bajarildi.

## Bajarilgan tekshiruvlar

| Tekshiruv | Natija |
|---|---|
| Avvalgi backend testlari | Boshlang‘ich holatda 70 passed, 1 skipped |
| Kengaytirilgan backend/himoya testlari | 78 passed, 1 skipped |
| Yangi Windows muhiti, `uv sync --frozen --no-dev` | O‘rnatildi; native calls paketi yo‘qligida web ilova yaratildi |
| Python wheel va sdist yig‘ish | Muvaffaqiyatli |
| Playwright / Chromium, 1440 / 768 / 390 px | Profil, qayd, qidiruv, nav, xato, yangi suhbat: ishladi; JS xatosi va gorizontal overflow topilmadi |
| Manbani chiqarish regressiyasi | Tasdiqlash → boshqa manbani ochish → Escape → yangilash: ikkinchi manba saqlandi |
| Auth chegarasi | Tokensiz API, yot Host va Origin rad etildi |
| Yuklash | Matn manbaga aylandi; yo‘l komponentlari tozalandi; bajariladigan format rad etildi |
| Profil | Noto‘g‘ri zona, noma’lum maydon va ortiqcha matn rad etildi |
| Konfiguratsiya | Boshqa process saqlagan qiymat yo‘qolmasligi tekshirildi |
| Dizayn ko‘rigi | Uch topilma tuzatildi; aynan shu uch tuzatish bo‘yicha `ship` xulosasi |

## Maxfiylik tekshiruvi

Mahalliy Git’dagi **21 commit / 126 blob** va GitHub private repodagi **3 commit / 77 blob** ko‘rildi. Shaxsiy ismlar/username’lar va tarix muallifi metadata’si eski tarixda mavjud. Demak, eski tarixni public qilishga tayyor deb bo‘lmaydi.

Kalit andozalari va 6 ta mavjud mahalliy maxfiy qiymat bo‘yicha haqiqiy credential mosligi topilmadi. Credential andozasiga tushgan bitta test qiymati sun’iy fixture deb tasdiqlandi. Bu tashqi fork, cache, o‘chirilgan remote obyekt yoki rasm ichidagi har bir yozuv tekshirildi degani emas.

Tarqatiladigan joriy matnlar shaxsiy nomlardan tozalandi. Avvalgi operatsion hujjatlar mahalliy `.private-local` arxivida saqlandi va release’dan chiqarildi. Dars uchun **yangi tarixli eksport** ishlatiladi. Eski GitHub private repo qayta yozilmadi va public qilinmadi.

## Tekshirilmagan qismlar

- Yangi kod bilan haqiqiy Telegram qo‘ng‘irog‘i, mikrofon audio sifati va pulli/cloud AI end-to-end oqimi sinovdan o‘tkazilmadi.
- Linux/macOS’da haqiqiy yangi ishga tushirish va Docker build bu mashinada bajarilmadi; CI konfiguratsiyasi mavjud, yangi CI run bajarilgani da’vo qilinmaydi.
- Screen reader bilan qo‘lda to‘liq audit qilinmadi.
- Dizayn yordamchisining kontekst/detektor launcheri ishlamadi; vizual tekshiruv haqiqiy screenshot va mustaqil ko‘rik asosida qilindi.

Muayyan natijani qayta tekshirish uchun README’dagi buyruqlar va `scripts/verify-web-ui.py`dan foydalaning. Testlar haqiqiy foydalanuvchi loginini ishlatmaydi.
