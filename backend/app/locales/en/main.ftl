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
    👋 Hi, <b>{ $username }</b>!

    🎭 Welcome to <b>Mafia Baku Black</b>!

    Here you can:
    • 🎮 Play Mafia in your Telegram groups
    • 💎 Earn diamonds, 💵 dollars, ⭐ XP
    • 🏆 Unlock achievements and climb the ELO ladder
    • 👑 Get premium status

    Pick an action:

btn-profile = 👤 Profile
btn-inventory = 🎒 Inventory
btn-buy-diamonds = 💎 Buy Diamonds
btn-help = ❓ Help

btn-add-to-group = ➕ Add to group

btn-language = 🌐 Language

btn-rules = 📖 Game rules


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

phase-night-start = 🌃 Night #{ $round }. Whispers of the night drift across the town...

phase-night-start-1 = 🌃 Night #{ $round }. Whispers of the night drift across the town...
phase-night-start-2 = 🌑 Night #{ $round }. The town murmurs under the moon — someone stopped breathing.
phase-night-start-3 = 🌃 Night #{ $round }. Lock your doors — there are footsteps in the street.
phase-night-start-4 = 🦉 Night #{ $round }. The owl is watching, but even it can't see everything.
phase-night-start-5 = 🌌 Night #{ $round }. The stars bear witness — the town doesn't sleep, it just pretends.

phase-day-start = ☀️ Day #{ $round }. The sun dried the blood spilled in the night...

phase-day-start-1 = ☀️ Day #{ $round }. The sun dried the blood spilled in the night...
phase-day-start-2 = 🌅 Day #{ $round }. The town wakes — but someone won't wake again.
phase-day-start-3 = ☕ Day #{ $round }. Breakfast time, but a few seats are empty...
phase-day-start-4 = 🐓 Day #{ $round }. The rooster crowed — time to count heads.
phase-day-start-5 = 🌤 Day #{ $round }. Dawn breaks, but night's shadows still linger.

phase-voting-start = 🗳 Voting time — should we hang somebody?


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

extend-indefinite = ⏳ Registration extended.

game-launched-by-admin = 🚀 The game has begun!


# ===========================================================
# NIGHT PROMPTS (private chat to player)
# ===========================================================

night-prompt-don = 🤵🏻 Don, who do you wish to eliminate tonight?

night-prompt-doctor = 👨🏻‍⚕ Doctor, who will you treat tonight?

night-prompt-hooker = 💃 Wanderer, who will you put to sleep tonight?

night-prompt-detective = 🕵🏼 Commissioner, your choice?

night-prompt-detective-check-only = 🕵🏼 Commissioner, on night 1 you may only investigate. Who do you check?

night-prompt-detective-both = 🕵🏼 Commissioner, who do you investigate or shoot? 🔍 = investigate, 🔫 = shoot

night-prompt-detective-prior-header = 🕵🏼 <b>Previously checked players:</b>
night-prompt-detective-prior-line = • <b>{ $name }</b> — { $role }
night-prompt-detective-chooser = 🕵🏼 What are we doing tonight?
night-prompt-detective-target-list-check = 🔍 Who do we check?
night-prompt-detective-target-list-kill = 🔫 Who do we take out?
btn-detective-check = 🔍 Investigate
btn-detective-kill = 🔫 Shoot
night-no-targets = ❌ No one to choose right now.

btn-skip = ⏭ Skip

night-skipped = Turn skipped.

night-skipped-confirm = ✅ You chose not to act this night.

night-not-in-active-game = You are not currently in any active game.

night-not-in-night-phase = The night phase has already ended.

night-cannot-act = You cannot perform this action.

night-target-invalid = The selected player does not exist or is already dead.

night-action-recorded = ✅ { $target } selected.

night-action-confirmed = ✅ Your choice: <b>{ $target }</b>

mafia-team-pick-broadcast = 🤵🏼 <b>{ $role }</b> ({ $actor }) picked: <b>{ $target }</b>


