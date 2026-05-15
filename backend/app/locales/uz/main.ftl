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
    👋 Salom, <b>{ $username }</b>!

    🎭 <b>Mafia Baku Black</b> botiga xush kelibsiz!

    Bu yerda siz:
    • 🎮 Telegram guruhingizda mafia o'yini o'ynay olasiz
    • 💎 Olmos, 💵 dollar, ⭐ XP yig'asiz
    • 🏆 Yutuqlarni qo'lga kiritasiz va ELO oshirasiz
    • 👑 Premium maqomga ega bo'lasiz

    Quyidagi tugmalardan birini tanlang:

btn-profile = 👤 Profil
btn-inventory = 🎒 Inventar
btn-buy-diamonds = 💎 Olmos sotib olish
btn-help = ❓ Yordam

btn-add-to-group = ➕ Guruhga qo'shish

btn-language = 🌐 Til

btn-rules = 📖 O'yin qoidalari


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

night-action-msg-detective-check = 🕵🏻‍♂ Komissar katani yovuzlarni qidirishga ketdi...

night-action-msg-detective-shoot = 🕵🏻‍♂ Komissar katani pistoletini o'qladi...

night-action-msg-doctor = 👨🏻‍⚕ Doktor tungi navbatchilikka ketti...

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
    Aholidan kimdir { $role_emoji } { $role_name } { $mention } o'limidan oldin:
    <i>{ $message }</i> deb qichqirganini eshitgan.

last-words-sent-confirm = ✅ Sizning habaringiz guruhga yuborildi!


# ===========================================================
# FLOOD CONTROL — buyruqlar spam'iga jahl xabarlar
# ===========================================================

flood-alert-1 = 😤 Hoy! Tinchlanvol, bot sening uchun robot emas. Ikki sekund kut!
flood-alert-2 = 🤨 Yana bosding-a? Qo'lingda spinnerga aylanib qoldi shekilli buyruq tugmasi.
flood-alert-3 = 🙄 Birovning robotini qiynama, og'ayni. Sabring yo'qmi yoki klaviaturang buzilganmi?
flood-alert-4 = 😡 Bas qil! Yana bir marta tegsang, jahlim chiqib chatdan otib yuboraman.


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

phase-night-start = 🌃 Tun #{ $round }. Shamollar tundagi mish-mishlarni butun shaharga yetkazmoqda...

phase-night-start-1 = 🌃 Tun #{ $round }. Shamollar tundagi mish-mishlarni butun shaharga yetkazmoqda...
phase-night-start-2 = 🌑 Tun #{ $round }. Shahar oy nuri ostida pichirlay boshladi — kimdir nafas olishni unutdi...
phase-night-start-3 = 🌃 Tun #{ $round }. Eshiklarni mahkamlang, ko'chada qadamlar eshitilmoqda...
phase-night-start-4 = 🦉 Tun #{ $round }. Boyqush hushyor, lekin u ham hammasini ko'ra olmaydi...
phase-night-start-5 = 🌌 Tun #{ $round }. Yulduzlar guvoh — kechasi shahar uxlamaydi, faqat o'zini uxlayotgandek ko'rsatadi.

phase-day-start = ☀️ Kun #{ $round }. Quyosh chiqib tunda to'kilgan qonlarni quritdi...

phase-day-start-1 = ☀️ Kun #{ $round }. Quyosh chiqib tunda to'kilgan qonlarni quritdi...
phase-day-start-2 = 🌅 Kun #{ $round }. Shahar uyg'ondi — ammo kimdir endi uyg'onmaydi.
phase-day-start-3 = ☕ Kun #{ $round }. Nonushta vaqti keldi, lekin ba'zi joylar bo'sh qoldi...
phase-day-start-4 = 🐓 Kun #{ $round }. Xo'roz qichqirdi — hisob-kitob qilish vaqti.
phase-day-start-5 = 🌤 Kun #{ $round }. Tong otdi, lekin tunning qora soyalari hali ham ko'cha boshida.


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

extend-indefinite = ⏳ Ro'yxatdan o'tish uzaytirildi.

game-launched-by-admin = 🚀 O'yin boshlandi!


# ===========================================================
# TUNGI SO'ROVLAR (o'yinchiga shaxsiy chatda)
# ===========================================================

