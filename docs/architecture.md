# Arxitektura — bir so‘rovning sayohati

```mermaid
sequenceDiagram
    actor User as Foydalanuvchi
    participant UI as Brauzer
    participant API as Local API
    participant Vault as Bilim ombori
    participant Agent as Hermes
    participant Model as AI modeli
    User->>UI: Savol yoki tekshirilgan ovoz matni
    UI->>API: Bearer token bilan POST /api/chat
    API->>API: Host, Origin, hajm, parallel vazifani tekshirish
    API->>Vault: Tegishli manbalarni izlash
    Vault-->>API: Matn, manba IDsi, sana, ishonch turi
    API->>Agent: Profil + dalillar + savol
    Agent->>Model: Hisobga ulangan model so‘rovi
    Model-->>Agent: Javob yoki vosita chaqirig‘i
    Agent-->>API: Strukturali haqiqiy natija
    API-->>UI: Javob matni yoki xavfsiz xato
    UI-->>User: Matn; ixtiyoriy brauzer ovozi
```

## Asosiy kod xaritasi

| Fayl | Mas’uliyat |
|---|---|
| `cli.py` | `hpa` buyruqlari va `web` kirish nuqtasi |
| `web_app.py` | Mahalliy autentifikatsiyalangan HTTP API, upload va suhbat |
| `web/` | O‘zbekcha responsiv interfeys, 3D matematik tasvir, Web Speech |
| `personalization.py` | Profil maydonlarini tekshirish va barcha javoblarga kontekst berish |
| `voice_common.py` | Instance yo‘llari va konfiguratsiya |
| `hermes_tasks.py` | Hermes subprocess, session xaritasi, retrieval, o‘rganish ishchisi |
| `wiki_store.py` | Faol manbalar, faktlar, bog‘lanishlar va Markdown wiki |
| `documents.py` | Hujjat formatlaridan matn/sahifa ajratish |
| `telegram_agent.py` | Egasi buyruqlari, topshiriqlar va xabar yo‘naltirish |
| `voice_service.py` | Telegram jonli audio va Gemini oqimi |
| `agent_store.py`, `services.py` | Diskdagi jadval, process va fon xizmatlari |
| `scripts/privacy_scan.py` | Ishchi fayl / Git tarixi bo‘yicha maxfiylik tekshiruvi |
| `scripts/export_public.py` | Eski tarixsiz tarqatish uchun alohida repo |

## Chegaralar

Web panel Telegram xizmatidan mustaqil; hisoblar sozlanmaganda ham profil va bilimlarni boshqaradi. Web’dan bir vaqtda bitta AI topshirig‘i qabul qilinadi. Parallel ikkinchi so‘rov 409 oladi. Telegram xizmati alohida process; profil/learning o‘zgarishidan keyin qayta boshlanadi.

Manbalar hech qachon egasi buyrug‘ining o‘rnini bosmaydi. AI suhbat matni va bilimlar lokal saqlanishi mumkin; provayderlar ham o‘z saqlash qoidalariga ega. Qidiruvdan chiqarish alohida fizik o‘chirish bilan bir xil emas.

## Masshtab

Hozirgi LLM-Wiki JSON manifest va fayllarni o‘qiydi; SQL/vector server yo‘q. Kichik shaxsiy ombor uchun sodda, tekshirish va ko‘chirish oson. Katta hajm uchun indeks va incremental qidiruv kelajakdagi ish; mavjud `semantic` opsiyasi faol wiki’da semantik qidiruvni yoqmaydi.

## 0.5.0 — birlashtirilgan o‘rnatish

`install.cmd` → `scripts/install.ps1` Python va calls/FFmpeg kutubxonalarini, keyin shaxsiy Hermes runtime’ni tayyorlaydi. `hpa web --setup` brauzerda o‘zbekcha ustani ochadi. Yangi instance Hermes dasturi/dependency va auth profilini bir `HERMES_HOME` ichida saqlaydi; bu launcher uchun zarur.

`setup_wizard.py` CLI OAuth jarayonidan faqat rasmiy havola/kodni ajratadi, xom credential yoki provider logini qaytarmaydi. Telegram login sessiyasi vaqtinchalik runtime lock bilan himoyalangan; kod/2FA/owner qadamlari keyin uziladi. AI modelining haqiqiy javobi tekshirilmaguncha yakunlash ochilmaydi.

`dashboard.py` mahalliy xabar inbox’ini saqlaydi, ishlayotgan xizmatga schedule/cancel so‘rovini yuboradi. Xizmat o‘chiq bo‘lsa supervisor/runtime lock ostida diskka yozadi. Brauzer asosiy xizmat bilan parallel `Store` yozuvchisini yaratmaydi. Xabarlar qoida yoki unread preview sifatida belgilanadi, model ularni mukammal saraladi degan da’vo yo‘q.