# ===========================================================
# GAME END
# ===========================================================

game-end-winner =
    🏆 Game over!

    { $team } wins!

    📋 Roles:

game-cancelled = ❌ The game has been cancelled.

game-cancelled-not-enough-players =
    ⏱ The game didn't start — not enough players joined in time (at least { $min_players } required).
    Use /game to start a new one.

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

feedback-doctor-saved = 👨🏻‍⚕ You — healed <b>{ $target }</b> :) Their visitor was { $visitors }.

feedback-doctor-no-visitors = 👨🏻‍⚕ The doctor couldn't help..

feedback-hooker-confirm = 💃 You put { $target } to sleep.

feedback-hooker-target = There it is — 💊 the drug is kicking in. Sweet dreams for a whole day...

mafia-kill-broadcast = 🤵🏼 During the Mafia vote, { $mention } was brutally killed 🩸


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
    ⭐ ID: <code>{ $id }</code>

    👤 { $name }

    💵 Dollars: { $dollars }
    💎 Diamonds: { $diamonds }

    🛡 Shield: { $shield }
    ⛑ Killer shield: { $killer_shield }
    ⚖️ Vote shield: { $vote_shield }
    🔫 Rifle: { $rifle }

    🎭 Mask: { $mask }
    📁 Fake document: { $fake_document }
    🃏 Next game role: { $next_role }

    🎯 Wins: { $wins }
    🎲 Total games: { $games_total }

inventory-header = 🎒 Your inventory:

inv-toggle-on = ✅ Enabled

inv-toggle-off = ⬜ Disabled

inv-no-items = 🚫 You don't own this item.

btn-toggle-on = { $emoji } - 🟢 ON

btn-toggle-off = { $emoji } - 🔴 OFF

btn-toggle-empty = { $emoji } - 🚫 0

btn-shop = 🛒 Shop

btn-buy-dollars = 💵 Buy

btn-buy-diamonds = 💎 Buy

btn-premium-groups = 👑 Premium groups

btn-news = 📢 News

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

shop-no-items = 🚫 Nothing available in this currency

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
    <b>Voting closed:</b>
    The town couldn't agree... No one was hanged today.

hanging-combined =
    <b>Voting results:</b>
    { $yes } 👍 | { $no } 👎

    { $mention } was hanged at the day meeting!

hanging-combined-with-role =
    <b>Voting results:</b>
    { $yes } 👍 | { $no } 👎

    { $mention } was hanged at the day meeting!
    They were { $role_emoji } <b>{ $role }</b>..

hanging-confirm-cannot-self = 😅 You can't vote on your own hanging!


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

help-text =
    ❓ <b>Help</b>

    <b>Main commands (private chat):</b>
    /start — Main menu
    /profile — Profile + inventory + stats
    /exchange — 💎 diamonds ↔ 💵 dollars

    <b>Group commands (after adding bot as admin):</b>
    /game — Start a new game
    /join — Join a game
    /leave — Leave a game
    /vote &lt;number&gt; — Cast your vote
    /stats — Group statistics

    <b>Premium:</b>
    • 👑 Premium status: /buy_premium
    • 🎁 Gift diamonds: <code>/give &lt;amount&gt;</code> (as reply)

    📢 News channel: @MafiaAzBot_news