night-prompt-don = 🤵🏻 Don, kechqurun kimni o'ldirmoqchisiz?

night-prompt-doctor = 👨🏻‍⚕ Doktor, kechqurun kimni davolaysiz?

night-prompt-hooker = 💃 Kezuvchi, kechqurun kimni uxlatasiz?

night-prompt-detective = 🕵🏼 Komissar, tanlovingiz?

night-prompt-detective-check-only = 🕵🏼 Komissar, 1-tunda faqat tekshirish mumkin. Kimni tekshirasiz?

night-prompt-detective-both = 🕵🏼 Komissar, kimni tekshirasiz yoki o'ldirasiz? 🔍 = tekshirish, 🔫 = o'ldirish

night-prompt-detective-prior-header = 🕵🏼 <b>Avval tekshirgan o'yinchilar:</b>
night-prompt-detective-prior-line = • <b>{ $name }</b> — { $role }
night-prompt-detective-chooser = 🕵🏼 Bu tunda nima qilamiz?
night-prompt-detective-target-list-check = 🔍 Kimni tekshirasiz?
night-prompt-detective-target-list-kill = 🔫 Kimni otasiz?
btn-detective-check = 🔍 Tekshirish
btn-detective-kill = 🔫 O'ldirish
night-no-targets = ❌ Hozir hech kimni tanlay olmaysiz.

btn-skip = ⏭ O'tkazib yuborish

night-skipped = Navbat o'tkazib yuborildi.

night-skipped-confirm = ✅ Bu tunda hech kim bilan ish ko'rmadingiz.

night-not-in-active-game = Siz hozir hech qanday o'yinda yo'qsiz.

night-not-in-night-phase = Tun fazasi tugagan.

night-cannot-act = Siz bu harakatni qilolmaysiz.

night-target-invalid = Tanlangan o'yinchi yo'q yoki o'lgan.

night-action-recorded = ✅ { $target } tanlandi.

night-action-confirmed = ✅ Sizning tanlovingiz: <b>{ $target }</b>

mafia-team-pick-broadcast = 🤵🏼 <b>{ $role }</b> ({ $actor }) tanlovi: <b>{ $target }</b>


# ===========================================================
# O'YIN TUGASHI
# ===========================================================

game-end-winner =
    🏆 O'yin tugadi!

    { $team } g'olib bo'ldi!

    📋 Rollar:

game-cancelled = ❌ O'yin bekor qilindi.

game-cancelled-not-enough-players =
    ⏱ O'yin boshlanmadi — vaqt tugaganda o'yinchilar yetarli emas edi (kamida { $min_players } ta kerak).
    Keyingi o'yinni boshlash uchun /game buyrug'idan foydalaning.

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

night-action-msg-lawyer = 👨‍💼 Advokat Mafiani ximoya qilish uchun qidiryapti...

night-action-msg-journalist = 👩🏼‍💻 Jurnalist tunda izlanmoqda...

night-action-msg-killer = 🥷 Ninza qonli ishini boshladi...

night-action-msg-maniac = 🔪 Qotil butalar orasiga yashirinib oldi va pichoqni qinidan chiqardi...

night-action-msg-werewolf = 🐺 Bo'ri tunda uvlay boshladi...

night-action-msg-arsonist = 🧟 G'azabkor yangi qurbonini belgiladi...

night-action-msg-crook = 🤹 Aferist yangi qiyofa kiyishni rejalashtirmoqda...

night-action-msg-snitch = 🤓 Sotqin malumot to'plash uchun izlanishni boshladi...

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

feedback-doctor-saved = 👨🏻‍⚕ Siz - <b>{ $target }</b> ni davoladingiz:) Uning mehmoni { $visitors } edi.

feedback-doctor-no-visitors = 👨🏻‍⚕ Doktor yordam berolmadi..

feedback-hooker-confirm = 💃 Siz { $target } ni uxlatdingiz.

feedback-hooker-target = Ana 💊 dori ta'sir qila boshladi endi sen bir kun uxlaysan...

