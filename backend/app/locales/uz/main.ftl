# Mafia Baku Black — @MafGameUzBot
# Locale: uz (O'zbek tili, Lotin yozuvi) — ASOSIY LOCALE
# Project Fluent sintaksisi: https://projectfluent.org/


# ===========================================================
# ONBOARDING (bot guruhga qo'shilganda)
# ===========================================================

onboarding-pick-language =
    👋 Salom! Men Mafia botman.
    Avval guruh tilini tanlang:

onboarding-only-admins-can-pick = ⚠️ Faqat guruh adminlari tilni tanlashi mumkin.

onboarding-grant-admin-perms =
    ✅ Til o'rnatildi.
    Endi meni guruh admini qiling. Quyidagi ruxsatlar kerak:
      ✓ Xabarlarni o'chirish (Delete messages)
      ✓ Foydalanuvchilarni cheklash (Restrict members)
      ✓ Xabarlarni qadash (Pin messages)
    Bu ruxsatlar o'yin davomida guruhni boshqarish uchun kerak.
    @{ $bot_username }ni admin qilib, quyidagi tugmani bosing.

onboarding-completed =
    🎉 Ajoyib! Endi /game buyrug'i bilan o'yin boshlay olasiz.

onboarding-success-toast = ✅ Tayyor! Bot sozlandi.

onboarding-perms-missing =
    ❌ Quyidagi ruxsatlar yetishmayapti: { $perms }
    Iltimos, ularni bering va qayta tekshiring.

btn-check-perms = 🔄 Tekshirish

perm-delete-messages = Xabarlarni o'chirish
perm-restrict-members = Foydalanuvchilarni cheklash
perm-pin-messages = Xabarlarni qadash


# ===========================================================
# /start (shaxsiy chat)
# ===========================================================

start-welcome =
    👋 Salom, { $username }!
    Mafia Baku Black botiga xush kelibsiz.
    Telegram guruhingizda o'yin boshlash uchun guruhga qo'shing.

btn-profile = 👤 Profil
btn-inventory = 🎒 Inventar
btn-buy-diamonds = 💎 Olmos sotib olish
btn-help = ❓ Yordam


# ===========================================================
# DEEPLINK QO'SHILISH FLOW
# ===========================================================

deeplink-invalid = ❌ Noto'g'ri havola. Iltimos, guruhdan qayta urinib ko'ring.

admin-login-deeplink-todo = 🔐 Super admin tizimiga kirish — tez orada qo'llaniladi (Bosqich 3).

join-banned =
    🚫 Siz vaqtinchalik banlandasiz.
    Ban tugashi: { $until }
    Sabab: { $reason }

join-already-in-this-game = 😏 Sabr qil sen o'yindasan o'yinda. Tushunyapsanmi o'yinda.

join-already-in-other-group =
    ❌ Siz allaqachon boshqa guruhda o'yindasiz: { $group_title }.
    Bir vaqtda faqat bitta o'yinda qatnashish mumkin.

join-group-not-found = ❌ Guruh topilmadi yoki bot ushbu guruhda faol emas.

join-no-active-registration =
    ⏱ Kechikdingiz! Ro'yxatdan o'tish vaqti tugagan.
    Keyingi o'yinni kuting.

join-success =
    ✅ Siz o'yinga omadli qo'shildingiz :)

btn-back-to-group = 🔙 Guruhga o'tish


# ===========================================================
# GURUH O'YIN BUYRUQLARI
# ===========================================================

game-onboarding-required =
    ⚠️ Avval botni sozlang: meni guruh admini qiling va kerakli ruxsatlarni bering.

game-todo-mvp = 🎮 /game tez orada qo'llaniladi (Bosqich 1).

leave-not-in-game = ❌ Siz hozir hech qanday o'yinda qatnashmayapsiz.

leave-todo = 🚪 /leave tez orada qo'llaniladi.

stop-todo = 🛑 /stop tez orada qo'llaniladi.


# ===========================================================
# ROL NOMLARI
# ===========================================================

