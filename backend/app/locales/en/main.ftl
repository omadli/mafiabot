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

    <e:item-mask> Welcome to <b>Mafia Baku Black</b>!

    Here you can:
    • 🎮 Play Mafia in your Telegram groups
    • <e:currency-diamond> Earn diamonds, <e:currency-dollar> dollars, ⭐ XP
    • <e:status-trophy> Unlock achievements and climb the ELO ladder
    • 👑 Get premium status

    Pick an action:

btn-profile = 👤 Profile
btn-inventory = 🎒 Inventory
btn-buy-diamonds = <e:currency-diamond> Buy Diamonds
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
btn-open-bot = 🤖 Open bot


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

night-result-shield-used = <e:status-spark> Someone used their protection!

feedback-shield-used =
    🛡 Someone tried to kill you tonight.
    Your shield saved you.

feedback-killer-shield-used =
    ⛑ A maniac tried to kill you.
    Your anti-maniac shield saved you.

feedback-fake-document-used =
    📁 Someone was curious about your role.
    You flashed your forged papers and they read you as "citizen".

feedback-vote-shield-used =
    ⚖️ The town tried to hang you today.
    Your vote shield kept you alive.

hanging-vote-shield-used = ⚖️ { $mention } used a vote shield.


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

last-words-sent-confirm = ✅ Your message has been delivered to the group!


# ===========================================================
# FLOOD CONTROL — sassy replies to command spam
# ===========================================================

flood-alert-1 = 😤 Hey! Easy there — I'm not your personal fidget toy. Two seconds, please!
flood-alert-2 = 🤨 Mashing that button again? Did your command key get stuck or what?
flood-alert-3 = 🙄 Quit hammering me, buddy. Out of patience or out of keyboard?
flood-alert-4 = 😡 That's enough! One more poke and I'm tossing you out of the chat.


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

registration-message-indefinite =
    🎲 Game registration has started!
    Press the button below to join.

    ⏳ Time extended indefinitely — the game starts when an admin runs /start.
    👥 Players ({ $count }):
    { $players }

registration-no-players-yet = — (no one has joined yet)

registration-bounty = <e:currency-diamond> Each winner receives: { $per_winner } diamonds (escrow: { $pool })

btn-join-game = 🎮 Join Game


# ===========================================================
# PHASE CHANGES
# ===========================================================

phase-night-start =
    <b>🌚 🌃Night:</b> { $round }
    <i>Only the brave and the fearless stepped outside. Come morning, we'll count the survivors...</i>

phase-night-start-1 =
    <b>🌚 🌃Night:</b> { $round }
    <i>Only the brave and the fearless stepped outside. Come morning, we'll count the survivors...</i>
phase-night-start-2 =
    <b>🌚 🌃Night:</b> { $round }
    <i>The town murmurs under the moon — someone stopped breathing.</i>
phase-night-start-3 =
    <b>🌚 🌃Night:</b> { $round }
    <i>Lock your doors — there are footsteps in the street.</i>
phase-night-start-4 =
    <b>🌚 🌃Night:</b> { $round }
    <i>The owl is watching, but even it can't see everything.</i>
phase-night-start-5 =
    <b>🌚 🌃Night:</b> { $round }
    <i>The stars bear witness — the town doesn't sleep, it just pretends.</i>

phase-day-start =
    <b>Good morning🌝</b>
    <b>🌄Day:</b> { $round }
    Whispers of the night drift across the town..

phase-day-start-1 =
    <b>Good morning🌝</b>
    <b>🌄Day:</b> { $round }
    Whispers of the night drift across the town..
phase-day-start-2 =
    <b>Good morning🌝</b>
    <b>🌄Day:</b> { $round }
    The sun dried the blood spilled in the night...
phase-day-start-3 =
    <b>Good morning🌝</b>
    <b>🌄Day:</b> { $round }
    The town wakes — but someone won't wake again.