mafia-kill-broadcast = 🤵🏼 Mafianing ovoz berish jarayonida { $mention } shavqatsizlarcha o'ldirildi 🩸


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
    ⭐ ID: <code>{ $id }</code>

    👤 { $name }

    💵 Dollar: { $dollars }
    💎 Olmos: { $diamonds }

    🛡 Himoya: { $shield }
    ⛑ Qotildan himoya: { $killer_shield }
    ⚖️ Ovoz berishni himoya qilish: { $vote_shield }
    🔫 Miltiq: { $rifle }

    🎭 Maska: { $mask }
    📁 Soxta hujjat: { $fake_document }
    🃏 Keyingi o'yindagi rolingiz: { $next_role }

    🎯 G'alabalar: { $wins }
    🎲 Jami o'yinlar: { $games_total }

inventory-header = 🎒 Sizning inventaringiz:

inv-toggle-on = ✅ Yoqildi

inv-toggle-off = ⬜ O'chirildi

inv-no-items = 🚫 Sizda bu narsadan yo'q.

# Single-line toggle button labels — used for profile inline keyboard
# Format: <item_emoji> - 🟢 ON  or  <item_emoji> - 🔴 OFF  or  <item_emoji> - 🚫 0
btn-toggle-on = { $emoji } - 🟢 ON
btn-toggle-off = { $emoji } - 🔴 OFF
btn-toggle-empty = { $emoji } - 🚫 0

btn-shop = 🛒 Do'kon
btn-buy-dollars = 💵 Xarid qilish
btn-buy-diamonds = 💎 Xarid qilish
btn-premium-groups = 👑 Premium guruhlar
btn-news = 📢 Yangiliklar
btn-pick-next-role = 🃏 Keyingi rolni tanlash
btn-clear-next-role = 🃏 Tanlovni bekor qilish
pick-role-prompt = 🃏 <b>Keyingi o'yinda qaysi rolda o'ynamoqchisiz?</b>
pick-role-confirmed = ✅ Keyingi o'yinda { $role } rolida o'ynaysiz!
pick-role-already-chosen = ℹ️ Siz allaqachon rol tanlagansiz.
pick-role-cleared = ❎ Rol tanlovi bekor qilindi.
btn-back = 🔙 Orqaga

btn-exchange = 🔁 Konvertatsiya

btn-close = ❎ Yopish


# ===========================================================
# DO'KON
# ===========================================================

shop-welcome =
    🛒 Mafia do'koniga xush kelibsiz!
    Nimani sotib olmoqchisiz?

shop-welcome-balance =
    🛒 <b>Do'kon</b>

    Sizning balansingiz: <b>{ $diamonds }</b> 💎  <b>{ $dollars }</b> 💵

shop-diamonds-header = 💎 Olmos paketlari:

shop-no-items = 🚫 Bu valyutada hech narsa yo'q

shop-items-header =
    🛡 <b>Itemlar</b>

    Balans: <b>{ $diamonds }</b> 💎  <b>{ $dollars }</b> 💵

    Narxni belgilangan valyutada to'lang.

shop-premium-info =
    👑 Premium foydalanuvchi:
    • 2x himoya
    • Kezuvchiga qarshi himoya
    • Boshqa imtiyozlar

btn-buy-items = 🎒 Qurol/himoya

btn-buy-premium = 👑 Premium

btn-buy-premium-30d = ⭐ 30 kun premium — { $price } 💎

buy-insufficient = ❌ Olmos yetarli emas

buy-success = ✅ Sotib olindi!

buy-success-detailed = ✅ { $item } sotib olindi! ({ $cost } { $currency })

buy-insufficient-diamonds = 💎 Olmosingiz yetarli emas

buy-insufficient-dollars = 💵 Dollarlaringiz yetarli emas

premium-activated = 👑 Premium aktivlashtirildi: { $days } kun

payment-success = ✅ To'lov muvaffaqiyatli! +💎 { $diamonds }

payment-failed = ❌ To'lov xato bo'ldi


# ===========================================================
# VALYUTA KONVERTATSIYASI
# ===========================================================

exchange-menu =
    🔁 <b>Valyuta konvertatsiyasi</b>

    Sizning balans: <b>{ $diamonds }</b> 💎  <b>{ $dollars }</b> 💵
    Kurs: 1 💎 = { $rate } 💵

    Yo'nalishni tanlang:

exchange-success = ✅ Sizga { $got } { $currency } qo'shildi!

exchange-disabled = 🚫 Konvertatsiya hozir o'chirilgan.

