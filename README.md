# Tungi Toshkent — reklamalar

Bu ombordan **Tungi Toshkent** o'yini shahardagi reklama panellari va "O'yin boshlanmoqda" ekrani uchun reklamalarni oladi.

- `ads.json` — hozirgi reklamalar ro'yxati (rasm/video manzili va muddati)
- `media/` — reklama rasmlari va videolari

Reklamalar **Promokod ADMIN** ilovasining "📢 Reklama" bo'limidan qo'yiladi. Qo'lda o'zgartirish shart emas.

Muallif: KOMRONBEK SHAROPOV · Telegram @VFF_UZB

## Reklama qo'yish — Telegram bot orqali (eng oson)

1. Telegram'da o'z botingizni oching.
2. **Rasm yoki video** (20 MB gacha) yuboring, izohiga muddatni yozing: `3 kun`, `12 soat`, `1 hafta`, `1 oy` yoki `muddatsiz` (yozilmasa — 1 kun).
3. 10–20 daqiqada bot "✅ Reklama qabul qilindi" deb javob beradi va reklama hamma o'yinchilarda chiqadi.

Buyruqlar: `/reklamalar` — efirdagilar, `/ochir 2` — o'chirish (`/ochir hammasi`), `/kanal @nom` — bosh menyudagi kanal.

Bot faqat admin (@VFF_UZB) xabarlarini qabul qiladi. Ishlash tartibi: `.github/workflows/telegram.yml` har 10 daqiqada `tools/bot.py` ni ishga tushiradi; bot kaliti omborning shifrlangan `BOT_TOKEN` sozlamasida.