rules-text =
    📖 <b>Mafia Game Rules</b>

    🎯 <b>Goal:</b> Win as your team.

    <b>3 main teams:</b>
    🤵🏼 <b>Mafia</b> — eliminate civilians
    👨‍👨‍👧‍👦 <b>Civilians</b> — find mafia and singletons
    🎯 <b>Singletons</b> — each has unique win conditions

    <b>🔄 Game cycle:</b>
    🌃 <b>Night</b> (60s) — roles take actions
    ☀️ <b>Day</b> (45s) — discuss results
    🗳 <b>Vote</b> (25s) — pick who to hang
    👍/👎 (15s) — confirmation

    ━━━━━━━━━━━━━━━━━━━━

    👨‍👨‍👧‍👦 <b>Civilians (10):</b>
    👨🏼 Citizen · 🕵🏻‍♂ Detective · 👮🏻‍♂ Sergeant · 🎖 Mayor (×2 vote)
    👨🏻‍⚕ Doctor · 💃 Hooker · 🧙‍♂ Hobo · 🤞🏼 Lucky
    🤦🏼 Suicide · 💣 Kamikaze

    🤵🏼 <b>Mafia (5):</b>
    🤵🏻 Don · 🤵🏼 Mafia · 👨‍💼 Lawyer · 👩🏼‍💻 Journalist · 🥷 Ninja

    🎯 <b>Singletons (6):</b>
    🔪 Maniac · 🐺 Werewolf · 🧙 Mage · 🧟 Arsonist · 🤹 Crook · 🤓 Snitch

    🛡 <b>Items (from shop):</b>
    🛡 Shield · ⛑ Killer shield · ⚖️ Vote shield · 🔫 Rifle
    🎭 Mask · 📁 Fake document

language-picker-prompt = 🌐 Pick a language:

language-switched = ✅ Language switched

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


# === Group settings menu ===

# --- Section A: /settings command responses ---

settings-admin-only = 🚫 This command is admin-only.

settings-sent-to-dm = ✉️ Settings sent to your private chat.

settings-cannot-dm = ❌ Cannot DM you. Please send /start to the bot first.

settings-dm-failed = ❌ Failed to send settings. Try again later.

settings-group-not-configured = ❌ This group is not configured yet.

# --- Section B: Settings home ---

settings-home =
    🛠 <b>{ $group_title }</b> settings

    Use the WebApp for full controls or quick toggles below:

btn-settings-webapp = 🌐 Full settings

btn-settings-history = 📊 Game history

btn-settings-roles = 🎭 Roles

btn-settings-timings = ⏱ Phase timings

btn-settings-items = 🛡 Items

btn-settings-silence = 🔇 Silence

btn-settings-gameplay = 🎮 Gameplay

btn-settings-lang = 🌐 Language

btn-settings-atmosphere = 📺 Atmosphere media

# --- Section C: Roles sub-menu ---

settings-roles-prompt =
    🎭 <b>Manage roles</b>

    Pick which roles can appear in games:

settings-team-civilians = 👨‍👨‍👧‍👦 Civilians

settings-team-mafia = 🤵🏼 Mafia

settings-team-singletons = 🎯 Singletons

# --- Section D: Timings sub-menu ---

settings-timings-prompt = ⏱ <b>Phase durations (in seconds)</b>

timing-registration = Registration

timing-night = Night

timing-day = Day

timing-mafia_vote = Mafia vote

timing-hanging_vote = Hanging vote

timing-hanging_confirm = Confirmation

timing-last_words = Last words

timing-afsungar_carry = Kamikaze choice

# --- Section E: Items sub-menu ---

settings-items-prompt =
    🛡 <b>Allowed items</b>

    Which protections are available in the shop and during games:

# --- Section F: Silence sub-menu ---

settings-silence-prompt =
    🔇 <b>Silence rules</b>

    Who can write and when:

silence-dead_players = Dead are silent

silence-sleeping_players = Sleeping are silent

silence-non_players = Non-players silent

silence-night_chat = Silent at night

# --- Section G: Gameplay sub-menu ---

settings-gameplay-status =
    🎮 <b>Gameplay settings</b>

    Mafia ratio: <b>{ $ratio }</b>
    Players: <b>{ $min_players }-{ $max_players }</b>

    Allow skip day vote: { $skip_day_vote }
    Allow skip night action: { $skip_night_action }

gameplay-ratio-low = Low (1/4)

gameplay-ratio-high = High (1/3)

gameplay-skip-day = Skip day vote

gameplay-skip-night = Skip night action