role-citizen = 👨🏼 Tinch aholi
role-detective = 🕵🏻‍♂ Komissar Katani
role-sergeant = 👮🏻‍♂ Serjant
role-mayor = 🎖 Janob
role-doctor = 👨🏻‍⚕ Doktor
role-hooker = 💃 Kezuvchi
role-hobo = 🧙‍♂ Daydi
role-lucky = 🤞🏼 Omadli
role-suicide = 🤦🏼 Suidsid
role-kamikaze = 💣 Afsungar
role-don = 🤵🏻 Don
role-mafia = 🤵🏼 Mafiya
role-lawyer = 👨‍💼 Advokat
role-journalist = 👩🏼‍💻 Jurnalist
role-killer = 🥷 Ninza
role-maniac = 🔪 Qotil
role-werewolf = 🐺 Bo'ri
role-mage = 🧙 Sehrgar
role-arsonist = 🧟 G'azabkor
role-crook = 🤹 Aferist
role-snitch = 🤓 Sotqin


# ===========================================================
# TUNGI ATMOSFERA XABARLARI (guruhga, rol harakatidan so'ng)
# ===========================================================

night-action-msg-don = 🤵🏻 Don navbatdagi o'ljasini tanladi...

night-action-msg-detective-check = 🕵🏼 Komissar Kattani yovuzlarni qidirishga ketdi...

night-action-msg-detective-shoot = 🕵🏼 Komissar Kattani pistoletini o'qladi...

night-action-msg-doctor = 👨🏻‍⚕ Doktor kechki vizitiga otlandi...

night-action-msg-hooker = 💃 Kezuvchining qandaydir mehmoni bor ekan...

night-action-msg-hobo = 🧙‍♂ Daydi shisha butilka uchun ko'chaga chiqdi...


# ===========================================================
# TUN NATIJASI XABARLARI (kun fazasi boshida guruhga)
# ===========================================================

night-result-killed-single =
    🌅 Tunda { $role_emoji_name } { $mention } vaxshiylarcha o'ldirildi.
    Aytishlaricha unikiga { $killer_role_emoji_name } kelgan...

night-result-no-deaths = 🌅 Ishonish qiyin, lekin bu tunda hech kim o'lmadi...

night-result-shield-used = 💫 Kimdir himoyasini ishlatdi!


# ===========================================================
# SO'NGGI SO'Z
# ===========================================================

