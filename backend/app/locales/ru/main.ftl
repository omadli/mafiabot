# Mafia Baku Black — @MafGameUzBot
# Locale: ru (Русский язык)
# Project Fluent синтаксис: https://projectfluent.org/


# ===========================================================
# ОНБОРДИНГ (бот добавлен в группу)
# ===========================================================

onboarding-pick-language =
    👋 Привет! Я Mafia бот.
    Сначала выберите язык группы:

onboarding-only-admins-can-pick = ⚠️ Только администраторы группы могут выбрать язык.

onboarding-grant-admin-perms =
    ✅ Язык установлен.
    Теперь назначьте меня администратором группы. Необходимые права:
      ✓ Удаление сообщений (Delete messages)
      ✓ Ограничение участников (Restrict members)
      ✓ Закрепление сообщений (Pin messages)
    Эти права нужны для управления группой во время игры.
    Назначьте @{ $bot_username } администратором и нажмите кнопку ниже.

onboarding-completed =
    🎉 Отлично! Теперь можете начать игру командой /game.

onboarding-success-toast = ✅ Готово! Бот настроен.

onboarding-perms-missing =
    ❌ Не хватает следующих прав: { $perms }
    Пожалуйста, предоставьте их и проверьте снова.

btn-check-perms = 🔄 Проверить

perm-delete-messages = Удаление сообщений
perm-restrict-members = Ограничение участников
perm-pin-messages = Закрепление сообщений


# ===========================================================
# /start (личный чат)
# ===========================================================

start-welcome =
    👋 Привет, <b>{ $username }</b>!

    <e:item-mask> Добро пожаловать в <b>Mafia Baku Black</b>!

    Здесь вы:
    • 🎮 Играете в мафию в Telegram-группах
    • <e:currency-diamond> Зарабатываете алмазы, <e:currency-dollar> доллары, ⭐ XP
    • <e:status-trophy> Получаете достижения и повышаете ELO
    • 👑 Можете оформить премиум

    Выберите действие:

btn-profile = 👤 Профиль
btn-inventory = 🎒 Инвентарь
btn-buy-diamonds = <e:currency-diamond> Купить алмазы
btn-help = ❓ Помощь

btn-add-to-group = ➕ Добавить в группу

btn-language = 🌐 Язык

btn-rules = 📖 Правила игры


# ===========================================================
# DEEPLINK ПРИСОЕДИНЕНИЕ
# ===========================================================

deeplink-invalid = ❌ Неверная ссылка. Попробуйте ещё раз через группу.

admin-login-deeplink-todo = 🔐 Вход в панель суперадмина — скоро (Этап 3).

join-banned =
    🚫 Вы временно заблокированы.
    Бан истекает: { $until }
    Причина: { $reason }

join-already-in-this-game = 😏 Не торопись — ты уже в игре. Слышишь? В игре.

join-already-in-other-group =
    ❌ Вы уже участвуете в игре в другой группе: { $group_title }.
    Одновременно можно участвовать только в одной игре.

join-group-not-found = ❌ Группа не найдена или бот не активен в этой группе.

join-no-active-registration =
    ⏱ Вы опоздали! Регистрация уже завершена.
    Ждите следующей игры.

join-success =
    ✅ Вы успешно присоединились к игре :)

btn-back-to-group = 🔙 Вернуться в группу


# ===========================================================
# ГРУППОВЫЕ КОМАНДЫ
# ===========================================================

game-onboarding-required =
    ⚠️ Сначала настройте бота: назначьте меня администратором и выдайте необходимые права.

game-todo-mvp = 🎮 /game будет доступна в ближайшее время (Этап 1).

leave-not-in-game = ❌ Вы сейчас не участвуете ни в одной игре.

leave-todo = 🚪 /leave будет доступна в ближайшее время.

stop-todo = 🛑 /stop будет доступна в ближайшее время.


# ===========================================================
# НАЗВАНИЯ РОЛЕЙ
# ===========================================================

role-citizen = 👨🏼 Мирный житель
role-detective = 🕵🏻‍♂ Комиссар Катани
role-sergeant = 👮🏻‍♂ Сержант
role-mayor = 🎖 Мэр
role-doctor = 👨🏻‍⚕ Доктор
role-hooker = 💃 Путана
role-hobo = 🧙‍♂ Бомж
role-lucky = 🤞🏼 Везунчик
role-suicide = 🤦🏼 Суицид
role-kamikaze = 💣 Камикадзе
role-don = 🤵🏻 Дон
role-mafia = 🤵🏼 Мафия
role-lawyer = 👨‍💼 Адвокат
role-journalist = 👩🏼‍💻 Журналист
role-killer = 🥷 Ниндзя
role-maniac = 🔪 Маньяк
role-werewolf = 🐺 Оборотень
role-mage = 🧙 Колдун
role-arsonist = 🧟 Берсерк
role-crook = 🤹 Аферист
role-snitch = 🤓 Предатель


# ===========================================================
# НОЧНЫЕ АТМОСФЕРНЫЕ СООБЩЕНИЯ (в группу после действия роли)
# ===========================================================

night-action-msg-don = 🤵🏻 Дон выбрал свою следующую жертву...

night-action-msg-detective-check = 🕵🏻‍♂ Комиссар Каттани отправился искать злодеев...

night-action-msg-detective-shoot = 🕵🏻‍♂ Комиссар Каттани зарядил пистолет...

night-action-msg-doctor = 👨🏻‍⚕ Доктор отправился на вечерний обход...

night-action-msg-hooker = 💃 У Путаны, кажется, появился ночной гость...

night-action-msg-hobo = 🧙‍♂ Бомж вышел на улицу в поисках стеклотары...


# ===========================================================
# РЕЗУЛЬТАТЫ НОЧИ (в начале дня, в группу)
# ===========================================================

night-result-killed-single =
    🌅 Этой ночью { $role_emoji_name } { $mention } был жестоко убит.
    По слухам, к нему приходил { $killer_role_emoji_name }...

night-result-no-deaths = 🌅 Невероятно, но этой ночью никто не погиб...

night-result-shield-used = <e:status-spark> Кто-то воспользовался защитой!

feedback-shield-used =
    🛡 Этой ночью кто-то пытался вас убить.
    Ваша защита спасла вас.

feedback-killer-shield-used =
    ⛑ Маньяк пытался вас убить.
    Ваша защита от маньяка спасла вас.

feedback-fake-document-used =
    📁 Кто-то заинтересовался вашей ролью.
    Вы предъявили поддельные документы и выглядели как «мирный житель».

feedback-vote-shield-used =
    ⚖️ Сегодня вас пытались повесить.
    Ваша защита от голосования спасла вас.

hanging-vote-shield-used = ⚖️ { $mention } воспользовался защитой от голосования.