# --- Section H: Language sub-menu ---

settings-lang-prompt =
    🌐 <b>Group language</b>

    Bot messages will use this language:

# --- Section I: Atmosphere info ---

settings-atmosphere-info =
    📺 <b>Atmosphere media</b>

    🟢 = set, ⚪ = empty

    To set media, reply to a GIF/video in the group and send:
    <code>/setatmosphere &lt;slot&gt;</code>

    Slots: <code>night</code>, <code>day</code>, <code>voting</code>,
    <code>win_civilian</code>, <code>win_mafia</code>, <code>win_singleton</code>


# === Game start announcement + role descriptions ===

game-started-announcement =
    🎭 <b>The game has started!</b>

    Tap the button to see your role:

btn-show-my-role = 🎭 Your role

show-role-not-in-game = 🚫 You are not in this game

show-role-no-game = 🚫 No active game right now

show-role-alert = 🎭 Your role: { $role }\n\n{ $description }

dm-your-role =
    🎭 <b>You are { $role }!</b>

    { $description }

role-desc-citizen = Your task: find the mafia and vote them out by day.
role-desc-detective = Each night you check one player and learn their real role.
role-desc-sergeant = Detective's helper — you see their messages and protect them.
role-desc-mayor = Your daytime vote counts twice.
role-desc-doctor = Each night you heal one player, saving them from death.
role-desc-hooker = Each night you put one player to sleep, cancelling their night action.
role-desc-hobo = At night you visit one player and see their visitors.
role-desc-lucky = 50% chance to survive a deadly attack.
role-desc-suicide = If you're hanged during the day — you win!
role-desc-kamikaze = If you're hanged, you take one player with you.
role-desc-don = Mafia boss — each night you kill one player.
role-desc-mafia = Member of the mafia. You support the Don.
role-desc-lawyer = At night you protect one mafia from the detective and from being hanged.
role-desc-journalist = You can find the detective's helpers, but not the detective.
role-desc-killer = Mafia's strongest killer — pierces through all protections.
role-desc-maniac = Solo winner — survive to be the last one standing.
role-desc-werewolf = You transform into the role of whoever you attack.
role-desc-mage = Win if you survive to the very end.
role-desc-arsonist = Win if you kill 3+ players.
role-desc-crook = Win if you survive. By day you can vote in another player's name.
role-desc-snitch = If you and the detective both target the same player, their role is revealed publicly.

# ===========================================================
# DM-based voting (Wave 6 — voting moved out of group chat)
# ===========================================================

voting-group-prompt-short =
    ⚖️ Time to find the guilty and pass judgement.
    Voting time: { $seconds } seconds.

voting-go-button = 🗳 Cast vote

voting-dm-prompt =
    ⚖️ <b>Time to find the guilty!</b>

    Who do you think should hang?

vote-recorded-dm-confirm = ✅ Your vote: <b>{ $target }</b>

vote-skipped-confirm = ✅ You chose "Nobody".

# Comedic rumor-style alerts for invalid voters in HANGING_CONFIRM
vote-dead-alert = 💀 You're dead, you cannot vote! Even your ghost is silent.
vote-not-in-game-alert = 😴 You're not in this game. We'll call you for the next one!
vote-already-voted-alert = ✋ You already voted!

# AFK comedic last-words
afk-last-words =
    Someone in town heard { $role } { $mention } shout before dying:
    "I'm never sleeping during the gaaaaaame again!"

# Per-player game-end DM
game-end-dm-win =
    🏆 <b>Congratulations, you won!</b>

    🎭 Role: { $role }
    ⭐ XP: +{ $xp }
    📊 ELO: { $elo_delta }
    💵 Reward: { $dollars }$

game-end-dm-loss =
    💀 <b>No luck this time.</b>

    🎭 Role: { $role }
    ⭐ XP: +{ $xp }
    📊 ELO: { $elo_delta }
    💵 Money: { $dollars }$
