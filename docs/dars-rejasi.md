# GitHub’dan o‘zingizning AI yordamchingizgacha

**90 daqiqalik amaliy dars.** Yakunda har bir ishtirokchida o‘ziga tegishli profil, bilim ombori va brauzer paneli bo‘ladi. AI/Telegram ulash vaqtini hisob loginlari uzaytirishi mumkin; ular alohida bosqich.

| Vaqt | O‘qituvchi ko‘rsatadi | Ishtirokchi bajaradi | Natijani tekshirish |
|---|---|---|---|
| 0–10 daqiqa | Kod, model va shaxsiy ma’lumot farqi | Talablarni tekshiradi | Brauzer, internet va bo‘sh joy bor |
| 10–25 | Git clone / Download ZIP | Bitta installer va o‘zbekcha usta bilan o‘rnatadi | Panel ochiladi |
| 25–35 | Ustaning profil va vaqt zonasi qadami | O‘z maqsadi/uslubini yozadi | Qayta ochganda profil qoladi |
| 35–50 | Qayd va hujjat qo‘shish | 3 ta xavfsiz manba kiritadi | Kalit so‘z bilan manba topiladi |
| 50–65 | Ustada OpenAI/Claude login va model tanlash | Rasmiy sahifada o‘z hisobini ulaydi | Oddiy savolga real javob |
| 65–75 | RAG va dalil tekshirish | Hujjat bo‘yicha savol beradi | Javobda manba IDsi bor |
| 75–85 | Mikrofon va javobni o‘qish | Brauzer ruxsatini yoqadi | Matnni tekshirib yuboradi |
| 85–90 | Maxfiylik, backup, to‘xtatish | Shaxsiy papkasini topadi | Kod va credentialni ajrata oladi |

## Darsdan oldin

Tarqatish uchun toza tarixli eksportdan foydalaning; ishchi private repo va eski tarixni ommaviy qilmang. Ikkinchi, yangi papkada installer sinovini bajaring. Demo uchun sun’iy profil va hujjatlardan foydalaning. Login, tokenli URL, API kaliti va Telegram kodini proyektorda ko‘rsatmang.

## Nazorat savollari

1. Hujjat qo‘shish model vaznlarini o‘zgartiradimi? **Yo‘q, manbali xotira va retrieval ishlaydi.**
2. Panel ochilishi AI login tayyorligini bildiradimi? **Yo‘q, haqiqiy javob bilan tekshiriladi.**
3. `.gitignore` eski commitdagi sirni o‘chiradimi? **Yo‘q.**
4. Mahalliy saqlash cloud’ga hech narsa ketmasligini bildiradimi? **Yo‘q, savol/profil/tegishli matn provayderga borishi mumkin.**
5. Kompyuter o‘chiq bo‘lsa eslatma keladimi? **Xizmat ishlamaydi; alohida doimiy server kerak.**

## Yakuniy mustaqil topshiriq

O‘zingizga mos yordamchi yarating: bitta profil, o‘qish rejasi, sun’iy loyiha tavsifi va ikki savol. Har javobning manbasini ochib tekshiring. Bir manbani qidiruvdan chiqarib, endi topilmasligini ko‘ring. Qaysi qism local va qaysi qism cloud’da ishlashini izohlang.

## Keyingi dars

Telegram’ni shaxsiy akkauntlar bilan ulash, fon o‘rganish, eslatmalar, xizmat sifatida ishlatish va Docker. Login vaqtini tejash uchun haqiqiy credentialni hech qachon umumiy arxivga qo‘shmang.

## 0.5.0 dars oqimi

Hermes’ni qo‘lda o‘rnatishni ko‘rsatmang: `install.cmd`ning o‘zi o‘rnatadi. Sozlash ustasida profil → AI → Telegram → ovoz → haqiqiy javob sinovi ketma-ketligidan foydalaning. API ID/hash olish uchun usta ichidagi yordamni oching. Claude Max + qo‘shimcha kredit shartini OpenAI loginidan ajrating. Keyin kalendarga vazifa kiriting, xizmat o‘chiq holatdagi ogohlantirishni va muhim xabarlar qoidalarini tushuntiring.
