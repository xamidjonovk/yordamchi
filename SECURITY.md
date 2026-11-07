# Maxfiylik va tarqatish

Kod va shaxsiy instance alohida. GitHub’ga faqat ko‘rib chiqilgan kod, umumiy hujjatlar va sun’iy test ma’lumotlari yuboriladi.

## Repoga kirmaydigan ma’lumotlar

`.env`, Telegram `.session` va `telegram.json`, OAuth `auth.json`, nazorat tokenlari, shaxsiy `config.json`, bilim ombori, chatlar, yuklangan fayllar, audio yozuvlar, backup va private transfer arxivlari. Screenshotda ham ism, username yoki login kodi bo‘lishi mumkin.

`.gitignore` yangi fayllarni yashiradi; oldin commit qilingan ma’lumotni tarixdan o‘chirmaydi. `.dockerignore` build kontekstini cheklaydi. Release yig‘ish aniq papkalar ro‘yxati va skandan foydalanadi.

## Tekshirish

```bash
python scripts/privacy_scan.py
python scripts/privacy_scan.py --history
python scripts/privacy_scan.py --private-root SHAXSIY_INSTANCE_PAPKASI
```

Skan kalit/token/telefon/private-key andozalari va berilgan mahalliy credentiallarning aniq qiymatlarini qidiradi. Faqat joy va toifani chiqaradi. Barcha sir turlari, rasmdagi yozuv, tashqi fork/cache va o‘chirilgan remote obyektlarni to‘liq tekshira olmaydi.

## Web chegarasi

- Server faqat `127.0.0.1`da, bitta foydalanuvchi uchun ishlaydi.
- Har ishga tushishda tasodifiy token; API’da Bearer header majburiy.
- Host/Origin tekshiruvi cross-origin so‘rov va DNS rebindingni cheklaydi.
- Token URL fragmentidan olinib manzildan o‘chiriladi; tabning sessionStorage’ida qoladi.
- Hujjat yo‘li foydalanuvchidan olinmaydi; upload vaqtinchalik xavfsiz nomga yoziladi.
- Provider xatosining xom matni brauzerga chiqmaydi.
- Bu ko‘p foydalanuvchili internet xizmati emas. Reverse proxy orqali ommaga ochmang.

## Haqiqiy kalit chiqib ketsa

Avval provayderda kalitni bekor qilib, yangisini oling. Telegram sessiyasi chiqsa Telegram Devices bo‘limidan uni tugating. Keyin tarix, tarqalgan nusxa va artefaktlarni tekshiring. Faqat oxirgi fayldan o‘chirish yetmaydi.

## Dars nusxasi

Eski private loyiha tarixida shaxsiy identifikatorlar bo‘lishi mumkin. Dars uchun `scripts/export_public.py` yaratgan yangi tarixli nusxadan foydalaning. README, fayllar, rasmlar va yangi tarixni tarqatishdan oldin tekshiring. Private repo ham credential saqlash joyi emas.

## Sozlash ustasi

OAuth faqat tanlangan provayderga yuboriladi; xom login chiqishi brauzerga chiqmaydi. Rasmiy login havolasi/vaqtinchalik device code autentifikatsiyalangan local API’da ko‘rsatiladi. Telegram kodi va 2FA paroli formadan yuborilgach maydonlar tozalanadi, ular logga yoki repoga yozilmaydi. Telegram sessiyasi pending login vaqtida bitta runtime lock bilan saqlanadi, vaqt tugaganda yoki server yopilganda uziladi.

Muhim xabar preview’lari instance’dagi `data/message-inbox.sqlite3`da (500 yozuvgacha) saqlanadi. Ular ham shaxsiy ma’lumot; backup va instance papkasini ommaga yubormang. Yangi Telegram loginidan oldin ishlayotgan xizmatni to‘xtating.
