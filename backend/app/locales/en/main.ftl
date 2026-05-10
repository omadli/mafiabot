# Mafia Baku Black — @MafGameUzBot
# Locale: en (English)
# Project Fluent syntax: https://projectfluent.org/


# ===========================================================
# ONBOARDING (bot added to group)
# ===========================================================

onboarding-pick-language =
    👋 Hello! I am the Mafia bot.
    Please select the group language:

onboarding-only-admins-can-pick = ⚠️ Only group administrators can select the language.

onboarding-grant-admin-perms =
    ✅ Language set.
    Now please make me a group administrator. The following permissions are required:
      ✓ Delete messages
      ✓ Restrict members
      ✓ Pin messages
    These permissions are needed to manage the group during gameplay.
    Make @{ $bot_username } an admin, then press the button below.

onboarding-completed =
    🎉 All set! You can now start a game with /game.

onboarding-success-toast = ✅ Done! Bot is configured.

onboarding-perms-missing =
    ❌ The following permissions are missing: { $perms }
    Please grant them and check again.

btn-check-perms = 🔄 Check

perm-delete-messages = Delete messages
perm-restrict-members = Restrict members
perm-pin-messages = Pin messages


# ===========================================================
# /start (private chat)
# ===========================================================

start-welcome =
    👋 Hello, { $username }!
    Welcome to Mafia Baku Black.
    Add this bot to your Telegram group to start a game.

btn-profile = 👤 Profile
btn-inventory = 🎒 Inventory
btn-buy-diamonds = 💎 Buy Diamonds
btn-help = ❓ Help


# ===========================================================
# DEEPLINK JOIN FLOW
# ===========================================================

deeplink-invalid = ❌ Invalid link. Please try again from the group.

admin-login-deeplink-todo = 🔐 Super admin login — coming soon (Phase 3).

join-banned =
    🚫 You are temporarily banned.
    Ban expires: { $until }
    Reason: { $reason }

join-already-in-this-game = 😏 Easy there — you're already in the game. In the game. Got it?

join-already-in-other-group =
    ❌ You are already playing in another group: { $group_title }.
    You can only participate in one game at a time.

join-group-not-found = ❌ Group not found or bot is not active in that group.

join-no-active-registration =
    ⏱ Too late! Registration has already closed.
    Wait for the next game.

join-success =
    ✅ You have successfully joined the game :)

btn-back-to-group = 🔙 Back to group


# ===========================================================
# GROUP GAME COMMANDS
# ===========================================================

game-onboarding-required =
    ⚠️ Please finish setup first: make me a group admin and grant the required permissions.

game-todo-mvp = 🎮 /game is coming soon (Phase 1).

leave-not-in-game = ❌ You are not currently participating in any game.

leave-todo = 🚪 /leave is coming soon.

stop-todo = 🛑 /stop is coming soon.


# ===========================================================
# ROLE NAMES
# ===========================================================

role-citizen = 👨🏼 Civilian
role-detective = 🕵🏻‍♂ Commissioner Catani
role-sergeant = 👮🏻‍♂ Sergeant
role-mayor = 🎖 Mayor
role-doctor = 👨🏻‍⚕ Doctor
role-hooker = 💃 Wanderer
role-hobo = 🧙‍♂ Tramp
role-lucky = 🤞🏼 Lucky
role-suicide = 🤦🏼 Suicide
role-kamikaze = 💣 Kamikaze
role-don = 🤵🏻 Don
role-mafia = 🤵🏼 Mafia
role-lawyer = 👨‍💼 Lawyer
role-journalist = 👩🏼‍💻 Journalist
role-killer = 🥷 Ninja
role-maniac = 🔪 Maniac
role-werewolf = 🐺 Werewolf
role-mage = 🧙 Mage
role-arsonist = 🧟 Berserker
role-crook = 🤹 Trickster
role-snitch = 🤓 Snitch