phase-day-start-4 =
    <b>Good morning🌝</b>
    <b>🌄Day:</b> { $round }
    Breakfast time, but a few seats are empty...
phase-day-start-5 =
    <b>Good morning🌝</b>
    <b>🌄Day:</b> { $round }
    The rooster crowed — time to count heads.



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

leave-self-hanged = 🪢 { $mention } didn't wait for the verdict and hanged themselves.

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

night-prompt-detective-both = 🕵🏼 Commissioner, who do you investigate or shoot? <e:action-check> = investigate, <e:item-rifle> = shoot

night-prompt-detective-prior-header = 🕵🏼 <b>Previously checked players:</b>
night-prompt-detective-prior-line = • <b>{ $name }</b> — { $role }
night-prompt-detective-chooser = 🕵🏼 What are we doing tonight?
night-prompt-detective-target-list-check = <e:action-check> Who do we check?
night-prompt-detective-target-list-kill = <e:item-rifle> Who do we take out?
btn-detective-check = <e:action-check> Investigate
btn-detective-kill = <e:item-rifle> Shoot
night-no-targets = ❌ No one to choose right now.
night-no-rifle = <e:item-rifle> You're out of rifle rounds.

rifle-confirm-prompt =
    🔫 Do you want to shoot <b>{ $target }</b> with the rifle?
    The rifle pierces every defence on the target.
    One-shot consumable — gone after firing.

btn-rifle-yes = ✅ Yes, fire
btn-rifle-no = ❌ No

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
    <e:status-trophy> Game over!

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

feedback-detective-target-notice = 🕵🏼 Tonight someone got curious about your role...

feedback-doctor-target-saved = 👨🏻‍⚕ The doctor healed you.

feedback-doctor-target-visit = 👨🏻‍⚕ The doctor came to visit you.

feedback-hooker-confirm = 💃 You put { $target } to sleep.

feedback-hooker-target = There it is — <e:action-heal> the drug is kicking in. Sweet dreams for a whole day...

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
    <e:status-trophy> Wins: { $wins }
    📈 WR: { $winrate }%
    <e:currency-diamond> ELO: { $elo }

stats-personal =
    👤 { $name }

    🎮 Games: { $games }   <e:status-trophy> Wins: { $wins }   💔 Losses: { $losses }
    📈 Winrate: { $winrate }%   <e:currency-diamond> ELO: { $elo }
    ⭐ XP: { $xp }   🏅 Level: { $level }

    🔥 Current streak: { $streak }   📌 Best streak: { $longest }

    <e:item-mask> Favourite roles: { $top_roles }

    👨🏼 Civilian: { $citizen_games } games, { $citizen_wins } wins
    🤵🏼 Mafia: { $mafia_games } games, { $mafia_wins } wins
    🎯 Singleton: { $singleton_games } games, { $singleton_wins } wins

top-empty = The leaderboard is empty

top-group-only = This command only works inside a group

top-header = <e:status-trophy> Top 10 (by { $sort }):

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

    <e:currency-dollar> Dollars: { $dollars }
    <e:currency-diamond> Diamonds: { $diamonds }
    { $premium_line }

    <e:item-shield> Shield: { $shield }
    <e:item-killer-shield> Killer shield: { $killer_shield }
    <e:scene-hanging> Vote shield: { $vote_shield }
    <e:item-rifle> Rifle: { $rifle }

    <e:item-mask> Mask: { $mask }
    <e:item-fake-document> Fake document: { $fake_document }
    🃏 Next game role: { $next_role }

    🎯 Wins: { $wins }
    🎲 Total games: { $games_total }

profile-premium-active = 👑 Premium: active until { $expires_at }
profile-premium-inactive = 👑 Premium: not purchased

inventory-header = 🎒 Your inventory:

inv-toggle-on = ✅ Enabled

inv-toggle-off = ⬜ Disabled

inv-no-items = 🚫 You don't own this item.

btn-toggle-on = { $emoji } - 🟢 ON