last-words-prompt-hanged =
    Sizni shavqatsizlarcha osishdi :(
    So'nggi so'zingni aytishing mumkin:

last-words-prompt-killed-night =
    Sizni shavqatsizlarcha o'ldirishdi :(
    So'nggi so'zingni aytishing mumkin:

last-words-broadcast =
    O'limidan oldin kimdir, { $mention } ni qichqirganini eshitdi:
    { $message }


# ===========================================================
# O'YIN RO'YXATGA OLISH / BOSHLASH XATOLARI
# ===========================================================

game-bounty-insufficient = ❌ /game { $required } uchun kamida { $required } olmos kerak. Sizda: { $have }

game-already-running = ❌ Bu guruhda o'yin allaqachon davom etmoqda!

game-cannot-start-not-waiting = ❌ O'yinni faqat ro'yxatdan o'tish fazasida boshlash mumkin.

game-not-enough-players = ❌ Kamida 4 o'yinchi kerak. Hozircha yetarli emas.

join-game-full = ❌ O'yin to'lib qoldi. Maksimum 30 o'yinchi.

error-only-admins = ❌ Bu buyruq faqat guruh adminlari uchun.


# ===========================================================
# RO'YXATDAN O'TISH XABARI
# ===========================================================

registration-message =
    🎲 O'yin uchun ro'yxatdan o'tish boshlandi!
    Pastdagi tugmani bosing.

    ⏱ Vaqt: { $timer }
    👥 Qatnashchilar ({ $count }):
    { $players }

registration-no-players-yet = — (hali hech kim qo'shilmagan)

registration-bounty = 💎 Har g'olibga: { $per_winner } olmos (escrow: { $pool })

btn-join-game = 🎮 O'yinga qo'shilish


# ===========================================================
# FAZA O'ZGARISHLARI
# ===========================================================

phase-night-start = 🌃 Tun #{ $round } boshlandi. Rollar harakatga o'tdi...

phase-day-start = ☀️ Kun #{ $round } boshlandi. Muhokama qiling!

phase-voting-start = 🗳 Ovoz berish vaqti! /vote @user


# ===========================================================
# OVOZ BERISH
# ===========================================================

vote-not-in-voting = Ovoz berish fazasi emas.

vote-not-alive = Siz o'lgansiz, ovoz berolmaysiz.

vote-target-required = /vote @username yoki kimningdir xabariga reply qiling.

vote-target-invalid = Bu o'yinchi yo'q yoki o'lgan.

vote-recorded = { $voter } → { $target } ga ovoz berdi.

vote-recorded-anon = ✅ Ovozingiz qabul qilindi (anonim)


# ===========================================================
# /leave VA /stop
# ===========================================================

leave-not-allowed = Bu guruhda /leave taqiqlangan.

leave-already-dead = Siz allaqachon o'lgansiz.

leave-broadcast = { $mention } bu shaharning yovuzliklariga chiday olmadi va o'z joniga qasd qildi.

unjoin-success = ✅ { $name } ro'yxatdan chiqib ketdi.

stop-no-game = Hozir hech qanday o'yin yo'q.

stop-not-allowed = Bu guruhda /stop taqiqlangan.

stop-success = 🛑 O'yin to'xtatildi.

extend-not-in-registration = Faqat ro'yxatdan o'tish fazasida uzaytirsa bo'ladi.

extend-success = ⏱ Vaqt { $seconds } sekundga uzaytirildi.


# ===========================================================
# TUNGI SO'ROVLAR (o'yinchiga shaxsiy chatda)
# ===========================================================

night-prompt-don = 🤵🏻 Don, kechqurun kimni o'ldirmoqchisiz?

night-prompt-doctor = 👨🏻‍⚕ Doktor, kechqurun kimni davolaysiz?

night-prompt-hooker = 💃 Kezuvchi, kechqurun kimni uxlatasiz?

night-prompt-detective = 🕵🏼 Komissar, tanlovingiz?

night-prompt-detective-check-only = 🕵🏼 Komissar, 1-tunda faqat tekshirish mumkin. Kimni tekshirasiz?

night-prompt-detective-both = 🕵🏼 Komissar, kimni tekshirasiz yoki o'ldirasiz? 🔍 = tekshirish, 🔫 = o'ldirish

btn-skip = ⏭ O'tkazib yuborish

night-skipped = Navbat o'tkazib yuborildi.

night-skipped-confirm = ✅ Bu tunda hech kim bilan ish ko'rmadingiz.

night-not-in-active-game = Siz hozir hech qanday o'yinda yo'qsiz.

night-not-in-night-phase = Tun fazasi tugagan.

night-cannot-act = Siz bu harakatni qilolmaysiz.

night-target-invalid = Tanlangan o'yinchi yo'q yoki o'lgan.

night-action-recorded = ✅ { $target } tanlandi.

night-action-confirmed = ✅ Sizning tanlovingiz: { $target }


# ===========================================================
# O'YIN TUGASHI
# ===========================================================

game-end-winner =
    🏆 O'yin tugadi!

    { $team } g'olib bo'ldi!

    📋 Rollar:

game-cancelled = ❌ O'yin bekor qilindi.

team-citizens = 👨🏼 Tinch aholi

team-mafia = 🤵🏼 Mafiya

team-singleton = 🎯 Singleton


# ===========================================================
# TURLI XABARLAR
# ===========================================================

click-to-join-private = Bot bilan private chatda ochiladi...


# ===========================================================
# TUNGI ATMOSFERA XABARLARI — YANGI ROLLAR
# ===========================================================

night-action-msg-lawyer = 👨‍💼 Advokat o'z mijozini himoyalashga ketdi...

night-action-msg-journalist = 👩🏼‍💻 Jurnalist tunda izlanmoqda...

night-action-msg-killer = 🥷 Ninza qonli ishini boshladi...

night-action-msg-maniac = 🔪 Qotil qonli pichog'ini qayradi...

night-action-msg-werewolf = 🐺 Bo'ri tunda uvlay boshladi...

night-action-msg-arsonist = 🧟 G'azabkor yangi qurbonini belgiladi...

night-action-msg-crook = 🤹 Aferist yangi qiyofa kiyishni rejalashtirmoqda...

night-action-msg-snitch = 🤓 Sotqin yashirin ma'lumot qidirib ko'chaga otildi...

night-action-msg-kamikaze = 🧞‍♂️ Afsungar mistik kuchlarini chaqirmoqda...


# ===========================================================
# TUNGI SO'ROVLAR — YANGI ROLLAR (o'yinchiga shaxsiy chatda)
# ===========================================================

night-prompt-hobo = 🧙‍♂ Daydi, kimning uyiga butilka uchun borasiz?

night-prompt-lawyer = 👨‍💼 Advokat, qaysi mafia a'zosini himoyalaysiz?

night-prompt-journalist = 👩🏼‍💻 Jurnalist, kimni tekshirasiz?

night-prompt-killer = 🥷 Ninza, kimni o'ldirasiz? (himoyalarni teshib o'tasiz)

night-prompt-maniac = 🔪 Qotil, kimni o'ldirasiz?

night-prompt-mafia = 🤵🏼 Mafiya, Don bilan kim haqida kelishdingiz?

night-prompt-arsonist = 🧟 G'azabkor, navbatdagi qurboniyingiz?

night-prompt-crook = 🤹 Aferist, kim nomidan ovoz berasiz ertaga?

night-prompt-snitch = 🤓 Sotqin, kimni Komissar tekshiradi deb o'ylaysiz?


# ===========================================================
# FEEDBACK DM (tun natijasidan keyin o'yinchiga shaxsiy)
# ===========================================================

feedback-detective-result = 🕵🏼 { $target } ning roli — { $role } ekan.

feedback-doctor-saved = 👨🏻‍⚕ Siz { $target } ni davoladingiz! Uning mehmonlari edi: { $visitors }

feedback-doctor-no-visitors = 👨🏻‍⚕ Siz { $target } ni davoladingiz. Uning yoniga hech kim kelmadi.

feedback-hooker-confirm = 💃 Siz { $target } ni uxlatdingiz.

feedback-hooker-target = Ana 💊 dori ta'sir qila boshladi endi sen bir kun uxlaysan...


# ===========================================================
# AFK
# ===========================================================

afk-kicked = { $mention } AFK uxlab qoldi va o'yindan chiqdi (XP -50)


# ===========================================================
# STATISTIKA BUYRUQLARI
# ===========================================================

stats-no-games = Sizda hali bironta o'yin yo'q. /game bilan boshlang!

stats-period-todo = Davriy statistika tez orada qo'llanadi (Bosqich 2)

stats-no-role-data = Hech qanday rol ma'lumoti yo'q

stats-role-no-data = { $role } rol bo'yicha o'yin o'ynamadingiz

stats-role-detail =
    📊 { $role } bo'yicha:
    🎮 O'yinlar: { $games }
    🏆 G'alabalar: { $wins }
    📈 WR: { $winrate }%
    💎 ELO: { $elo }

stats-personal =
    👤 { $name }

    🎮 O'yinlar: { $games }   🏆 G'alabalar: { $wins }   💔 Mag'lubiyat: { $losses }
    📈 Winrate: { $winrate }%   💎 ELO: { $elo }
    ⭐ XP: { $xp }   🏅 Level: { $level }

    🔥 Joriy seriya: { $streak }   📌 Eng uzun: { $longest }

    🎭 Sevimli rollar: { $top_roles }

    👨🏼 Tinch aholi: { $citizen_games } o'yin, { $citizen_wins } g'alaba
    🤵🏼 Mafiya: { $mafia_games } o'yin, { $mafia_wins } g'alaba
    🎯 Singleton: { $singleton_games } o'yin, { $singleton_wins } g'alaba

top-empty = Leaderboard hali bo'sh

top-group-only = Bu buyruq faqat guruhda ishlaydi

top-header = 🏆 Top 10 ({ $sort } bo'yicha):

global-top-header = 🌍 Global Top 10:

profile-target-not-found = Foydalanuvchi topilmadi. Reply qiling yoki @username yozing.

profile-no-games = { $name } hali o'yin o'ynamagan

group-stats-no-games = Bu guruhda hali o'yin bo'lmagan

group-stats-message =
    📊 Guruh statistikasi:
    🎮 Jami o'yinlar: { $total_games }
    ⏱ O'rtacha davom: { $avg_duration } daqiqa
    👥 O'rtacha o'yinchi: { $avg_players }

    Tomonlar winrate:
    👨🏼 Tinch: { $citizens_wr }%
    🤵🏼 Mafiya: { $mafia_wr }%
    🎯 Singleton: { $singleton_wr }%


# ===========================================================
# PROFIL VA INVENTAR
# ===========================================================

profile-info =
    👤 { $name }
    { $is_premium ->
        [true] 👑 Premium (tugashi: { $premium_until })
       *[false] —
    }

    💎 Olmos: { $diamonds }
    💵 Dollar: { $dollars }
    ⭐ XP: { $xp }   🏅 Level: { $level }

inventory-header = 🎒 Sizning inventaringiz:

inv-toggle-on = ✅ Yoqildi

inv-toggle-off = ⬜ O'chirildi

btn-shop = 🛒 Do'kon

btn-back = 🔙 Orqaga


# ===========================================================
# DO'KON
# ===========================================================

shop-welcome =
    🛒 Mafia do'koniga xush kelibsiz!
    Nimani sotib olmoqchisiz?

shop-diamonds-header = 💎 Olmos paketlari:

shop-items-header = 🛡 Qurol va himoyalar (sizda 💎 { $diamonds }):

shop-premium-info =
    👑 Premium foydalanuvchi:
    • 2x himoya
    • Kezuvchiga qarshi himoya
    • Boshqa imtiyozlar

btn-buy-items = 🎒 Qurol/himoya

btn-buy-premium = 👑 Premium

btn-buy-premium-30d = 👑 30 kun — 💎 { $price }

buy-insufficient = ❌ Olmos yetarli emas

buy-success = ✅ Sotib olindi!

premium-activated = 👑 Premium aktivlashtirildi: { $days } kun

payment-success = ✅ To'lov muvaffaqiyatli! +💎 { $diamonds }

payment-failed = ❌ To'lov xato bo'ldi


# ===========================================================
# GIVEAWAY
# ===========================================================

give-amount-required = ❌ /give 50 kabi miqdor yozing

give-amount-too-small = ❌ Miqdor 1 dan kam bo'lmasligi kerak

give-cannot-self = ❌ O'zingizga hadya qilolmaysiz

give-insufficient = ❌ Olmos yetarli emas (sizda 💎 { $have }, kerak 💎 { $need })

give-target-not-found = ❌ Foydalanuvchi topilmadi

give-direct-success = 💎 { $sender } → { $receiver }: { $amount } olmos hadya qildi!

give-creating = 💎 Giveaway yaratilmoqda...

give-group-message =
    🎁 { $sender } — { $amount } olmos giveaway boshladi!
    Birinchi bosganlar ko'proq oladi.

give-no-clicks = 🎁 Giveaway tugadi — hech kim bosmadi

give-results-header = 🎁 Giveaway natijasi:

btn-claim-diamond = 💎 Olmos olish

giveaway-clicked-ok = ✅ Bosildi!

giveaway-already-clicked-or-finished = ❌ Allaqachon bosgansiz yoki tugadi


# ===========================================================
# OVOZ BERISH UI (inline tugmali)
# ===========================================================

voting-prompt = 🗳 Ovoz berish vaqti! Tirik o'yinchilar: { $count }. Pastdagi tugma orqali ovoz bering:

vote-skip-button = ❌ Hech kim

vote-cannot-self = ❌ O'zingizga ovoz berolmaysiz

vote-recorded-toast = ✅ Sizning ovozingiz: { $target }

vote-skipped-toast = ✅ "Hech kim" tanladingiz


# ===========================================================
# OSISH TASDIQLASH
# ===========================================================

hanging-confirm-prompt =
    ⚖️ { $target } ni osishni tasdiqlaymi?
    👍 = ha, 👎 = yo'q

hanging-yes = 👍 Ha, osmoq kerak

hanging-no = 👎 Yo'q

hanging-confirm-expired = ❌ Tasdiqlash vaqti tugagan


# ===========================================================
# SEHRGAR REAKTIV XABARLARI (o'yinchiga shaxsiy)
# ===========================================================

mage-attacked = 🧙 Sizga { $attacker_role } hujum qildi.\nKechirasizmi yoki o'ldirasizmi?

mage-forgive = 💚 Kechirish

mage-kill = 💀 O'ldirish

mage-forgive-confirm = Kechirildi

mage-forgive-confirm-text = 💚 Siz kechirdingiz. U tirik qoldi.

mage-kill-confirm = O'ldirildi

mage-kill-confirm-text = 💀 { $target } o'ldirildi (sizning lanatingiz)


# ===========================================================
# G'AZABKOR (ARSONIST) XABARLARI
# ===========================================================

arsonist-final-night-button = 🔥 Oxirgi tun!

arsonist-queued = 🧟 { $target } ro'yxatga qo'shildi

arsonist-final-confirm = 💥 Oxirgi tun aktivlashdi! Barcha tanlaganlaringiz o'ladi.


# ===========================================================
# AFSUNGAR (KAMIKAZE) XABARLARI
# ===========================================================

kamikaze-choose-victim = 🧞 Sizni osishdi! O'zingiz bilan birga kim bilan ketmoqchisiz?

kamikaze-took-victim = 🔥 { $kamikaze } o'lganida { $victim } ni o'zi bilan jahannamga olib ketdi!

kamikaze-took-confirm = Tanlandi

kamikaze-took-confirm-text = 🧞 Siz { $target } ni o'zingiz bilan olib ketdingiz.


# ===========================================================
# BO'RI TRANSFORMATSIYA XABARLARI (guruhga)
# ===========================================================

transform-werewolf-to-mafia = 🐺 { $mention } yangi qiyofada paydo bo'ldi: bundan buyon 🤵🏼 Mafiya sifatida o'ynaydi!

transform-werewolf-to-sergeant = 🐺 { $mention } yangi qiyofada paydo bo'ldi: bundan buyon 👮🏻‍♂ Serjant sifatida tinch aholiga xizmat qiladi!


# ===========================================================
# SOTQIN OSHKOR XABARI (guruhga)
# ===========================================================

snitch-reveal-broadcast = 📢 Sotqin xabari: { $target } ning roli — { $role } ekan!


# ===========================================================
# YORDAM VA QOIDALAR
# ===========================================================

help-private =
    ❓ Yordam (private chat):

    /start — botni ishga tushirish
    /profile — sizning profil
    /inventory — qurollar/himoyalar
    /stats — statistika
    /global_top — global reyting
    /rules — qoidalar

    Guruhlarda /game bilan o'yin boshlang.

help-group =
    ❓ Guruh buyruqlari:

    /game [bounty] — yangi o'yin
    /leave — chiqib ketish
    /vote @user — ovoz
    /give amount [reply] — olmos hadya
    /stats /top /group_stats /profile — statistika
    /extend N — vaqtni uzaytirish
    /stop — bekor qilish (admin)
    /rules — qoidalar

rules-summary =
    📖 Mafia Baku Black — qoidalar:

    Shahar ikki tomonga bo'linadi: tinch aholi va mafiya.
    Har kecha mafiya bitta odamni o'ldiradi. Kunduz aholi
    ovoz berib birini osadi. Komissar Kattani yovuzlarni
    fosh etadi, Doktor qurbonlarni himoyalaydi.

    Singleton rollar (Qotil, Bo'ri, Sehrgar va boshqalar)
    yakka holda o'z g'alaba shartlari bilan o'ynaydi.

    G'alaba: mafiyani yo'q qilsang — tinch aholi g'olib.
    Tinch aholi sonini tenglashtirsang — mafiya g'olib.

    /game bilan boshlang. Omad!