# ===========================================================
# ПОСЛЕДНЕЕ СЛОВО
# ===========================================================

last-words-prompt-hanged =
    Вас безжалостно повесили :(
    Вы можете сказать последнее слово:

last-words-prompt-killed-night =
    Вас безжалостно убили :(
    Вы можете сказать последнее слово:

last-words-broadcast =
    Кто-то услышал, как { $role_emoji } { $role_name } { $mention } перед смертью кричал:
    <i>{ $message }</i>

last-words-sent-confirm = ✅ Ваше сообщение отправлено в группу!


# ===========================================================
# FLOOD CONTROL — насмешливые ответы на спам команд
# ===========================================================

flood-alert-1 = 😤 Эй! Угомонись, я тебе не робот-раб. Подожди пару секунд!
flood-alert-2 = 🤨 Опять жмёшь? У тебя что, кнопка команды залипла что ли?
flood-alert-3 = 🙄 Не мучай чужого бота, друг. Терпения нет или клава сломалась?
flood-alert-4 = 😡 Хватит уже! Ещё раз — выставлю из чата к чертям.


# ===========================================================
# ОШИБКИ РЕГИСТРАЦИИ / СТАРТА ИГРЫ
# ===========================================================

game-bounty-insufficient = ❌ Для /game { $required } нужно минимум { $required } алмазов. У вас: { $have }

game-already-running = ❌ В этой группе уже идёт игра!

game-cannot-start-not-waiting = ❌ Начать игру можно только в фазе регистрации.

game-not-enough-players = ❌ Нужно минимум 4 игрока. Сейчас недостаточно.

join-game-full = ❌ Игра заполнена. Максимум 30 игроков.

error-only-admins = ❌ Эта команда доступна только администраторам группы.


# ===========================================================
# СООБЩЕНИЕ РЕГИСТРАЦИИ
# ===========================================================

registration-message =
    🎲 Регистрация на игру началась!
    Нажмите кнопку ниже.

    ⏱ Время: { $timer }
    👥 Участники ({ $count }):
    { $players }

registration-message-indefinite =
    🎲 Регистрация на игру началась!
    Нажмите кнопку ниже.

    ⏳ Время продлено без ограничения — игра начнётся, когда админ нажмёт /start.
    👥 Участники ({ $count }):
    { $players }

registration-no-players-yet = — (пока никто не присоединился)

registration-bounty = <e:currency-diamond> Каждому победителю: { $per_winner } алмазов (эскроу: { $pool })

btn-join-game = 🎮 Присоединиться к игре


# ===========================================================
# СМЕНА ФАЗ
# ===========================================================

phase-night-start = 🌃 Ночь #{ $round }. Ветер разносит ночные слухи по всему городу...

phase-night-start-1 = 🌃 Ночь #{ $round }. Ветер разносит ночные слухи по всему городу...
phase-night-start-2 = 🌑 Ночь #{ $round }. Город шепчет под луной — кто-то перестал дышать...
phase-night-start-3 = 🌃 Ночь #{ $round }. Заприте двери — на улице слышны шаги...
phase-night-start-4 = 🦉 Ночь #{ $round }. Сова бдит, но и она видит не всё...
phase-night-start-5 = 🌌 Ночь #{ $round }. Звёзды свидетели — город ночью не спит, лишь притворяется.

phase-day-start = <e:scene-day> День #{ $round }. Солнце высушило кровь, пролитую ночью...

phase-day-start-1 = <e:scene-day> День #{ $round }. Солнце высушило кровь, пролитую ночью...
phase-day-start-2 = 🌅 День #{ $round }. Город проснулся — но кто-то уже не проснётся.
phase-day-start-3 = ☕ День #{ $round }. Время завтрака, но за столами стало пустее...
phase-day-start-4 = 🐓 День #{ $round }. Петух прокричал — время считать.
phase-day-start-5 = 🌤 День #{ $round }. Рассвет, но тени ночи всё ещё на углу.



# ===========================================================
# ГОЛОСОВАНИЕ
# ===========================================================

vote-not-in-voting = Сейчас не фаза голосования.

vote-not-alive = Вы мертвы, голосовать нельзя.

vote-target-required = /vote @username или ответьте на чьё-либо сообщение.

vote-target-invalid = Этот игрок не найден или уже мёртв.

vote-recorded = { $voter } → проголосовал за { $target }.

vote-recorded-anon = ✅ Ваш голос принят (анонимно)


# ===========================================================
# /leave И /stop
# ===========================================================

leave-not-allowed = В этой группе /leave запрещён.

leave-already-dead = Вы уже мертвы.

leave-broadcast = { $mention } не выдержал злодеяний этого города и покончил с собой.

unjoin-success = ✅ { $name } покинул регистрацию.

stop-no-game = Сейчас нет активной игры.

stop-not-allowed = В этой группе /stop запрещён.

stop-success = 🛑 Игра остановлена.

extend-not-in-registration = Продлить можно только в фазе регистрации.

extend-success = ⏱ Время продлено на { $seconds } секунд.

extend-indefinite = ⏳ Регистрация продлена.

game-launched-by-admin = 🚀 Игра началась!


# ===========================================================
# НОЧНЫЕ ЗАПРОСЫ (в личный чат игроку)
# ===========================================================

night-prompt-don = 🤵🏻 Дон, кого вы хотите убить этой ночью?

night-prompt-doctor = 👨🏻‍⚕ Доктор, кого вы лечите этой ночью?

night-prompt-hooker = 💃 Путана, кого вы уложите спать этой ночью?

night-prompt-detective = 🕵🏼 Комиссар, ваш выбор?

night-prompt-detective-check-only = 🕵🏼 Комиссар, в 1-ю ночь можно только проверять. Кого проверяете?

night-prompt-detective-both = 🕵🏼 Комиссар, кого проверяете или убиваете? <e:action-check> = проверить, <e:item-rifle> = убить

night-prompt-detective-prior-header = 🕵🏼 <b>Ранее проверенные игроки:</b>
night-prompt-detective-prior-line = • <b>{ $name }</b> — { $role }
night-prompt-detective-chooser = 🕵🏼 Что делаем этой ночью?
night-prompt-detective-target-list-check = <e:action-check> Кого проверим?
night-prompt-detective-target-list-kill = <e:item-rifle> Кого устраним?
btn-detective-check = <e:action-check> Проверить
btn-detective-kill = <e:item-rifle> Убить
night-no-targets = ❌ Сейчас некого выбрать.
night-no-rifle = <e:item-rifle> У вас не осталось патронов.

btn-skip = ⏭ Пропустить

night-skipped = Ход пропущен.

night-skipped-confirm = ✅ Этой ночью вы ни с кем не взаимодействовали.

night-not-in-active-game = Вы сейчас не участвуете ни в одной игре.

night-not-in-night-phase = Ночная фаза уже завершена.

night-cannot-act = Вы не можете совершить это действие.

night-target-invalid = Выбранный игрок не найден или уже мёртв.

night-action-recorded = ✅ { $target } выбран.

night-action-confirmed = ✅ Ваш выбор: <b>{ $target }</b>

mafia-team-pick-broadcast = 🤵🏼 <b>{ $role }</b> ({ $actor }) выбрал: <b>{ $target }</b>


# ===========================================================
# КОНЕЦ ИГРЫ
# ===========================================================

game-end-winner =
    <e:status-trophy> Игра завершена!

    { $team } победила!

    📋 Роли:

game-cancelled = ❌ Игра отменена.

game-cancelled-not-enough-players =
    ⏱ Игра не началась — к моменту окончания регистрации не набралось достаточно игроков (нужно минимум { $min_players }).
    Чтобы начать новую игру, используйте /game.

team-citizens = 👨🏼 Мирные жители

team-mafia = 🤵🏼 Мафия

team-singleton = 🎯 Синглтон


# ===========================================================
# РАЗНОЕ
# ===========================================================

click-to-join-private = Открывается в личном чате с ботом...


# ===========================================================
# НОЧНЫЕ АТМОСФЕРНЫЕ СООБЩЕНИЯ — НОВЫЕ РОЛИ
# ===========================================================

night-action-msg-lawyer = 👨‍💼 Адвокат ищет, кого из Мафии защитить...

night-action-msg-journalist = 👩🏼‍💻 Журналист ведёт ночное расследование...

night-action-msg-killer = 🥷 Ниндзя приступил к кровавой работе...

night-action-msg-maniac = 🔪 Маньяк притаился в кустах и достал нож из ножен...

night-action-msg-werewolf = 🐺 Оборотень завыл в ночи...

night-action-msg-arsonist = 🧟 Берсерк наметил свою следующую жертву...

night-action-msg-crook = 🤹 Аферист планирует примерить новую личину...

night-action-msg-snitch = 🤓 Стукач начал поиски, чтобы собрать информацию...

night-action-msg-kamikaze = 🧞‍♂️ Камикадзе призывает мистические силы...


# ===========================================================
# НОЧНЫЕ ЗАПРОСЫ — НОВЫЕ РОЛИ (в личный чат игроку)
# ===========================================================

night-prompt-hobo = 🧙‍♂ Бомж, в чей дом вы идёте за стеклотарой?

night-prompt-lawyer = 👨‍💼 Адвокат, кого из членов мафии вы защищаете?

night-prompt-journalist = 👩🏼‍💻 Журналист, кого проверяете?

night-prompt-killer = 🥷 Ниндзя, кого убиваете? (пробивает все защиты)

night-prompt-maniac = 🔪 Маньяк, кого убиваете?

night-prompt-mafia = 🤵🏼 Мафия, с кем договорились с Доном этой ночью?

night-prompt-arsonist = 🧟 Берсерк, кто ваша следующая жертва?

night-prompt-crook = 🤹 Аферист, от чьего имени голосуете завтра?

night-prompt-snitch = 🤓 Стукач, кого, по-вашему, проверит Комиссар?


# ===========================================================
# ФИДБЭК В ЛИЧКУ (после ночного разрешения)
# ===========================================================

feedback-detective-result = 🕵🏼 Роль { $target } — { $role }.

feedback-doctor-saved = 👨🏻‍⚕ Вы — <b>{ $target }</b> вылечили :) Его гостем был { $visitors }.

feedback-doctor-no-visitors = 👨🏻‍⚕ Доктор не смог помочь..

feedback-detective-target-notice = 🕵🏼 Этой ночью кто-то интересовался вашей ролью...

feedback-doctor-target-saved = 👨🏻‍⚕ Доктор вас вылечил.

feedback-doctor-target-visit = 👨🏻‍⚕ Доктор зашёл к вам в гости.

feedback-hooker-confirm = 💃 Вы усыпили { $target }.

feedback-hooker-target = Вот <e:action-heal> таблетка подействовала — теперь ты поспишь целый день...

mafia-kill-broadcast = 🤵🏼 Во время голосования мафии { $mention } был безжалостно убит 🩸


# ===========================================================
# AFK
# ===========================================================

afk-kicked = { $mention } уснул прямо в игре и был исключён (XP -50)


# ===========================================================
# КОМАНДЫ СТАТИСТИКИ
# ===========================================================

stats-no-games = У вас ещё нет ни одной игры. Начните с /game!

stats-period-todo = Периодическая статистика появится в ближайшее время (Этап 2)

stats-no-role-data = Данных по ролям нет

stats-role-no-data = Вы не играли за роль { $role }

stats-role-detail =
    📊 Статистика за { $role }:
    🎮 Игр: { $games }
    <e:status-trophy> Побед: { $wins }
    📈 WR: { $winrate }%
    <e:currency-diamond> ELO: { $elo }

stats-personal =
    👤 { $name }

    🎮 Игр: { $games }   <e:status-trophy> Побед: { $wins }   💔 Поражений: { $losses }
    📈 Winrate: { $winrate }%   <e:currency-diamond> ELO: { $elo }
    ⭐ XP: { $xp }   🏅 Уровень: { $level }

    🔥 Текущая серия: { $streak }   📌 Лучшая серия: { $longest }

    <e:item-mask> Любимые роли: { $top_roles }

    👨🏼 Мирные: { $citizen_games } игр, { $citizen_wins } побед
    🤵🏼 Мафия: { $mafia_games } игр, { $mafia_wins } побед
    🎯 Синглтон: { $singleton_games } игр, { $singleton_wins } побед

top-empty = Таблица лидеров пока пуста

top-group-only = Эта команда работает только в группе

top-header = <e:status-trophy> Топ 10 (по { $sort }):

global-top-header = 🌍 Глобальный топ 10:

profile-target-not-found = Пользователь не найден. Ответьте на сообщение или введите @username.

profile-no-games = { $name } ещё не сыграл ни одной игры

group-stats-no-games = В этой группе ещё не было игр

group-stats-message =
    📊 Статистика группы:
    🎮 Всего игр: { $total_games }
    ⏱ Средняя длительность: { $avg_duration } мин.
    👥 Среднее число игроков: { $avg_players }

    Винрейт сторон:
    👨🏼 Мирные: { $citizens_wr }%
    🤵🏼 Мафия: { $mafia_wr }%
    🎯 Синглтон: { $singleton_wr }%


# ===========================================================
# ПРОФИЛЬ И ИНВЕНТАРЬ
# ===========================================================

profile-info =
    ⭐ ID: <code>{ $id }</code>

    👤 { $name }

    <e:currency-dollar> Доллар: { $dollars }
    <e:currency-diamond> Алмаз: { $diamonds }
    { $premium_line }

    <e:item-shield> Защита: { $shield }
    <e:item-killer-shield> Защита от убийцы: { $killer_shield }
    <e:scene-hanging> Защита от голосования: { $vote_shield }
    <e:item-rifle> Винтовка: { $rifle }

    <e:item-mask> Маска: { $mask }
    <e:item-fake-document> Поддельный документ: { $fake_document }
    🃏 Роль на следующую игру: { $next_role }

    🎯 Побед: { $wins }
    🎲 Всего игр: { $games_total }

profile-premium-active = 👑 Премиум: активен до { $expires_at }
profile-premium-inactive = 👑 Премиум: не куплен

inventory-header = 🎒 Ваш инвентарь:

inv-toggle-on = ✅ Включено

inv-toggle-off = ⬜ Отключено

inv-no-items = 🚫 У вас нет этого предмета.

btn-toggle-on = { $emoji } - 🟢 ВКЛ

btn-toggle-off = { $emoji } - 🔴 ВЫКЛ

btn-toggle-empty = { $emoji } - 🚫 0

btn-shop = 🛒 Магазин

btn-buy-dollars = <e:currency-dollar> Купить

btn-premium-groups = 👑 Премиум-группы
btn-pick-next-role = 🃏 Выбрать следующую роль
btn-clear-next-role = 🃏 Отменить выбор
pick-role-prompt = 🃏 <b>Какую роль вы хотите в следующей игре?</b>
pick-role-confirmed = ✅ В следующей игре вы сыграете за { $role }!
pick-role-already-chosen = ℹ️ Вы уже выбрали роль.
pick-role-cleared = ❎ Выбор роли отменён.

btn-news = 📢 Новости

btn-back = 🔙 Назад

btn-exchange = 🔁 Обмен

btn-close = ❎ Закрыть


# ===========================================================
# МАГАЗИН
# ===========================================================

shop-welcome =
    🛒 Добро пожаловать в магазин Mafia!
    Что желаете купить?

shop-welcome-balance =
    🛒 <b>Магазин</b>

    Ваш баланс: <b>{ $diamonds }</b> <e:currency-diamond>  <b>{ $dollars }</b> <e:currency-dollar>

shop-diamonds-header = <e:currency-diamond> Пакеты алмазов:

shop-no-items = 🚫 В этой валюте ничего нет

shop-items-header =
    <e:item-shield> <b>Предметы</b>

    Баланс: <b>{ $diamonds }</b> <e:currency-diamond>  <b>{ $dollars }</b> <e:currency-dollar>

    Оплата в указанной валюте.

shop-premium-info =
    👑 <b>Премиум-пользователь</b>
    • Двойная защита
    • Защита от Путаны
    • Другие привилегии

    Ваш статус: <b>не куплен</b>

shop-premium-info-active =
    👑 <b>Премиум-пользователь</b>
    • Двойная защита
    • Защита от Путаны
    • Другие привилегии

    Премиум уже активен — действует до <b>{ $expires_at }</b>.
    Продлите его одной из кнопок ниже.

btn-buy-items = 🎒 Оружие/защита

btn-buy-premium = 👑 Премиум

btn-buy-premium-30d = ⭐ 1 месяц премиум — { $price } <e:currency-diamond>

btn-buy-premium-365d = ⭐ 1 год премиум — { $price } <e:currency-diamond>

btn-extend-premium-30d = ⏳ Продлить на 30 дней — { $price } <e:currency-diamond>

btn-extend-premium-365d = ⏳ Продлить на 1 год — { $price } <e:currency-diamond>

shop-special-pick-prompt =
    🃏 <b>Особая роль</b>

    Выберите роль ниже — цена: <b>{ $price }</b>

    Выбранная роль будет назначена вам в следующей игре.

shop-special-purchased = ✅ { $role } куплена! ({ $cost } { $currency }). В следующей игре вы сыграете в этой роли.

premium-groups-empty =
    🚫 Пока что нет премиум-групп.

    В премиум-группах игроки получают 2x больше наград.

premium-groups-header =
    👑 <b>Премиум-группы — TOP</b>

    Игроки этих групп получают { $multiplier }x доллары и алмазы!

premium-groups-row = { $rank }. <b>{ $title }</b> — { $games } игр

buy-insufficient = ❌ Недостаточно алмазов

buy-success = ✅ Куплено!

buy-success-detailed = ✅ { $item } куплен! ({ $cost } { $currency })

buy-insufficient-diamonds = <e:currency-diamond> Недостаточно алмазов

buy-insufficient-dollars = <e:currency-dollar> Недостаточно долларов

premium-activated = 👑 Премиум активирован: +{ $days } дней. Действует до { $expires_at }.

premium-extended = ⏳ Премиум продлён: +{ $days } дней. Теперь действует до { $expires_at }.

payment-success = ✅ Оплата прошла успешно! +<e:currency-diamond> { $diamonds }

payment-failed = ❌ Ошибка оплаты


# ===========================================================
# КОНВЕРТАЦИЯ ВАЛЮТЫ
# ===========================================================

exchange-menu =
    🔁 <b>Конвертация валюты</b>

    Ваш баланс: <b>{ $diamonds }</b> <e:currency-diamond>  <b>{ $dollars }</b> <e:currency-dollar>
    Курс: 1 <e:currency-diamond> = { $rate } <e:currency-dollar>

    Выберите направление:

exchange-success = ✅ Вам зачислено { $got } { $currency }!

exchange-disabled = 🚫 Конвертация сейчас отключена.

exchange-insufficient-diamonds = <e:currency-diamond> Недостаточно алмазов для конвертации

exchange-insufficient-dollars = <e:currency-dollar> Недостаточно долларов для конвертации

exchange-below-minimum = ❌ Ниже минимальной суммы


# ===========================================================
# ГИВЭВЕЙ
# ===========================================================

give-amount-required = ❌ Укажите сумму, например /give 50

give-amount-too-small = ❌ Сумма не может быть меньше 1

give-cannot-self = ❌ Нельзя подарить алмазы самому себе

give-insufficient = ❌ Недостаточно алмазов (у вас <e:currency-diamond> { $have }, нужно <e:currency-diamond> { $need })

give-target-not-found = ❌ Пользователь не найден

give-direct-success = { $sender } <e:currency-diamond> { $amount } передал в дар { $receiver }!

give-creating = <e:currency-diamond> Создаётся гивэвей...

give-group-message =
    🎁 { $sender } запустил гивэвей на { $amount } алмазов!
    Кто нажмёт первым — получит больше.

give-no-clicks = 🎁 Гивэвей завершён — никто не нажал

give-results-header = 🎁 Итоги гивэвея:

btn-claim-diamond = <e:currency-diamond> Забрать алмазы

giveaway-clicked-ok = ✅ Нажато!

giveaway-already-clicked-or-finished = ❌ Вы уже нажимали или гивэвей завершён


# ===========================================================
# ГОЛОСОВАНИЕ UI (с инлайн-кнопками)
# ===========================================================

voting-prompt = <e:scene-voting> Время голосования! Живых игроков: { $count }. Проголосуйте кнопкой ниже:

vote-skip-button = ❌ Никого

vote-cannot-self = ❌ Вы не можете голосовать за себя

vote-recorded-toast = ✅ Ваш голос: { $target }

vote-skipped-toast = ✅ Вы выбрали «Никого»

vote-broadcast = <b>{ $voter }</b> -- проголосовал(а) за <b>{ $target }</b>

vote-broadcast-abstain = 🚫 <b>{ $voter }</b> решил(а) никого не выбирать..


# ===========================================================
# ПОДТВЕРЖДЕНИЕ КАЗНИ
# ===========================================================

hanging-confirm-prompt =
    <e:scene-hanging> Подтвердить казнь { $target }?
    👍 = да, 👎 = нет

hanging-yes = 👍 Да, повесить

hanging-no = 👎 Нет

hanging-confirm-expired = ❌ Время подтверждения истекло

hanging-tally =
    <b>Результаты голосования:</b>
    { $yes } 👍 | { $no } 👎

hanging-result-with-role = <b>{ $name }</b> повешен(а) на дневном собрании! Это был { $role_emoji } <b>{ $role }</b>..

hanging-result = <b>{ $name }</b> повешен(а) на дневном собрании!

hanging-cancelled =
    <b>Голосование завершено:</b>
    Народ не пришёл к согласию... Из-за разногласий никто не был повешен...

hanging-combined =
    <b>Результаты голосования:</b>
    { $yes } 👍 | { $no } 👎

    { $mention } был(а) повешен(а) на дневном собрании!

hanging-combined-with-role =
    <b>Результаты голосования:</b>
    { $yes } 👍 | { $no } 👎

    { $mention } был(а) повешен(а) на дневном собрании!
    Это был { $role_emoji } <b>{ $role }</b>..

hanging-confirm-cannot-self = 😅 Нельзя голосовать за собственное повешение!


# ===========================================================
# РЕАКТИВНЫЕ СООБЩЕНИЯ КОЛДУНА (в личку игроку)
# ===========================================================

mage-attacked =
    🧙 На вас напал { $attacker_role }.
    Прощаете или убиваете?

mage-forgive = 💚 Простить

mage-kill = <e:status-death> Убить

mage-forgive-confirm = Прощён

mage-forgive-confirm-text = 💚 Вы простили. Он остался жив.

mage-kill-confirm = Убит

mage-kill-confirm-text = <e:status-death> { $target } убит (ваше проклятие)


# ===========================================================
# БЕРСЕРК (ARSONIST) СООБЩЕНИЯ
# ===========================================================

arsonist-final-night-button = 🔥 Последняя ночь!

arsonist-queued = 🧟 { $target } добавлен в список

arsonist-final-confirm = 💥 Последняя ночь активирована! Все отмеченные вами погибнут.


# ===========================================================
# КАМИКАДЗЕ СООБЩЕНИЯ
# ===========================================================

kamikaze-choose-victim = 🧞 Вас повесили! Кого хотите забрать с собой?

kamikaze-took-victim =
    🧞 Камикадзе забрал с собой в ад { $victim }..
    Это был { $victim_role_emoji } { $victim_role }.

kamikaze-took-confirm = Выбрано

kamikaze-took-confirm-text = 🧞 Вы забрали { $target } с собой.


# ===========================================================
# ТРАНСФОРМАЦИИ ОБОРОТНЯ (в группу)
# ===========================================================

transform-werewolf-to-mafia = 🐺 Оборотень превратился в 🤵🏼 Мафиози!

transform-werewolf-to-sergeant = 🐺 Оборотень превратился в 👮🏻‍♂ Сержанта!


# ===========================================================
# РАЗОБЛАЧЕНИЕ ПРЕДАТЕЛЯ (в группу)
# ===========================================================

snitch-reveal-broadcast = 📢 Сообщение Стукача: роль { $target } — { $role }!


# ===========================================================
# ПОМОЩЬ И ПРАВИЛА
# ===========================================================

help-text =
    ❓ <b>Помощь</b>

    <b>Команды в личном чате:</b>
    /start — Главное меню
    /profile — Профиль, инвентарь, магазин (= /inventory, /items)
    /exchange — <e:currency-diamond> алмазы ↔ <e:currency-dollar> доллары
    /stats — Моя статистика
    /global_top — Глобальный рейтинг
    /help — Помощь · /rules — Правила

    <b>Команды в группе (бот добавлен админом):</b>
    /game [bounty] — Новая игра (опциональный <e:currency-diamond> bounty)
    /start — Запустить набранную игру
    /leave — Выйти из игры
    /extend &lt;сек&gt; — Продлить время регистрации
    /stop — Отменить игру (админ)
    /settings — Настройки (админ)
    /give &lt;кол-во&gt; — <e:currency-diamond> подарить алмазы (reply или групповой inline)
    /stats · /top · /global_top · /profile · /group_stats — Статистика

    <b>💡 Примечание:</b>
    • Регистрация и голосование — через кнопки (отдельных команд нет)
    • 👑 Премиум и 🛒 магазин — через меню /profile

    📢 Канал новостей: @Mafiauzbot_news

rules-text =
    📖 <b>Правила Мафии</b>

    🎯 <b>Цель:</b> победить за свою команду.

    <b>3 основные стороны:</b>
    🤵🏼 <b>Мафия</b> — уничтожить мирных
    👨‍👨‍👧‍👦 <b>Мирные</b> — вычислить мафию и одиночек
    🎯 <b>Одиночки</b> — у каждого своё условие победы

    <b>🔄 Цикл игры:</b>
    🌃 <b>Ночь</b> (60с) — роли совершают действия
    <e:scene-day> <b>День</b> (45с) — обсуждение результатов
    <e:scene-voting> <b>Голосование</b> (25с) — выбор повешенного
    👍/👎 (15с) — подтверждение

    ━━━━━━━━━━━━━━━━━━━━

    👨‍👨‍👧‍👦 <b>Мирные (9):</b>
    👨🏼 <b>Мирный житель</b> — обычный горожанин
    🕵🏻‍♂ <b>Комиссар Каттани</b> — каждую ночь проверяет, кто перед ним
    👮🏻‍♂ <b>Сержант</b> — помощник Комиссара
    🎖 <b>Мэр</b> — голос считается за два
    👨🏻‍⚕ <b>Доктор</b> — лечит одного человека за ночь
    💃 <b>Путана</b> — усыпляет одного человека на ночь
    🧙‍♂ <b>Бомж</b> — видит убийцу
    🤞🏼 <b>Везунчик</b> — 50% шанс выжить
    💣 <b>Камикадзе</b> — на повешении забирает кого-то с собой

    🤵🏼 <b>Мафия (5):</b>
    🤵🏻 <b>Дон</b> — убивает по одному за ночь
    🤵🏼 <b>Мафия</b> — поддерживает Дона
    👨‍💼 <b>Адвокат</b> — защищает от Комиссара и от повешения
    👩🏼‍💻 <b>Журналист</b> — может вычислить Доктора/Бомжа/Путану
    🥷 <b>Ниндзя</b> — пробивает любые защиты

    🎯 <b>Одиночки (7):</b>
    🤦🏼 <b>Суицид</b> — побеждает только если его повесят (ночная смерть или выживание = проигрыш)
    🔪 <b>Маньяк</b> — одиночка (побеждает, оставшись в живых последним)
    🐺 <b>Оборотень</b> — превращается в другую роль в зависимости от удара
    🧙 <b>Маг</b> — побеждает, дожив до конца игры
    🧟 <b>Поджигатель</b> — побеждает, убив 3+ человек
    🤹 <b>Аферист</b> — побеждает, оставшись в живых (крадёт дневной голос)
    🤓 <b>Стукач</b> — если выбрал того же, что и Комиссар, раскрывает роль

    <e:item-shield> <b>Защиты (из магазина):</b>
    <e:item-shield> Щит · <e:item-killer-shield> От убийцы · <e:scene-hanging> От голосования · <e:item-rifle> Винтовка
    <e:item-mask> Маска · <e:item-fake-document> Поддельный документ

language-picker-prompt = 🌐 Выберите язык:

language-switched = ✅ Язык изменён

help-private =
    ❓ <b>Помощь</b>

    <b>Личный чат:</b>
    /start — главное меню
    /profile — профиль, инвентарь, магазин (= /inventory, /items)
    /exchange — <e:currency-diamond> алмазы ↔ <e:currency-dollar> доллары
    /stats — моя статистика
    /global_top — глобальный рейтинг
    /rules — правила и подробности о ролях

    <b>Игра в группе:</b>
    Добавьте бота админом в группу и начните игру командой /game.

    📢 Канал новостей: @Mafiauzbot_news

help-group =
    ❓ <b>Команды в группе:</b>

    /game [bounty] — новая игра (опциональный <e:currency-diamond> bounty)
    /start — запустить набранную игру
    /leave — выйти из игры
    /extend &lt;сек&gt; — продлить время регистрации
    /stop — отменить игру (админ)
    /settings — настройки (админ)
    /give &lt;кол-во&gt; — <e:currency-diamond> подарить алмазы (reply или групповой inline)
    /stats · /top · /global_top · /profile · /group_stats — статистика

    💡 <b>Примечание:</b> регистрация и голосование — через кнопки (отдельных команд нет).

rules-summary =
    📖 <b>Правила игры в Мафию</b>

    🏙 <b>Сцена:</b> город разделён на два лагеря — <b>мирных жителей</b> и <b>мафию</b>. Рядом с ними играют <b>синглтоны</b> со своими условиями победы.

    🎲 <b>Раунд:</b>
      1️⃣ <b>Ночь</b> — тайные действия (мафия убивает, Комиссар проверяет, Доктор лечит и т.д.).
      2️⃣ <b>День</b> — объявляются ночные события, идёт обсуждение.
      3️⃣ <b>Голосование</b> — выбираем подозреваемого.
      4️⃣ <b>Подтверждение</b> 👍/👎 — если "за" больше, его вешают.
      5️⃣ <b>Последнее слово</b> — погибший может оставить сообщение в чат.

    <e:scene-voting> <b>Голосование</b> идёт в личке — другие игроки не видят, кому вы отдали голос (если админ так настроил).

    <e:currency-diamond> <b>Предметы:</b> <e:item-shield> Щит, <e:item-killer-shield> Щит от Киллера, <e:scene-hanging> Защита голоса, <e:item-rifle> Винтовка (пробивает защиту), <e:item-mask> Маска (скрывает вашу роль), <e:item-fake-document> Поддельный документ (Комиссар видит "мирного").

    <e:status-trophy> <b>Условия победы:</b>
      • <b>Мирные</b>: уничтожить всех мафиози и синглтонов.
      • <b>Мафия</b>: сравняться или превзойти мирных по числу.
      • <b>Синглтоны</b> — у каждого свои условия (читайте по кнопке ниже).

    ⚙️ <b>Настройки:</b> админ группы через /settings меняет роли, тайминги, правила тишины и т.д.

    По кнопке ниже узнайте, как именно работает каждая роль 👇

btn-rules-roles = <e:item-mask> Подробнее о ролях
btn-rules-back = 🔙 Назад

rules-pick-team =
    <e:item-mask> <b>Стороны и наборы ролей</b>

    Какая сторона вас интересует?

rules-team-civilians = Мирные жители
rules-team-mafia = Мафия
rules-team-singletons = Синглтоны (одиночки)

rules-team-civilians-intro =
    👨‍👨‍👧‍👦 <b>Мирные жители</b>

    Главная задача: вычислить и устранить мафию и синглтонов. У каждой роли свои возможности — важно правильно распределять действия ночью.

    Выберите роль для подробностей 👇

rules-team-mafia-intro =
    🤵🏼 <b>Мафия</b>

    Главная задача: сократить число мирных и сравняться с ними. Каждую ночь мафия убивает одного игрока (выбор за Доном, иначе — за Мафией). Спец-роли — Адвокат, Журналист, Киллер — дают дополнительные способности.

    Выберите роль для подробностей 👇

rules-team-singletons-intro =
    🎯 <b>Синглтоны (одиночки)</b>

    Эти роли не в команде — у каждого свои условия победы. Может противостоять и мафии, и мирным, и другим синглтонам.

    Выберите роль для подробностей 👇

rules-role-detail =
    { $emoji } <b>{ $role }</b>

    { $description }


# === Mafia chat ===

mafia-chat-opened =
    🤵🏻 Открыта мафия-ночь.
    Вы можете общаться с участниками вашей команды:
    { $members }

    <e:scene-last-words> Любой текст здесь будет отправлен другим мафиози.


# === Atmosphere media ===

atmosphere-admin-only = 🚫 Эта команда только для администраторов группы.

atmosphere-help =
    📺 <b>Атмосферное медиа</b>

    Ответьте на GIF/видео:
    <code>/setatmosphere &lt;slot&gt;</code>

    Доступные слоты: { $slots }

atmosphere-invalid-slot = ❌ Неверный слот. Доступные: { $slots }

atmosphere-reply-required = ❌ Ответьте на анимацию или видео.

atmosphere-no-media = ❌ В ответном сообщении нет медиа.

atmosphere-no-group = ❌ Настройки группы не найдены.

atmosphere-saved = ✅ Медиа для слота <b>{ $slot }</b> сохранено.

atmosphere-clear-help = 🧹 <code>/clearatmosphere &lt;slot&gt;</code> — очистить слот. Доступные: { $slots }

atmosphere-cleared = ✅ <b>{ $slot }</b> очищен.


# ===========================================================
# НОВЫЕ КЛЮЧИ (adds)
# ===========================================================

leave-broadcast-with-role =
    { $mention } не вынес зла этого города и покончил с собой.
    Это был { $role_emoji } { $role_name }.

crook-stole-vote-dm = <e:item-mask> Крук обманул вас и забрал ваше право голоса на дневном голосовании.

arsonist-self-burn = <b>{ $name }</b> (🧟 Поджигатель) убил себя!

game-end-header = <b>Игра окончена!</b>

game-end-winners-section = <b>Победители:</b>

game-end-losers-section = <b>Остальные игроки:</b>

game-end-duration = <i>Игра длилась { $minutes } минут</i>


# === Group settings menu ===

# --- Section A: Ответы на /settings ---

settings-admin-only = 🚫 Эта команда только для администраторов группы.

settings-sent-to-dm = ✉️ Настройки отправлены в личный чат.

settings-cannot-dm = ❌ Не могу отправить вам ЛС. Сначала отправьте боту /start.

settings-dm-failed = ❌ Ошибка при отправке настроек. Попробуйте позже.

settings-group-not-configured = ❌ Эта группа ещё не настроена.

# --- Section B: Settings home ---

settings-home =
    🛠 Настройки группы <b>{ $group_title }</b>

    Полное меню в WebApp или быстрые настройки в боте:

btn-settings-webapp = 🌐 Полные настройки

btn-settings-history = 📊 История игр

btn-settings-roles = <e:item-mask> Роли

btn-settings-timings = ⏱ Время фаз

btn-settings-items = <e:item-shield> Защиты

btn-settings-silence = 🔇 Тишина

btn-settings-gameplay = 🎮 Игровые параметры

btn-settings-lang = 🌐 Язык

btn-settings-atmosphere = 📺 Атмосфера

# --- Section C: Roles sub-menu ---

settings-roles-prompt =
    <e:item-mask> <b>Управление ролями</b>

    Выберите роли, которые будут участвовать в игре:

settings-team-civilians = 👨‍👨‍👧‍👦 Мирные

settings-team-mafia = 🤵🏼 Мафия

settings-team-singletons = 🎯 Одиночки

# --- Section D: Timings sub-menu ---

settings-timings-prompt = ⏱ <b>Время фаз (в секундах)</b>

timing-registration = Регистрация

timing-night = Ночь

timing-day = День

timing-mafia_vote = Голос мафии

timing-hanging_vote = Голос казни

timing-hanging_confirm = Подтверждение

timing-last_words = Последнее слово

timing-afsungar_carry = Выбор камикадзе

# --- Section E: Items sub-menu ---

settings-items-prompt =
    <e:item-shield> <b>Разрешённые защиты</b>

    Какие защиты продаются в магазине и используются в игре:

# --- Section F: Silence sub-menu ---

settings-silence-prompt =
    🔇 <b>Правила тишины</b>

    Кто и когда может писать:

silence-dead_players = Мёртвые молчат

silence-sleeping_players = Спящие молчат

silence-non_players = Зрители молчат

silence-night_chat = Тишина ночью

# --- Section G: Gameplay sub-menu ---

settings-gameplay-status =
    🎮 <b>Игровые параметры</b>

    Доля мафии: <b>{ $ratio }</b>
    Игроки: <b>{ $min_players }-{ $max_players }</b>

    Пропуск дневного голоса: { $skip_day_vote }
    Пропуск ночного действия: { $skip_night_action }

gameplay-ratio-low = Низкая (1/4)

gameplay-ratio-high = Высокая (1/3)

gameplay-skip-day = Пропуск дневного голоса

gameplay-skip-night = Пропуск ночного действия

# --- Section G.2: Display sub-menu ---

btn-settings-display = 🖼 Отображение

settings-display-prompt =
    🖼 <b>Настройки отображения</b>

    Что показывать в сообщениях бота:

display-show_role_emojis = Эмодзи ролей
display-group_roles_in_list = Группировать роли в списке
display-anonymous_voting = Анонимное голосование
display-auto_pin_registration = Автозакрепление регистрации
display-show_role_on_death = Показывать роль после смерти

# --- Section G.3: Permissions sub-menu ---

btn-settings-permissions = 🔐 Права

settings-permissions-prompt =
    🔐 <b>Права доступа</b>

    Кто какие команды может использовать:

perm-who_can_register = Регистрация на игру
perm-who_can_start = Запуск игры
perm-who_can_extend = Продление времени
perm-who_can_stop = Остановка игры
perm-allow_leave = Разрешить покидать игру

perm-target-all = Все
perm-target-admins = Только админы
perm-target-registrar = Первый записавшийся
perm-target-creator = Только создатель
perm-target-none = Никто

# --- Section G.4: AFK sub-menu ---

btn-settings-afk = 💤 AFK

settings-afk-prompt =
    💤 <b>Пороги AFK</b>

    Правила санкций для неактивных игроков:

afk-skip_phases_before_kick = Пропущенных фаз до кика
afk-xp_penalty_on_kick = Штраф XP при кике
afk-elo_penalty_on_leave = Штраф ELO при выходе
afk-consecutive_leaves_to_ban = Подряд выходов до бана
afk-ban_duration_hours = Длительность бана (час)

# --- Section H: Language sub-menu ---

settings-lang-prompt =
    🌐 <b>Язык группы</b>

    Сообщения бота будут на этом языке:

# --- Section I: Atmosphere info ---

settings-atmosphere-info =
    📺 <b>Атмосфера медиа</b>

    🟢 = настроено, ⚪ = пусто

    Чтобы задать медиа, ответьте на GIF/видео в группе и отправьте:
    <code>/setatmosphere &lt;slot&gt;</code>

    Слоты: <code>night</code>, <code>day</code>, <code>voting</code>,
    <code>win_civilian</code>, <code>win_mafia</code>, <code>win_singleton</code>


# === Game start announcement + role descriptions ===

game-started-announcement =
    <e:item-mask> <b>Игра началась!</b>

    Нажмите кнопку и узнайте свою роль:

btn-show-my-role = <e:item-mask> Ваша роль

show-role-not-in-game = 🚫 Вы не в этой игре

show-role-no-game = 🚫 Сейчас нет активной игры

dm-stale-game-alert = ⏳ Эта игра уже завершена. Старое сообщение будет удалено.

show-role-alert =
    <e:item-mask> Ваша роль: { $role }

    { $description }

dm-your-role =
    <e:item-mask> <b>Вы - { $role }!</b>

    { $description }

role-desc-citizen =
    Особых способностей у вас нет — но <b>ваша сила в голосе</b>.
    Ночью вы молчите. Днём активно участвуйте в обсуждении: вычисляйте
    мафию по словам и голосуйте грамотно.

role-desc-detective =
    Каждую ночь проверяете одного игрока и узнаёте, <b>мафия он или мирный</b>.
    Мафия захочет вас убить — будьте осторожны. Совет: не выдавайте находки
    в чат сразу, иначе мафия вас вычислит.

role-desc-sergeant =
    Помощник Комиссара. Если Комиссар погибнет, вы наследуете его роль и начинаете
    проверять игроков сами. Видите сообщения Комиссара.

role-desc-mayor =
    Мэр. Ваш <b>голос считается за 2</b> (как на дневном голосовании, так и
    в подтверждении казни). Мафия может попытаться убить вас первым — будьте начеку.

role-desc-doctor =
    Каждую ночь лечите одного игрока, спасая его от атаки мафии.
    <b>Себя можно лечить только 1 раз</b>. Одного игрока две ночи подряд лечить нельзя.

role-desc-hooker =
    Каждую ночь усыпляете одного игрока, <b>отменяя его ночное действие</b>.
    Усыпите Дона — мафия не убивает. Усыпите Комиссара — он не проверяет.
    Себя усыпить нельзя.

role-desc-hobo =
    Ночью идёте к одному игроку. <b>Видите, кто к нему приходил</b> — так можно
    вычислить убийц мафии. Игроков в маске не узнаёте.

role-desc-lucky =
    Если мафия атакует, <b>с 50% вероятностью вы выживаете</b>. Решений не принимаете —
    воля удачи. Комиссару видитесь "мирным".

role-desc-suicide =
    Особое условие: <b>если вас повесят днём — вы победили!</b>
    Но если убьют ночью — проиграете. Задача: навлечь на себя подозрение.
    Комиссару видитесь "мирным".

role-desc-kamikaze =
    Не уходите в одиночку. <b>Если вас повесят — заберёте с собой одного игрока</b>
    (по вашему выбору). Забрали мафиози — отдельная победа.

role-desc-don =
    Глава мафии. Каждую ночь <b>выбираете жертву</b> (мафия слушается вас).
    Комиссару видитесь "мирным". Найти вас — большая удача для мирных.

role-desc-mafia =
    Член мафии. Ночью поддерживаете Дона и участвуете в убийстве выбранной им
    жертвы. Чат мафии помогает координироваться.

role-desc-lawyer =
    Адвокат мафии. Каждую ночь <b>выбираете 1 мафиози</b> и защищаете его от проверки
    Комиссара и от казни днём (не повесят). Себя тоже можно защищать.

role-desc-journalist =
    Шпион мафии. Каждую ночь проверяете 1 игрока — можете узнать, что он
    <b>Доктор, Бомж или Жрица</b>. Но Комиссара и Сержанта распознать не можете.

role-desc-killer =
    Самый сильный убийца мафии. Ваша винтовка <b>пробивает все защиты</b>
    (Доктор, 🛡 Щит, ⛑ Щит от Киллера). Ночью убиваете жертву Дона; с разрешения
    Дона можете выбрать сами.

role-desc-maniac =
    Маньяк-одиночка. Ваша победа — <b>остаться последним выжившим</b>.
    Враг и мафии, и мирным. Ночью убиваете 1 игрока. Комиссару видитесь "мирным".

role-desc-werewolf =
    Оборотень. Ночью атакуете игрока и <b>превращаетесь в его роль</b>:
    атаковали Дона — стали Мафией, атаковали Комиссара — стали Сержантом.
    Если другой Оборотень атаковал и вас — оба погибаете.

role-desc-mage =
    Маг. <b>Доживёте до конца — побеждаете в одиночку</b>. Если на вас напали,
    можете выбрать "простить" или "убить в ответ". Комиссару видитесь "мирным".

role-desc-arsonist =
    Поджигатель. Ночью "поджигаете" жертв, но они не умирают сразу.
    Когда у вас <b>3 и более жертв</b> — все они погибают одновременно,
    и вы становитесь одиночным победителем.

role-desc-crook =
    Аферист. <b>Доживёте до конца — победили в одиночку</b>. Особая способность:
    днём можете голосовать от имени другого игрока — ваш голос засчитается
    как его голос.

role-desc-snitch =
    Стукач. Ночью выбираете 1 игрока. <b>Если Комиссар проверяет именно его</b> —
    ваша роль раскрывается группе, и вы побеждаете! Игроков в маске не узнаёте.

# ===========================================================
# DM-based voting (Wave 6 — voting moved out of group chat)
# ===========================================================

voting-group-prompt-short =
    <e:scene-hanging> Пора найти виновных и наказать.
    На голосование — { $seconds } секунд.

voting-go-button = <e:scene-voting> Голосовать

voting-dm-prompt =
    <e:scene-hanging> <b>Пора найти виновных!</b>

    Кого, по-вашему, нужно повесить?

vote-recorded-dm-confirm = ✅ Ваш голос: <b>{ $target }</b>

vote-skipped-confirm = ✅ Вы выбрали "Никто".

# Comedic rumor-style alerts for invalid voters in HANGING_CONFIRM
vote-dead-alert = <e:status-death> Ты мёртв, голосовать не можешь! Дух тоже молчит.
vote-not-in-game-alert = 😴 Вы не в этой игре. Позовём вас в следующую!
vote-already-voted-alert = ✋ Вы уже проголосовали!

# AFK comedic last-words
afk-last-words =
    Кто-то из жителей слышал, как { $role } { $mention } перед смертью кричал:
    "Я больше во время игры не сплю-у-у-у-у!"

# Per-player game-end DM
game-end-dm-win =
    <e:status-trophy> <b>Поздравляем, вы победили!</b>

    <e:item-mask> Роль: { $role }
    ⭐ XP: +{ $xp }
    📊 ELO: { $elo_delta }
    <e:currency-dollar> Награда: { $dollars }$

game-end-dm-loss =
    <e:status-death> <b>В этот раз не повезло.</b>

    <e:item-mask> Роль: { $role }
    ⭐ XP: +{ $xp }
    📊 ELO: { $elo_delta }
    <e:currency-dollar> Деньги: { $dollars }$