btn-toggle-off = { $emoji } - 🔴 OFF

btn-toggle-empty = { $emoji } - 🚫 0

btn-shop = 🛒 Shop

btn-buy-dollars = <e:currency-dollar> Buy

btn-premium-groups = 👑 Premium groups
btn-pick-next-role = 🃏 Pick next role
btn-clear-next-role = 🃏 Clear pick
pick-role-prompt = 🃏 <b>Which role do you want next game?</b>
pick-role-confirmed = ✅ You'll play as { $role } next game!
pick-role-already-chosen = ℹ️ You already picked a role.
pick-role-cleared = ❎ Role pick cleared.

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

    Your balance: <b>{ $diamonds }</b> <e:currency-diamond>  <b>{ $dollars }</b> <e:currency-dollar>

shop-diamonds-header = <e:currency-diamond> Diamond packages:

shop-no-items = 🚫 Nothing available in this currency

shop-items-header =
    <e:item-shield> <b>Items</b>

    Balance: <b>{ $diamonds }</b> <e:currency-diamond>  <b>{ $dollars }</b> <e:currency-dollar>

    Pay in the listed currency.

shop-premium-info =
    👑 <b>Premium user</b>
    • 2x protection
    • Protection against the Wanderer
    • Other privileges

    Your status: <b>not purchased</b>

shop-premium-info-active =
    👑 <b>Premium user</b>
    • 2x protection
    • Protection against the Wanderer
    • Other privileges

    You already have premium — active until <b>{ $expires_at }</b>.
    Use one of the buttons below to extend it.

btn-buy-items = 🎒 Weapons/shields

btn-buy-premium = 👑 Premium

btn-buy-premium-30d = ⭐ 1-month premium — { $price } <e:currency-diamond>

btn-buy-premium-365d = ⭐ 1-year premium — { $price } <e:currency-diamond>

btn-extend-premium-30d = ⏳ Extend by 30 days — { $price } <e:currency-diamond>

btn-extend-premium-365d = ⏳ Extend by 1 year — { $price } <e:currency-diamond>

shop-special-pick-prompt =
    🃏 <b>Special role</b>

    Pick a role below — price: <b>{ $price }</b>

    The chosen role will be assigned to you in the next game.

shop-special-purchased = ✅ { $role } purchased! ({ $cost } { $currency }). You'll play this role in the next game.

premium-groups-empty =
    🚫 No premium groups yet.

    Premium groups give players 2x more rewards.

premium-groups-header =
    👑 <b>Premium groups — TOP</b>

    Playing in these groups grants { $multiplier }x dollars and diamonds!

premium-groups-row = { $rank }. <b>{ $title }</b> — { $games } games

buy-insufficient = ❌ Not enough diamonds

buy-success = ✅ Purchased!

buy-success-detailed = ✅ { $item } purchased! ({ $cost } { $currency })

buy-insufficient-diamonds = <e:currency-diamond> Not enough diamonds

buy-insufficient-dollars = <e:currency-dollar> Not enough dollars

premium-activated = 👑 Premium activated: +{ $days } days. Valid until { $expires_at }.

premium-extended = ⏳ Premium extended: +{ $days } days. Now valid until { $expires_at }.

payment-success = ✅ Payment successful! +<e:currency-diamond> { $diamonds }

payment-failed = ❌ Payment failed


# ===========================================================
# CURRENCY EXCHANGE
# ===========================================================

exchange-menu =
    🔁 <b>Currency exchange</b>

    Your balance: <b>{ $diamonds }</b> <e:currency-diamond>  <b>{ $dollars }</b> <e:currency-dollar>
    Rate: 1 <e:currency-diamond> = { $rate } <e:currency-dollar>

    Pick a direction:

exchange-success = ✅ Credited { $got } { $currency }!

exchange-disabled = 🚫 Exchange is currently disabled.

exchange-insufficient-diamonds = <e:currency-diamond> Not enough diamonds for exchange