# ===========================================================
# NIGHT ATMOSPHERIC MESSAGES (sent to group after each role acts)
# ===========================================================

night-action-msg-don = 🤵🏻 The Don has chosen his next prey...

night-action-msg-detective-check = 🕵🏻‍♂ Detective Cattani went hunting for evildoers...

night-action-msg-detective-shoot = 🕵🏻‍♂ Detective Cattani loaded their pistol...

night-action-msg-doctor = 👨🏻‍⚕ The Doctor set off on his evening rounds...

night-action-msg-hooker = 💃 It seems the Wanderer has a visitor tonight...

night-action-msg-hobo = 🧙‍♂ The Tramp wandered into the streets looking for bottles...


# ===========================================================
# NIGHT RESULT MESSAGES (start of day, sent to group)
# ===========================================================

night-result-killed-single =
    🌅 Last night { $role_emoji_name } { $mention } was brutally murdered.
    Word on the street is that { $killer_role_emoji_name } paid them a visit...

night-result-no-deaths = 🌅 Hard to believe, but no one died last night...

night-result-shield-used = 💫 Someone used their protection!


# ===========================================================
# LAST WORDS
# ===========================================================

last-words-prompt-hanged =
    You were mercilessly hanged :(
    You may speak your last words:

last-words-prompt-killed-night =
    You were mercilessly killed :(
    You may speak your last words:

last-words-broadcast =
    Someone heard { $role_emoji } { $role_name } { $mention } scream before death:
    <i>{ $message }</i>


# ===========================================================
# GAME REGISTRATION / START ERRORS
# ===========================================================

game-bounty-insufficient = ❌ /game { $required } requires at least { $required } diamonds. You have: { $have }

game-already-running = ❌ A game is already in progress in this group!

game-cannot-start-not-waiting = ❌ A game can only be started during the registration phase.

game-not-enough-players = ❌ At least 4 players are required. Not enough yet.

join-game-full = ❌ The game is full. Maximum 30 players.

error-only-admins = ❌ This command is available to group administrators only.


# ===========================================================
# REGISTRATION MESSAGE
# ===========================================================

registration-message =
    🎲 Game registration has started!
    Press the button below to join.

    ⏱ Time: { $timer }
    👥 Players ({ $count }):
    { $players }

registration-no-players-yet = — (no one has joined yet)

registration-bounty = 💎 Each winner receives: { $per_winner } diamonds (escrow: { $pool })

btn-join-game = 🎮 Join Game


# ===========================================================
# PHASE CHANGES
# ===========================================================

phase-night-start = 🌃 Night #{ $round } has begun. Roles are taking action...

phase-day-start = ☀️ Day #{ $round } has begun. Start the discussion!

phase-voting-start = 🗳 Time to vote! /vote @user


# ===========================================================
# VOTING
# ===========================================================

vote-not-in-voting = It is not the voting phase right now.

vote-not-alive = You are dead. You cannot vote.

vote-target-required = Use /vote @username or reply to someone's message.

vote-target-invalid = That player does not exist or is already dead.

vote-recorded = { $voter } → voted for { $target }.

vote-recorded-anon = ✅ Your vote has been recorded (anonymous)


# ===========================================================
# /leave AND /stop
# ===========================================================

leave-not-allowed = /leave is disabled in this group.

leave-already-dead = You are already dead.

leave-broadcast = { $mention } could not bear the evil of this city and took their own life.

unjoin-success = ✅ { $name } has left the registration.

stop-no-game = There is no active game right now.

stop-not-allowed = /stop is disabled in this group.

stop-success = 🛑 The game has been stopped.

extend-not-in-registration = You can only extend time during the registration phase.

extend-success = ⏱ Time extended by { $seconds } seconds.


# ===========================================================
# NIGHT PROMPTS (private chat to player)
# ===========================================================

night-prompt-don = 🤵🏻 Don, who do you wish to eliminate tonight?

night-prompt-doctor = 👨🏻‍⚕ Doctor, who will you treat tonight?

night-prompt-hooker = 💃 Wanderer, who will you put to sleep tonight?

night-prompt-detective = 🕵🏼 Commissioner, your choice?

night-prompt-detective-check-only = 🕵🏼 Commissioner, on night 1 you may only investigate. Who do you check?

night-prompt-detective-both = 🕵🏼 Commissioner, who do you investigate or shoot? 🔍 = investigate, 🔫 = shoot

btn-skip = ⏭ Skip

night-skipped = Turn skipped.

night-skipped-confirm = ✅ You chose not to act this night.

night-not-in-active-game = You are not currently in any active game.

night-not-in-night-phase = The night phase has already ended.

night-cannot-act = You cannot perform this action.

night-target-invalid = The selected player does not exist or is already dead.

night-action-recorded = ✅ { $target } selected.

night-action-confirmed = ✅ Your choice: { $target }


# ===========================================================
# GAME END
# ===========================================================

game-end-winner =
    🏆 Game over!

    { $team } wins!

    📋 Roles:

game-cancelled = ❌ The game has been cancelled.

team-citizens = 👨🏼 Civilians

team-mafia = 🤵🏼 Mafia

team-singleton = 🎯 Singleton


# ===========================================================
# MISCELLANEOUS
# ===========================================================

click-to-join-private = Opens in private chat with the bot...


# ===========================================================
# NIGHT ATMOSPHERIC MESSAGES — NEW ROLES
# ===========================================================

night-action-msg-lawyer = 👨‍💼 Lawyer is searching for whom to protect among the Mafia...

night-action-msg-journalist = 👩🏼‍💻 The Journalist is investigating under cover of night...

night-action-msg-killer = 🥷 The Ninja has begun his bloody work...

night-action-msg-maniac = 🔪 Maniac hid among the bushes and drew the knife from its sheath...

night-action-msg-werewolf = 🐺 The Werewolf howled into the dark night...

night-action-msg-arsonist = 🧟 The Berserker has marked his next victim...

night-action-msg-crook = 🤹 The Crook is planning to wear a new face tonight...

night-action-msg-snitch = 🤓 Snitch began searching to gather information...

night-action-msg-kamikaze = 🧞‍♂️ The Kamikaze is summoning his mystical powers...


# ===========================================================
# NIGHT PROMPTS — NEW ROLES (private chat to player)
# ===========================================================

night-prompt-hobo = 🧙‍♂ Hobo, whose door are you knocking on tonight?

night-prompt-lawyer = 👨‍💼 Lawyer, which Mafia member are you shielding tonight?

night-prompt-journalist = 👩🏼‍💻 Journalist, who are you investigating?

night-prompt-killer = 🥷 Ninja, who do you eliminate tonight? (pierces all shields)

night-prompt-maniac = 🔪 Maniac, who do you kill tonight?

night-prompt-mafia = 🤵🏼 Mafia, who did you agree to target with the Don tonight?

night-prompt-arsonist = 🧟 Berserker, who is your next victim?

night-prompt-crook = 🤹 Crook, whose vote will you cast tomorrow?

night-prompt-snitch = 🤓 Snitch, who do you think the Commissioner will investigate?


# ===========================================================
# FEEDBACK DMs (after night resolution)
# ===========================================================

feedback-detective-result = 🕵🏼 { $target }'s role is — { $role }.

feedback-doctor-saved = 👨🏻‍⚕ You treated { $target }! Their visitors tonight were: { $visitors }

feedback-doctor-no-visitors = 👨🏻‍⚕ You treated { $target }. Nobody came to them tonight.

feedback-hooker-confirm = 💃 You put { $target } to sleep.

feedback-hooker-target = There it is — 💊 the drug is kicking in. Sweet dreams for a whole day...


# ===========================================================
# AFK
# ===========================================================

afk-kicked = { $mention } fell asleep mid-game and was removed (XP -50)


# ===========================================================
# STATS COMMANDS
# ===========================================================

stats-no-games = You have not played a single game yet. Start with /game!

stats-period-todo = Period statistics are coming soon (Phase 2)

stats-no-role-data = No role data available

stats-role-no-data = You have not played as { $role } yet

stats-role-detail =
    📊 Stats for { $role }:
    🎮 Games: { $games }
    🏆 Wins: { $wins }
    📈 WR: { $winrate }%
    💎 ELO: { $elo }

stats-personal =
    👤 { $name }

    🎮 Games: { $games }   🏆 Wins: { $wins }   💔 Losses: { $losses }
    📈 Winrate: { $winrate }%   💎 ELO: { $elo }
    ⭐ XP: { $xp }   🏅 Level: { $level }

    🔥 Current streak: { $streak }   📌 Best streak: { $longest }

    🎭 Favourite roles: { $top_roles }

    👨🏼 Civilian: { $citizen_games } games, { $citizen_wins } wins
    🤵🏼 Mafia: { $mafia_games } games, { $mafia_wins } wins
    🎯 Singleton: { $singleton_games } games, { $singleton_wins } wins

top-empty = The leaderboard is empty

top-group-only = This command only works inside a group

top-header = 🏆 Top 10 (by { $sort }):

global-top-header = 🌍 Global Top 10:

profile-target-not-found = User not found. Reply to a message or type @username.

profile-no-games = { $name } has not played any games yet

group-stats-no-games = No games have been played in this group yet

group-stats-message =
    📊 Group statistics:
    🎮 Total games: { $total_games }
    ⏱ Avg duration: { $avg_duration } min
    👥 Avg players: { $avg_players }

    Side winrates:
    👨🏼 Civilians: { $citizens_wr }%
    🤵🏼 Mafia: { $mafia_wr }%
    🎯 Singleton: { $singleton_wr }%


# ===========================================================
# PROFILE AND INVENTORY
# ===========================================================

profile-info =
    👤 { $name }
    { $is_premium ->
        [true] 👑 Premium (expires: { $premium_until })
       *[false] —
    }

    💎 Diamonds: { $diamonds }
    💵 Dollars: { $dollars }
    ⭐ XP: { $xp }   🏅 Level: { $level }

inventory-header = 🎒 Your inventory:

inv-toggle-on = ✅ Enabled

inv-toggle-off = ⬜ Disabled

inv-no-items = 🚫 You don't own this item.

btn-shop = 🛒 Shop

btn-back = 🔙 Back

btn-exchange = 🔁 Exchange

btn-close = ❎ Close


# ===========================================================
# SHOP
# ===========================================================

shop-welcome =
    🛒 Welcome to the Mafia shop!
    What would you like to buy?

shop-welcome-balance =
    🛒 <b>Shop</b>

    Your balance: <b>{ $diamonds }</b> 💎  <b>{ $dollars }</b> 💵

shop-diamonds-header = 💎 Diamond packages:

shop-items-header =
    🛡 <b>Items</b>

    Balance: <b>{ $diamonds }</b> 💎  <b>{ $dollars }</b> 💵

    Pay in the listed currency.

shop-premium-info =
    👑 Premium user:
    • 2x protection
    • Protection against the Wanderer
    • Other privileges

btn-buy-items = 🎒 Weapons/shields

btn-buy-premium = 👑 Premium

btn-buy-premium-30d = ⭐ 30-day premium — { $price } 💎

buy-insufficient = ❌ Not enough diamonds

buy-success = ✅ Purchased!

buy-success-detailed = ✅ { $item } purchased! ({ $cost } { $currency })

buy-insufficient-diamonds = 💎 Not enough diamonds

buy-insufficient-dollars = 💵 Not enough dollars

premium-activated = 👑 Premium activated: { $days } days

payment-success = ✅ Payment successful! +💎 { $diamonds }

payment-failed = ❌ Payment failed


# ===========================================================
# CURRENCY EXCHANGE
# ===========================================================

exchange-menu =
    🔁 <b>Currency exchange</b>

    Your balance: <b>{ $diamonds }</b> 💎  <b>{ $dollars }</b> 💵
    Rate: 1 💎 = { $rate } 💵

    Pick a direction:

exchange-success = ✅ Credited { $got } { $currency }!

exchange-disabled = 🚫 Exchange is currently disabled.

exchange-insufficient-diamonds = 💎 Not enough diamonds for exchange

exchange-insufficient-dollars = 💵 Not enough dollars for exchange

exchange-below-minimum = ❌ Amount is below the minimum


# ===========================================================
# GIVEAWAY
# ===========================================================

give-amount-required = ❌ Please specify an amount, e.g. /give 50

give-amount-too-small = ❌ Amount must be at least 1

give-cannot-self = ❌ You cannot gift diamonds to yourself

give-insufficient = ❌ Not enough diamonds (you have 💎 { $have }, need 💎 { $need })

give-target-not-found = ❌ User not found

give-direct-success = { $sender } 💎 { $amount } gifted to { $receiver }!

give-creating = 💎 Creating giveaway...

give-group-message =
    🎁 { $sender } started a { $amount }-diamond giveaway!
    The sooner you click, the more you get.

give-no-clicks = 🎁 Giveaway ended — nobody clicked

give-results-header = 🎁 Giveaway results:

btn-claim-diamond = 💎 Claim diamonds

giveaway-clicked-ok = ✅ Claimed!

giveaway-already-clicked-or-finished = ❌ You have already clicked or the giveaway has ended


# ===========================================================
# VOTING UI (inline buttons)
# ===========================================================

voting-prompt = 🗳 Time to vote! Living players: { $count }. Cast your vote using the button below:

vote-skip-button = ❌ Nobody

vote-cannot-self = ❌ You cannot vote for yourself

vote-recorded-toast = ✅ Your vote: { $target }

vote-skipped-toast = ✅ You chose "Nobody"

vote-broadcast = <b>{ $voter }</b> -- voted for <b>{ $target }</b>

vote-broadcast-abstain = 🚫 <b>{ $voter }</b> decided not to choose anyone..


# ===========================================================
# HANGING CONFIRMATION
# ===========================================================

hanging-confirm-prompt =
    ⚖️ Confirm hanging { $target }?
    👍 = yes, 👎 = no

hanging-yes = 👍 Yes, hang them

hanging-no = 👎 No

hanging-confirm-expired = ❌ Confirmation window has expired

hanging-tally =
    <b>Voting results:</b>
    { $yes } 👍 | { $no } 👎

hanging-result-with-role = <b>{ $name }</b> was hanged at the day meeting! They were { $role_emoji } <b>{ $role }</b>..

hanging-result = <b>{ $name }</b> was hanged at the day meeting!

hanging-cancelled =
    <b>Voting results:</b>
    People couldn't agree ({ $yes } 👍 | { $no } 👎)...
    Due to disagreement, no one was hanged...


# ===========================================================
# MAGE REACTIVE MESSAGES (private to player)
# ===========================================================

mage-attacked = 🧙 { $attacker_role } has attacked you.\nDo you forgive them or kill them?

mage-forgive = 💚 Forgive

mage-kill = 💀 Kill

mage-forgive-confirm = Forgiven

mage-forgive-confirm-text = 💚 You forgave them. They live.

mage-kill-confirm = Killed

mage-kill-confirm-text = 💀 { $target } has been killed (by your curse)


# ===========================================================
# ARSONIST (BERSERKER) MESSAGES
# ===========================================================

arsonist-final-night-button = 🔥 Final Night!

arsonist-queued = 🧟 { $target } added to the list

arsonist-final-confirm = 💥 Final night activated! Everyone you marked will die.


# ===========================================================
# KAMIKAZE MESSAGES
# ===========================================================

kamikaze-choose-victim = 🧞 You have been hanged! Who do you take with you to the grave?

kamikaze-took-victim =
    🧞 Kamikaze took { $victim } to hell with them..
    They were { $victim_role_emoji } { $victim_role }.

kamikaze-took-confirm = Chosen

kamikaze-took-confirm-text = 🧞 You took { $target } with you.


# ===========================================================
# WEREWOLF TRANSFORMATION MESSAGES (sent to group)
# ===========================================================

transform-werewolf-to-mafia = 🐺 Werewolf transformed into 🤵🏼 Mafia!

transform-werewolf-to-sergeant = 🐺 Werewolf transformed into 👮🏻‍♂ Sergeant!


# ===========================================================
# SNITCH REVEAL BROADCAST (sent to group)
# ===========================================================

snitch-reveal-broadcast = 📢 Snitch report: { $target }'s role is — { $role }!


# ===========================================================
# HELP AND RULES
# ===========================================================

help-private =
    ❓ Help (private chat):

    /start — launch the bot
    /profile — your profile
    /inventory — weapons/shields
    /stats — statistics
    /global_top — global rankings
    /rules — game rules

    Use /game in a group chat to start a game.

help-group =
    ❓ Group commands:

    /game [bounty] — start a new game
    /leave — leave the game
    /vote @user — cast a vote
    /give amount [reply] — gift diamonds
    /stats /top /group_stats /profile — statistics
    /extend N — extend registration time
    /stop — cancel game (admins only)
    /rules — game rules

rules-summary =
    📖 Mafia Baku Black — rules:

    The city is split into two sides: civilians and mafia.
    Each night the mafia silently eliminates one player. Each
    day the town debates and votes to hang a suspect.
    Commissioner Cattani hunts the wicked; the Doctor saves
    the doomed.

    Singleton roles (Maniac, Werewolf, Mage and others)
    play alone under their own win conditions.

    Victory: wipe out the mafia — civilians win.
    Match or outnumber the civilians — mafia wins.

    Start with /game. Good luck!


# === Mafia chat ===

mafia-chat-opened =
    🤵🏻 Mafia night is open.
    You can chat with your teammates:
    { $members }

    💬 Any text you send here is relayed to other mafia members.


# === Atmosphere media ===

atmosphere-admin-only = 🚫 This command is admin-only.

atmosphere-help =
    📺 <b>Atmosphere media</b>

    Reply to a GIF/video with:
    <code>/setatmosphere &lt;slot&gt;</code>

    Available slots: { $slots }

atmosphere-invalid-slot = ❌ Invalid slot. Available: { $slots }

atmosphere-reply-required = ❌ Reply to an animation or video.

atmosphere-no-media = ❌ No media found in the replied message.

atmosphere-no-group = ❌ Group settings not found.

atmosphere-saved = ✅ Media saved for slot <b>{ $slot }</b>.

atmosphere-clear-help = 🧹 <code>/clearatmosphere &lt;slot&gt;</code> — clear slot. Available: { $slots }

atmosphere-cleared = ✅ <b>{ $slot }</b> cleared.


# ===========================================================
# NEW KEYS (adds)
# ===========================================================

leave-broadcast-with-role =
    { $mention } couldn't bear the evils of this city and took their own life.
    They were { $role_emoji } { $role_name }.

crook-stole-vote-dm = 🎭 The Crook deceived you and stole your voting right for today's vote.

arsonist-self-burn = <b>{ $name }</b> (🧟 Arsonist) killed themselves!

game-end-header = <b>Game over!</b>

game-end-winners-section = <b>Winners:</b>

game-end-losers-section = <b>Other players:</b>

game-end-duration = <i>Game lasted { $minutes } minutes</i>