exchange-insufficient-diamonds = 💎 Konvertatsiya uchun olmos yetarli emas

exchange-insufficient-dollars = 💵 Konvertatsiya uchun dollar yetarli emas

exchange-below-minimum = ❌ Minimal miqdordan kam


# ===========================================================
# GIVEAWAY
# ===========================================================

give-amount-required = ❌ /give 50 kabi miqdor yozing

give-amount-too-small = ❌ Miqdor 1 dan kam bo'lmasligi kerak

give-cannot-self = ❌ O'zingizga hadya qilolmaysiz

give-insufficient = ❌ Olmos yetarli emas (sizda 💎 { $have }, kerak 💎 { $need })

give-target-not-found = ❌ Foydalanuvchi topilmadi

give-direct-success = { $sender } 💎 { $amount } { $receiver }-ga xayriya qildi!

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

vote-broadcast = <b>{ $voter }</b> -- <b>{ $target }</b> ga ovoz berdi

vote-broadcast-abstain = 🚫 <b>{ $voter }</b> hech kimni tanlamaslikka qaror qildi..


# ===========================================================
# OSISH TASDIQLASH
# ===========================================================

hanging-confirm-prompt =
    ⚖️ { $target } ni osishni tasdiqlaymi?
    👍 = ha, 👎 = yo'q

hanging-yes = 👍 Ha, osmoq kerak

hanging-no = 👎 Yo'q

hanging-confirm-expired = ❌ Tasdiqlash vaqti tugagan

hanging-tally =
    <b>Ovoz berish natijalari:</b>
    { $yes } 👍 | { $no } 👎

hanging-result-with-role = <b>{ $name }</b> O'tkazilgan kunduzgi yig'ilishda osildi! U edi { $role_emoji } <b>{ $role }</b>..

hanging-result = <b>{ $name }</b> O'tkazilgan kunduzgi yig'ilishda osildi!

hanging-cancelled =
    <b>Ovoz berish yakunlandi:</b>
    Aholi kelisha olmadi... Kelisha olmaslik oqibatida hech kim osilmadi...

hanging-combined =
    <b>Ovoz berish natijalari:</b>
    { $yes } 👍 | { $no } 👎

    { $mention } O'tkazilgan kunduzgi yig'ilishda osildi!

hanging-combined-with-role =
    <b>Ovoz berish natijalari:</b>
    { $yes } 👍 | { $no } 👎

    { $mention } O'tkazilgan kunduzgi yig'ilishda osildi!
    U { $role_emoji } <b>{ $role }</b> edi..

hanging-confirm-cannot-self = 😅 O'zingizning osilishingizga ovoz bera olmaysiz!


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

kamikaze-took-victim =
    🧞 Afsungar { $victim } ni o'zi bilan birga jahannasiga olib ketdi..
    U { $victim_role_emoji } { $victim_role } edi.

kamikaze-took-confirm = Tanlandi

kamikaze-took-confirm-text = 🧞 Siz { $target } ni o'zingiz bilan olib ketdingiz.


# ===========================================================
# BO'RI TRANSFORMATSIYA XABARLARI (guruhga)
# ===========================================================

transform-werewolf-to-mafia = 🐺 Bo'ri 🤵🏼 Mafiya ga aylandi!

transform-werewolf-to-sergeant = 🐺 Bo'ri 👮🏻‍♂ Serjant ga aylandi!


# ===========================================================
# SOTQIN OSHKOR XABARI (guruhga)
# ===========================================================

snitch-reveal-broadcast = 📢 Sotqin xabari: { $target } ning roli — { $role } ekan!


# ===========================================================
# YORDAM VA QOIDALAR
# ===========================================================