exchange-insufficient-dollars = <e:currency-dollar> Not enough dollars for exchange

exchange-below-minimum = ❌ Amount is below the minimum


# ===========================================================
# GIVEAWAY
# ===========================================================

give-amount-required = ❌ Please specify an amount, e.g. /give 50

give-amount-too-small = ❌ Amount must be at least 1

give-cannot-self = ❌ You cannot gift diamonds to yourself

give-insufficient = ❌ Not enough diamonds (you have <e:currency-diamond> { $have }, need <e:currency-diamond> { $need })

give-target-not-found = ❌ User not found

give-direct-success = { $sender } <e:currency-diamond> { $amount } gifted to { $receiver }!

give-creating = <e:currency-diamond> Creating giveaway...

give-group-message =
    🎁 { $sender } started a { $amount }-diamond giveaway!
    The sooner you click, the more you get.

give-no-clicks = 🎁 Giveaway ended — nobody clicked

give-results-header = 🎁 Giveaway results:

btn-claim-diamond = <e:currency-diamond> Claim diamonds

giveaway-clicked-ok = ✅ Claimed!

giveaway-already-clicked-or-finished = ❌ You have already clicked or the giveaway has ended


# ===========================================================
# VOTING UI (inline buttons)
# ===========================================================

voting-prompt = <e:scene-voting> Time to vote! Living players: { $count }. Cast your vote using the button below:

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
    <e:scene-hanging> Confirm hanging { $target }?
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
    { $yes } 👍 | { $no } 👎

    <i>The town couldn't agree — voting turned into a shouting match, and everyone went home...</i>

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

mage-attacked =
    🧙 { $attacker_role } has attacked you.
    Do you forgive them or kill them?

mage-forgive = 💚 Forgive

mage-kill = <e:status-death> Kill

mage-forgive-confirm = Forgiven

mage-forgive-confirm-text = 💚 You forgave them. They live.

mage-kill-confirm = Killed

mage-kill-confirm-text = <e:status-death> { $target } has been killed (by your curse)


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

    <b>Private chat commands:</b>
    /start — Main menu
    /profile — Profile, inventory, shop (= /inventory, /items)
    /exchange — <e:currency-diamond> diamonds ↔ <e:currency-dollar> dollars
    /stats — My statistics
    /global_top — Global leaderboard
    /help — Help · /rules — Rules

    <b>Group commands (bot added as admin):</b>
    /game [bounty] — Start a new game (optional <e:currency-diamond> bounty)
    /start — Launch the queued game
    /leave — Leave the game
    /extend &lt;sec&gt; — Extend registration time
    /stop — Cancel the game (admin)
    /settings — Settings (admin)
    /give &lt;amount&gt; — Gift <e:currency-diamond> diamonds (reply or group inline)
    /stats · /top · /global_top · /profile · /group_stats — Statistics

    <b>💡 Note:</b>
    • Joining and voting happen via buttons (no separate commands)
    • 👑 Premium and 🛒 shop — through the /profile menu

    📢 News channel: @Mafiauzbot_news

rules-text =
    📖 <b>Mafia Game Rules</b>

    🎯 <b>Goal:</b> Win as your team.

    <b>3 main teams:</b>
    🤵🏼 <b>Mafia</b> — eliminate civilians
    👨‍👨‍👧‍👦 <b>Civilians</b> — find mafia and singletons
    🎯 <b>Singletons</b> — each has unique win conditions

    <b>🔄 Game cycle:</b>
    🌃 <b>Night</b> (60s) — roles take actions
    <e:scene-day> <b>Day</b> (45s) — discuss results
    <e:scene-voting> <b>Vote</b> (25s) — pick who to hang
    👍/👎 (15s) — confirmation

    ━━━━━━━━━━━━━━━━━━━━

    👨‍👨‍👧‍👦 <b>Civilians (9):</b>
    👨🏼 <b>Citizen</b> — ordinary townsfolk
    🕵🏻‍♂ <b>Detective Cattani</b> — investigates one player each night
    👮🏻‍♂ <b>Sergeant</b> — Detective's helper
    🎖 <b>Mayor</b> — vote counts double
    👨🏻‍⚕ <b>Doctor</b> — heals one player each night
    💃 <b>Hooker</b> — puts one player to sleep for the night
    🧙‍♂ <b>Hobo</b> — can identify the killer
    🤞🏼 <b>Lucky</b> — 50% survival chance
    💣 <b>Kamikaze</b> — when hanged, takes someone with them

    🤵🏼 <b>Mafia (5):</b>
    🤵🏻 <b>Don</b> — kills one player per night
    🤵🏼 <b>Mafia</b> — supports the Don
    👨‍💼 <b>Lawyer</b> — protects from the Detective and from hanging
    👩🏼‍💻 <b>Journalist</b> — can spot the Doctor / Hobo / Hooker
    🥷 <b>Ninja</b> — pierces all defences

    🎯 <b>Singletons (7):</b>
    🤦🏼 <b>Suicide</b> — wins only if hanged (night death or survival = loss)
    🔪 <b>Maniac</b> — solo winner (last one alive)
    🐺 <b>Werewolf</b> — transforms into another role based on who hits them
    🧙 <b>Mage</b> — wins by surviving to the end of the game
    🧟 <b>Arsonist</b> — wins by killing 3+ players
    🤹 <b>Crook</b> — wins by surviving (steals a day vote)
    🤓 <b>Snitch</b> — if they target the same player as the Detective, the role is revealed

    <e:item-shield> <b>Items (from shop):</b>
    <e:item-shield> Shield · <e:item-killer-shield> Killer shield · <e:scene-hanging> Vote shield · <e:item-rifle> Rifle
    <e:item-mask> Mask · <e:item-fake-document> Fake document

language-picker-prompt = 🌐 Pick a language:

language-switched = ✅ Language switched

help-private =
    ❓ <b>Help</b>

    <b>Private chat:</b>
    /start — launch the bot
    /profile — profile, inventory, shop (= /inventory, /items)
    /exchange — <e:currency-diamond> diamonds ↔ <e:currency-dollar> dollars
    /stats — my statistics
    /global_top — global leaderboard
    /rules — game rules and full role details

    <b>Playing in a group:</b>
    Add the bot to a group as an admin and start a game with /game.

    📢 News channel: @Mafiauzbot_news

help-group =
    ❓ <b>Group commands:</b>

    /game [bounty] — new game (optional <e:currency-diamond> bounty)
    /start — launch the queued game
    /leave — leave the game
    /extend &lt;sec&gt; — extend registration time
    /stop — cancel the game (admin)
    /settings — settings (admin)
    /give &lt;amount&gt; — gift <e:currency-diamond> diamonds (reply or group inline)
    /stats · /top · /global_top · /profile · /group_stats — statistics

    💡 <b>Note:</b> joining and voting happen via buttons (no separate commands).

rules-summary =
    📖 <b>Mafia game rules</b>

    🏙 <b>Setting:</b> the city is split into two main sides — <b>civilians</b> and <b>mafia</b>. Alongside them, <b>singleton</b> roles play with their own win conditions.

    🎲 <b>Round structure:</b>
      1️⃣ <b>Night</b> — secret actions (mafia kills, Detective checks, Doctor heals, etc.).
      2️⃣ <b>Day</b> — night events announced, town debates.
      3️⃣ <b>Voting</b> — pick a suspect.
      4️⃣ <b>Confirm</b> 👍/👎 — enough "yes" votes hang them.
      5️⃣ <b>Last words</b> — the dead may send a final message to the group.

    <e:scene-voting> <b>Voting</b> happens in DMs — other players don't see your vote (if the admin enables anonymity).

    <e:currency-diamond> <b>Items:</b> <e:item-shield> Shield, <e:item-killer-shield> Killer shield, <e:scene-hanging> Vote shield, <e:item-rifle> Rifle (pierces shields), <e:item-mask> Mask (hides your role), <e:item-fake-document> Fake document (Detective sees "civilian").

    <e:status-trophy> <b>Win conditions:</b>
      • <b>Civilians</b>: wipe out all mafia and singletons.
      • <b>Mafia</b>: equal or outnumber the civilians.
      • <b>Singletons</b> — each role has its own conditions (read more via the button below).

    ⚙️ <b>Settings:</b> group admins use /settings to tweak roles, timings, silence rules and more.

    Tap below to learn exactly how every role works 👇