help-text =
    ❓ <b>Yordam</b>

    <b>Asosiy buyruqlar (private chat):</b>
    /start — Bosh menyu
    /profile — Profil + inventar + statistika
    /exchange — 💎 olmos ↔ 💵 dollar

    <b>Guruh buyruqlari (admin sifatida qo'shgan guruhda):</b>
    /game — Yangi o'yin boshlash
    /join — O'yinga qo'shilish
    /leave — O'yindan chiqish
    /vote &lt;raqam&gt; — Ovoz berish
    /stats — Guruh statistikasi

    <b>Premium imkoniyatlari:</b>
    • 👑 Premium maqom: /buy_premium
    • 🎁 Olmos sovg'a: <code>/give &lt;miqdor&gt;</code> (reply qilib)

    <b>Yordam kerakmi?</b>
    📢 Kanal: @MafiaAzBot_news

rules-text =
    📖 <b>Mafia o'yin qoidalari</b>

    🎯 <b>Maqsad:</b> Tomoningizga g'olib bo'lish.

    <b>3 ta asosiy tomon:</b>
    🤵🏼 <b>Mafiya</b> — Tinch aholini yo'q qilish
    👨‍👨‍👧‍👦 <b>Tinch aholilar</b> — Mafiya va Singleton'larni topish
    🎯 <b>Singleton</b> — har biri o'ziga xos g'alaba sharti

    <b>🔄 O'yin sikli:</b>
    🌃 <b>Tun</b> (60s) — rollar maxsus harakatlar qiladi
    ☀️ <b>Kun</b> (45s) — natijalar muhokama qilinadi
    🗳 <b>Ovoz berish</b> (25s) — kimni osishni tanlash
    👍/👎 (15s) — osishni tasdiqlash

    ━━━━━━━━━━━━━━━━━━━━

    👨‍👨‍👧‍👦 <b>Tinch aholilar (10):</b>
    👨🏼 <b>Tinch aholi</b> — oddiy fuqaro
    🕵🏻‍♂ <b>Komissar Kattani</b> — har tunda kim ekanligini tekshiradi
    👮🏻‍♂ <b>Serjant</b> — Komissar yordamchisi
    🎖 <b>Janob</b> — ovozi 2 baravar
    👨🏻‍⚕ <b>Doktor</b> — har tunda 1 kishini davolaydi
    💃 <b>Kezuvchi</b> — bir kishining tuni uxlaydi
    🧙‍♂ <b>Daydi</b> — qotilni ko'ra oladi
    🤞🏼 <b>Omadli</b> — 50% omon qolish
    🤦🏼 <b>Suidsid</b> — osilsa yutadi
    💣 <b>Afsungar</b> — osilganda kimnidir o'zi bilan ketadi

    🤵🏼 <b>Mafiya (5):</b>
    🤵🏻 <b>Don</b> — har tunda 1 kishini o'ldiradi
    🤵🏼 <b>Mafiya</b> — Donni qo'llab-quvvatlaydi
    👨‍💼 <b>Advokat</b> — Komissardan va osilishdan himoyalaydi
    👩🏼‍💻 <b>Jurnalist</b> — Doktor/Daydi/Kezuvchini topa oladi
    🥷 <b>Ninza</b> — barcha himoyalarni teshib o'tadi

    🎯 <b>Singletonlar (6):</b>
    🔪 <b>Qotil</b> — yakka g'olib (oxirgi tirik bo'lsa)
    🐺 <b>Bo'ri</b> — hujumiga qarab boshqa rolga aylanadi
    🧙 <b>Sehrgar</b> — oxirigacha tirik qolsa g'olib
    🧟 <b>G'azabkor</b> — 3+ kishini o'ldirsa g'olib
    🤹 <b>Aferist</b> — tirik qolsa g'olib (kun ovozini o'g'irlaydi)
    🤓 <b>Sotqin</b> — Komissar bilan bir odamni tanlasa rolni oshkor qiladi

    🛡 <b>Himoyalar (do'kondan sotib olinadi):</b>
    🛡 Himoya — 1 marta o'ldirishdan saqlaydi
    ⛑ Qotildan himoya — faqat Qotil zarbasidan
    ⚖️ Ovoz himoyasi — osilishdan saqlaydi
    🔫 Miltiq — barcha himoyalarni teshib o'tadi
    🎭 Maska — Daydi va Sotqin ko'rmaydi
    📁 Soxta hujjat — Komissarga "Tinch aholi" deb ko'rinadi

language-picker-prompt = 🌐 Tilni tanlang:

language-switched = ✅ Til o'zgartirildi

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


# === Mafia chat ===

mafia-chat-opened =
    🤵🏻 Mafiya tunini ochildi.
    Ayrim a'zolaringiz bilan suhbatlasha olasiz:
    { $members }

    💬 Bu yerga yozgan har qanday matningiz boshqa mafiyalarga yetkaziladi.


# === Atmosphere media ===

atmosphere-admin-only = 🚫 Bu komanda faqat guruh administratorlari uchun.

atmosphere-help =
    📺 <b>Atmosfera media</b>

    GIF/video xabarga reply qilib yuboring:
    <code>/setatmosphere &lt;slot&gt;</code>

    Mavjud slotlar: { $slots }

atmosphere-invalid-slot = ❌ Noto'g'ri slot. Mavjud: { $slots }

atmosphere-reply-required = ❌ Animatsiya yoki videoga reply qiling.

atmosphere-no-media = ❌ Reply qilingan xabarda media topilmadi.

atmosphere-no-group = ❌ Guruh sozlamalari topilmadi.

atmosphere-saved = ✅ <b>{ $slot }</b> sloti uchun media saqlandi.

atmosphere-clear-help = 🧹 <code>/clearatmosphere &lt;slot&gt;</code> — slotni tozalash. Mavjud: { $slots }

atmosphere-cleared = ✅ <b>{ $slot }</b> tozalandi.


# ===========================================================
# YANGI KALITLAR (adds)
# ===========================================================

leave-broadcast-with-role =
    { $mention } bu shaharning yovuzliklariga chiday olmadi va o'z joniga qasd qildi.
    U { $role_emoji } { $role_name } edi.

crook-stole-vote-dm = 🎭 Aferist sizni aldab, kunlik ovoz berishda sizning ovoz berish huquqingizni olib qo'ydi.

arsonist-self-burn = <b>{ $name }</b> (🧟 G'azabkor) o'zimni o'ldirdim!

game-end-header = <b>O'yin tugadi!</b>

game-end-winners-section = <b>G'oliblar:</b>

game-end-losers-section = <b>Qolgan o'yinchilar:</b>

game-end-duration = <i>O'yin: { $minutes } minut davom etdi</i>


# === Group settings menu ===

# --- Section A: /settings buyrug'i javoblari ---

settings-admin-only = 🚫 Bu buyruq faqat guruh adminlari uchun.

settings-sent-to-dm = ✉️ Sozlamalar shaxsiy chatga yuborildi.

settings-cannot-dm = ❌ Sizga shaxsiy xabar yubora olmadim. Avval botga /start yuboring.

settings-dm-failed = ❌ Sozlamalarni yuborishda xato. Keyinroq qayta urinib ko'ring.

settings-group-not-configured = ❌ Bu guruh hali to'liq sozlanmagan.

# --- Section B: Settings home ---

settings-home =
    🛠 <b>{ $group_title }</b> sozlamalari

    WebApp orqali to'liq menyu yoki bot ichida tezkor sozlash:

btn-settings-webapp = 🌐 To'liq sozlamalar

btn-settings-history = 📊 O'yinlar tarixi

btn-settings-roles = 🎭 Rollar

btn-settings-timings = ⏱ Vaqt sozlamalari

btn-settings-items = 🛡 Himoyalar

btn-settings-silence = 🔇 Jimlik

btn-settings-gameplay = 🎮 O'yin variantlari

btn-settings-lang = 🌐 Til

btn-settings-atmosphere = 📺 Atmosfera media

# --- Section C: Roles sub-menu ---

settings-roles-prompt =
    🎭 <b>Rollarni boshqarish</b>

    O'yinda ishtirok etadigan rollarni tanlang:

settings-team-civilians = 👨‍👨‍👧‍👦 Tinch aholilar

settings-team-mafia = 🤵🏼 Mafiya

settings-team-singletons = 🎯 Singletonlar

# --- Section D: Timings sub-menu ---

settings-timings-prompt = ⏱ <b>Faza vaqtlari (sekundlarda)</b>

timing-registration = Ro'yxat

timing-night = Tun

timing-day = Kun

timing-mafia_vote = Mafia ovozi

timing-hanging_vote = Osish ovozi

timing-hanging_confirm = Tasdiq

timing-last_words = So'nggi so'z

timing-afsungar_carry = Afsungar tanlovi

# --- Section E: Items sub-menu ---

settings-items-prompt =
    🛡 <b>Himoyalarni ruxsat berish</b>

    Qaysi himoyalar do'konda sotiladi va o'yinda ishlatiladi:

# --- Section F: Silence sub-menu ---

settings-silence-prompt =
    🔇 <b>Jimlik qoidalari</b>

    Kim qachon yozish mumkinligini boshqaring:

silence-dead_players = O'lganlar jim

silence-sleeping_players = Uxlovchilar jim

silence-non_players = Tashqari odamlar jim

silence-night_chat = Tunda yozish yo'q

# --- Section G: Gameplay sub-menu ---

settings-gameplay-status =
    🎮 <b>O'yin variantlari</b>

    Mafia nisbati: <b>{ $ratio }</b>
    O'yinchilar: <b>{ $min_players }-{ $max_players }</b>

    Kun ovozini o'tkazib yuborish: { $skip_day_vote }
    Tun harakatini o'tkazib yuborish: { $skip_night_action }

gameplay-ratio-low = Past (1/4)

gameplay-ratio-high = Yuqori (1/3)

gameplay-skip-day = Kun ovozini o'tkazib yuborish

gameplay-skip-night = Tun harakatini o'tkazib yuborish

# --- Section G.2: Display sub-menu ---

btn-settings-display = 🖼 Ko'rinish

settings-display-prompt =
    🖼 <b>Ko'rinish sozlamalari</b>

    Bot xabarlarida ko'rsatish qoidalari:

display-show_role_emojis = Rol emojilari ko'rinsin
display-group_roles_in_list = Ro'yxatda rollar tartibi bilan
display-anonymous_voting = Anonim ovoz berish
display-auto_pin_registration = Ro'yxatni avto-pin qilish
display-show_role_on_death = O'limdan keyin rol oshkor qilinsin

# --- Section G.3: Permissions sub-menu ---

btn-settings-permissions = 🔐 Ruxsatlar

settings-permissions-prompt =
    🔐 <b>Ruxsatlar</b>

    Kim qaysi buyruqni ishlatishi mumkin:

perm-who_can_register = Ro'yxatga yozilish
perm-who_can_start = O'yinni boshlash
perm-who_can_extend = Vaqtni uzaytirish
perm-who_can_stop = O'yinni to'xtatish
perm-allow_leave = O'yindan chiqib ketishga ruxsat

perm-target-all = Hamma
perm-target-admins = Faqat adminlar
perm-target-registrar = Birinchi yozilgan
perm-target-creator = Faqat creator

# --- Section G.4: AFK sub-menu ---

btn-settings-afk = 💤 AFK

settings-afk-prompt =
    💤 <b>AFK chegaralari</b>

    Faolsiz o'yinchilar uchun jazo qoidalari:

afk-skip_phases_before_kick = O'tkazilgan fazalardan keyin chiqarish
afk-xp_penalty_on_kick = Chiqarilgan o'yinchi XP jarima
afk-elo_penalty_on_leave = Tashlab ketgan ELO jarima
afk-consecutive_leaves_to_ban = Ban uchun ketma-ket tashlash
afk-ban_duration_hours = Ban davomiyligi (soat)

# --- Section H: Language sub-menu ---

settings-lang-prompt =
    🌐 <b>Guruh tili</b>

    Bot xabarlari shu tilda ko'rsatiladi:

# --- Section I: Atmosphere info ---

settings-atmosphere-info =
    📺 <b>Atmosfera media</b>

    🟢 = sozlangan, ⚪ = bo'sh

    O'rnatish uchun guruhda GIF/video xabariga reply qilib quyidagi buyruqni yuboring:
    <code>/setatmosphere &lt;slot&gt;</code>

    Slotlar: <code>night</code>, <code>day</code>, <code>voting</code>,
    <code>win_civilian</code>, <code>win_mafia</code>, <code>win_singleton</code>


# === Game start announcement + role descriptions ===

game-started-announcement =
    🎭 <b>O'yin boshlandi!</b>

    Quyidagi tugmani bosing va o'z rolingizni ko'ring:

btn-show-my-role = 🎭 Sizning rolingiz

show-role-not-in-game = 🚫 Siz bu o'yinda emassiz

show-role-no-game = 🚫 Hozir o'yin yo'q

show-role-alert = 🎭 Sizning rolingiz: { $role }\n\n{ $description }

dm-your-role =
    🎭 <b>Siz - { $role } siz!</b>

    { $description }

role-desc-citizen = Vazifangiz mafiani topish va kunduzgi ovozda osish.
role-desc-detective = Har tunda 1 o'yinchini tekshirib, uning aslida kim ekanligini bilasiz.
role-desc-sergeant = Komissarning yordamchisi — uning xabarlarini ko'rasiz va himoya qilasiz.
role-desc-mayor = Sizning ovozingiz ikki barobar hisoblanadi.
role-desc-doctor = Har tunda 1 o'yinchini davolab, uni o'limdan saqlaysiz.
role-desc-hooker = Har tunda 1 o'yinchini uxlatib, uning tundagi harakatini bekor qilasiz.
role-desc-hobo = Tunda 1 o'yinchining uyiga borasiz va uning mehmonlarini ko'rasiz.
role-desc-lucky = 50% omadingiz bor — o'limdan tasodifan qutulishingiz mumkin.
role-desc-suicide = Sizni kunduzgi ovozda osishsa, siz g'olib bo'lasiz!
role-desc-kamikaze = Osilsangiz, o'zingiz bilan birga 1 odamni jahannamga olib ketasiz.
role-desc-don = Mafiya boshlig'i — har tunda 1 o'yinchini o'ldirasiz.
role-desc-mafia = Mafiya guruhi a'zosi. Donni qo'llab-quvvatlaysiz.
role-desc-lawyer = Tunda 1 mafiyani Komissardan va kunduzgi osishdan himoyalaysiz.
role-desc-journalist = Komissar yordamchilarini topa olasiz, lekin Komissarning o'zini emas.
role-desc-killer = Mafiyaning eng kuchli o'ldiruvchisi — barcha himoyalarni teshib o'tasiz.
role-desc-maniac = Yakka g'olib — oxirgi tirik qolish uchun hammani o'ldirasiz.
role-desc-werewolf = Hujum qilgan o'yinchining roliga aylanasiz.
role-desc-mage = Oxirgacha tirik qolsangiz, yakka g'olib bo'lasiz.
role-desc-arsonist = 3+ o'yinchini o'ldirsangiz, yakka g'olib bo'lasiz.
role-desc-crook = Tirik qolsangiz, yakka g'olib bo'lasiz. Kunduzi boshqa o'yinchi nomidan ovoz bera olasiz.
role-desc-snitch = Komissar bilan bir odamni tanlasangiz, rolini guruhga oshkor qilasiz.

# ===========================================================
# DM-based voting (Wave 6 — voting moved out of group chat)
# ===========================================================

voting-group-prompt-short =
    ⚖️ Aybdorlarni aniqlash va jazolash vaqti keldi.
    Ovoz berish uchun { $seconds } sekund.

voting-go-button = 🗳 Ovoz berish

voting-dm-prompt =
    ⚖️ <b>Aybdorlarni topish va jazolash vaqti keldi!</b>

    Kimni osish kerak deb hisoblaysiz?

vote-recorded-dm-confirm = ✅ Sizning ovozingiz: <b>{ $target }</b>

vote-skipped-confirm = ✅ Siz "Hech kim" tanladingiz.

# Comedic rumor-style alerts for invalid voters in HANGING_CONFIRM
vote-dead-alert = 💀 Sen o'lgansan, ovoz berolmaysan! Ruhing ham jim turibdi-da.
vote-not-in-game-alert = 😴 Siz bu o'yinda emassiz. Keyingi o'yinda sizni ham chaqiramiz!
vote-already-voted-alert = ✋ Siz allaqachon ovoz bergansiz!

# AFK comedic last-words (rumor format) — replaces afk-kicked
afk-last-words =
    Aholidan kimdir { $role } { $mention } o'limidan oldin:
    "Men o'yin paytida boshqa uxlamayma-a-a-a-a-a-an!" deb qichqirganini eshitgan.

# Per-player game-end DM
game-end-dm-win =
    🏆 <b>Tabriklaymiz, siz g'olibsiz!</b>

    🎭 Rolingiz: { $role }
    ⭐ XP: +{ $xp }
    📊 ELO: { $elo_delta }
    💵 Mukofot: { $dollars }$

game-end-dm-loss =
    💀 <b>Bu safar omadingiz chopmadi.</b>

    🎭 Rolingiz: { $role }
    ⭐ XP: +{ $xp }
    📊 ELO: { $elo_delta }
    💵 Pul: { $dollars }$