btn-rules-roles = <e:item-mask> Roles in detail
btn-rules-back = 🔙 Back

rules-pick-team =
    <e:item-mask> <b>Roles by team</b>

    Which side would you like to read about?

rules-team-civilians = Civilians
rules-team-mafia = Mafia
rules-team-singletons = Singletons (solo)

rules-team-civilians-intro =
    👨‍👨‍👧‍👦 <b>Civilians</b>

    Main goal: identify and eliminate the mafia and singletons. Each role has its own toolkit — coordinate carefully so nights aren't wasted.

    Pick a role for full details 👇

rules-team-mafia-intro =
    🤵🏼 <b>Mafia</b>

    Main goal: reduce the civilian count until you match them. Each night the mafia kills one player (Don picks; if no Don, plain Mafia). Special roles — Lawyer, Journalist, Killer — add extra abilities.

    Pick a role for full details 👇

rules-team-singletons-intro =
    🎯 <b>Singleton roles (solo)</b>

    These roles aren't on either team — each has its own win condition. They can rival mafia, civilians, and even other singletons.

    Pick a role for full details 👇

rules-role-detail =
    { $emoji } <b>{ $role }</b>

    { $description }


# === Mafia chat ===

mafia-chat-opened =
    🤵🏻 Mafia night is open.
    You can chat with your teammates:
    { $members }

    <e:scene-last-words> Any text you send here is relayed to other mafia members.


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

crook-stole-vote-dm = <e:item-mask> The Crook deceived you and stole your voting right for today's vote.

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

btn-settings-roles = <e:item-mask> Roles

btn-settings-timings = ⏱ Phase timings

btn-settings-items = <e:item-shield> Items

btn-settings-silence = 🔇 Silence

btn-settings-gameplay = 🎮 Gameplay

btn-settings-lang = 🌐 Language

btn-settings-atmosphere = 📺 Atmosphere media

# --- Section C: Roles sub-menu ---

settings-roles-prompt =
    <e:item-mask> <b>Manage roles</b>

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
    <e:item-shield> <b>Allowed items</b>

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

# --- Section G.2: Display sub-menu ---

btn-settings-display = 🖼 Display

settings-display-prompt =
    🖼 <b>Display options</b>

    What the bot should reveal in chat:

display-show_role_emojis = Show role emojis
display-group_roles_in_list = Group roles in lists
display-anonymous_voting = Anonymous voting
display-auto_pin_registration = Auto-pin registration
display-show_role_on_death = Reveal role on death

# --- Section G.3: Permissions sub-menu ---

btn-settings-permissions = 🔐 Permissions

settings-permissions-prompt =
    🔐 <b>Permissions</b>

    Who can run which commands:

perm-who_can_register = Register for game
perm-who_can_start = Start game
perm-who_can_extend = Extend timer
perm-who_can_stop = Stop game
perm-allow_leave = Allow leaving game

perm-target-all = Everyone
perm-target-admins = Admins only
perm-target-registrar = First registrant
perm-target-creator = Creator only
perm-target-none = Nobody

# --- Section G.4: AFK sub-menu ---

btn-settings-afk = 💤 AFK

settings-afk-prompt =
    💤 <b>AFK thresholds</b>

    Penalty rules for inactive players:

afk-skip_phases_before_kick = Skipped phases before kick
afk-xp_penalty_on_kick = XP penalty on kick
afk-elo_penalty_on_leave = ELO penalty on leave
afk-consecutive_leaves_to_ban = Consecutive leaves before ban
afk-ban_duration_hours = Ban duration (hours)

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
    <e:item-mask> <b>The game has started!</b>

    Tap the button to see your role:

btn-show-my-role = <e:item-mask> Your role

show-role-not-in-game = 🚫 You are not in this game

show-role-no-game = 🚫 No active game right now

dm-stale-game-alert = ⏳ This game has already ended. The old message will be removed.

show-role-alert =
    <e:item-mask> Your role: { $role }

    { $description }

dm-your-role =
    <e:item-mask> <b>You are { $role }!</b>

    { $description }

# Short role blurbs — for the "Your role" alert popup (Telegram ~200-char
# limit on callback alerts). Full prose lives in role-desc-{code}.
role-short-citizen = No special abilities. Join the debate and try to spot the mafia.
role-short-detective = Each night you investigate 1 player and learn whether they're mafia or civilian.
role-short-sergeant = Detective's deputy. If the Detective dies, you take over the night check.
role-short-mayor = Your vote counts as two.
role-short-doctor = Each night heal 1 player, blocking the kill. You can heal yourself only once.
role-short-hooker = Each night put 1 player to sleep, cancelling their night action.
role-short-hobo = Visit a player at night and see who else came to their house.
role-short-lucky = If the mafia attacks, you survive with 50% luck.
role-short-suicide = Win if you get hanged by day. Lose if killed at night.
role-short-kamikaze = If hanged, take 1 player with you to hell.
role-short-don = Tonight you decide who dies. You are the head of the Mafia.
role-short-mafia = Mafia member. At night you help carry out the Don's kill.
role-short-lawyer = Each night protect 1 mafia from Detective checks and hanging.
role-short-journalist = Mafia spy. At night learn whether a player is Doctor/Hobo/Hooker.
role-short-killer = The Doctor can't heal your kill. The Hooker can't put you to sleep.
role-short-maniac = Lone killer. Win by being the last alive. Kill 1 player at night.
role-short-werewolf = Attack a player at night and become their role (Don→Mafia, Detective→Sergeant).
role-short-mage = Mage. Survive to the end and win alone.
role-short-arsonist = Douse targets at night. On the 3rd, they all burn at once.
role-short-crook = Crook. Survive to the end to win. You can vote in someone else's name.
role-short-snitch = Pick a player at night. If the Detective picks the same one — you win!

role-desc-citizen =
    No special abilities — but <b>your power is your voice</b>.
    Stay quiet at night. By day, take part in the debate: read suspects'
    behaviour and vote sharply.

role-desc-detective =
    Each night you check one player and learn whether they are <b>mafia or civilian</b>.
    The mafia will hunt you — stay careful. Tip: don't reveal your findings to
    the whole chat right away, or mafia will pin you fast.

role-desc-sergeant =
    Detective's deputy. If the Detective dies, you inherit their role and start
    checking players yourself. You see the Detective's messages.

role-desc-mayor =
    Mayor. <b>Your vote counts as 2</b> (during day voting and hang confirmation).
    Mafia may target you first — stay alert.

role-desc-doctor =
    Each night you heal one player, saving them from a mafia attack.
    <b>Self-heal works only once</b>. You can't heal the same player two nights in a row.

role-desc-hooker =
    Each night you put one player to sleep, <b>cancelling their night action</b>.
    Sleep the Don — mafia doesn't kill. Sleep the Detective — they don't check.
    You can't sleep yourself.

role-desc-hobo =
    At night you visit one player. You <b>see who else came to visit them</b> —
    which exposes mafia killers. Masked players you can't identify.

role-desc-lucky =
    On a mafia attack, you <b>survive 50% of the time</b>. No choices to make —
    it's pure luck. To the Detective you appear as "civilian".

role-desc-suicide =
    Special condition: <b>if you're hanged by the day vote — you win!</b>
    But if you're killed at night — you lose. Goal: draw suspicion onto yourself.
    To the Detective you appear as "civilian".

role-desc-kamikaze =
    Don't go down alone. <b>If you're hanged — you take one player with you</b>
    (your choice). Taking a mafia member with you counts as a separate win.

role-desc-don =
    Tonight <b>you decide who dies</b>. You are the head of the Mafia.

role-desc-mafia =
    Mafia member. You back the Don at night and join in killing the chosen
    target. The mafia chat helps you coordinate.

role-desc-lawyer =
    Mafia lawyer. Each night <b>you pick one mafia member</b> and shield them
    from a Detective check and from being hanged. You can shield yourself too.

role-desc-journalist =
    Mafia spy. Each night you check one player — you can spot a <b>Doctor, Hobo
    or Hooker</b>. But the Detective and Sergeant you can't identify.

role-desc-killer =
    Mafia's signature assassin. <b>The Doctor cannot save</b> your victim —
    whoever you mark dies. 🛡 Shield and ⛑ Killer shield still block your
    attack, but a 🔫 Rifle in your hands punches through them.
    💃 The Hooker cannot put you to sleep.

role-desc-maniac =
    Solo killer. Your win: <b>be the last alive</b> (everyone else dead).
    Enemy of both mafia and civilians. You kill one player per night.
    To the Detective you appear as "civilian".

role-desc-werewolf =
    Werewolf. At night you attack a player and <b>transform into their role</b>:
    attack the Don → become Mafia, attack the Detective → become Sergeant.
    If another Werewolf attacks you too — both of you die.

role-desc-mage =
    Mage. <b>Survive to the end — you win solo</b>. If attacked, you may
    "forgive" or "kill in return". To the Detective you appear as "civilian".

role-desc-arsonist =
    Arsonist. At night you "set fire" to your targets, but they don't die yet.
    Once you have <b>3 or more marked targets</b>, they all die at once and
    you become the solo winner.

role-desc-crook =
    Crook. <b>Survive to the end — you win solo</b>. Special ability: by day
    you can cast your vote in another player's name — your vote registers as
    if it were theirs.

role-desc-snitch =
    Snitch. At night you pick one player. <b>If the Detective targets that
    exact same player</b>, your role is revealed to the group and you win!
    Masked players can't be identified.

# ===========================================================
# DM-based voting (Wave 6 — voting moved out of group chat)
# ===========================================================

voting-group-prompt-short =
    <e:scene-hanging> Time to find the guilty and pass judgement.
    Voting time: { $seconds } seconds.

voting-go-button = <e:scene-voting> Cast vote

voting-dm-prompt =
    <e:scene-hanging> <b>Time to find the guilty!</b>

    Who do you think should hang?

vote-recorded-dm-confirm = ✅ Your vote: <b>{ $target }</b>

vote-skipped-confirm = ✅ You chose "Nobody".

# Comedic rumor-style alerts for invalid voters in HANGING_CONFIRM
vote-dead-alert = <e:status-death> You're dead, you cannot vote! Even your ghost is silent.
vote-not-in-game-alert = 😴 You're not in this game. We'll call you for the next one!
vote-already-voted-alert = ✋ You already voted!

# AFK comedic last-words
afk-last-words =
    Someone in town heard { $role } { $mention } shout before dying:
    "I'm never sleeping during the gaaaaaame again!"

# Per-player game-end DM
game-end-dm-win =
    <e:status-trophy> <b>Congratulations, you won!</b>

    <e:item-mask> Role: { $role }
    ⭐ XP: +{ $xp }
    📊 ELO: { $elo_delta }
    <e:currency-dollar> Reward: { $dollars }$

game-end-dm-loss =
    <e:status-death> <b>No luck this time.</b>

    <e:item-mask> Role: { $role }
    ⭐ XP: +{ $xp }
    📊 ELO: { $elo_delta }
    <e:currency-dollar> Money: { $dollars }$
