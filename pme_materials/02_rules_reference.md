# AFWIP Rules Reference (as the digital app plays)

This is the authoritative rules reference **for the AFWIP web app**. It reflects
how the app's engine actually resolves things, including the design rulings that
supersede or clarify the printed rulebook. Where a ruling differs from the paper
game it is flagged **[app ruling]**. When advising a player of the app, follow
this document; never suggest an action the app's listed choices don't offer.

Contents: [Setup & drafting](#setup-and-drafting) · [Dice](#dice) ·
[Turn structure](#turn-structure) ·
[Activating squadrons](#activating-a-squadron) · [Move](#move) ·
[Acquire](#acquire) · [Shoot](#shoot) · [Winchester](#winchester) ·
[Missile Defense](#missile-defense) · [Enablers](#enabler-cards) ·
[Cyber & Intel](#cyber-and-intel) · [Bases & damage](#bases-and-damage) ·
[End of ATO / carryover](#end-of-ato-and-carryover) · [Scoring](#scoring-by-mission)
· [Campaigns](#campaign-specifics)

## Setup and drafting

At the start of each ATO cycle, each side privately builds its force: pick a
**Posture** (which sets how many squadron and enabler cards you get), then draft
that many **Squadron Cards** and **Enabler Cards**.

**Decks are separate and NOT contested — this is important.**

- **Each side has its own deck.** There are **54 US cards and 54 PRC cards**, two
  distinct sets. You draft your posture, squadrons, and enablers **only from your
  own side's cards**.
- **The opponent cannot take, deny, or compete for your cards.** There is **no
  shared or contested draft pool**. Choosing (say) the AEW squadron does not let
  the enemy grab your F-22 squadron — your cards are always yours, and every one
  of your surviving cards remains available to you in later cycles.
- **You draft your whole roster in one sequence, not alternating pick-by-pick
  with the opponent.** In the app, one side completes its entire draft (posture →
  squadrons → placement → enablers), then the other side drafts theirs. There is
  no interleaving where the enemy picks between your picks. (The only per-cycle
  contest is the separate **Bid for Initiative**, a D4 roll — not a card draft.)
- **Order within your own draft doesn't cost you anything.** Because nothing is
  contested, picking AEW "first" or "last" is irrelevant to what you can still
  take — draft in whatever order is convenient; you get every card you choose up
  to the posture's limits.

Squadron cards are deployed **face-down** to the Airbase or (US only) a
Contingency Location; enablers go to hand, hidden. Squadrons and enablers are
re-drafted every cycle — see [End of ATO / carryover](#end-of-ato-and-carryover).

## Dice

All resolution uses a **four-sided die (D4)**. A roll can be at:

- **Normal** — one die.
- **Advantage** — roll two dice, keep the **higher**.
- **Disadvantage** — roll two dice, keep the **lower**.

Advantage and disadvantage **cancel one-for-one and never stack**: one of each
= a normal roll; two advantage + one disadvantage = a single net advantage.

Some tokens/effects add a flat **bonus** to a roll (e.g. AEW `+2`, most radars
`+1`); the bonus is added after the die is chosen. A target's **acquisition
value** or a shooter's **threshold** is the number the final roll must **meet or
exceed**.

## Turn structure

Players alternate. On your turn, in either order, you may:

1. **Play one Enabler Card** (optional; max one per turn on your own turn).
2. **One of:** *Activate a Squadron* **or** a *Move-Acquire-Shoot* action.

Then your turn ends. **When both players pass in succession, the ATO cycle
ends.** Passing is doing nothing; taking any action (including just playing an
enabler) breaks the pass streak.

**[app ruling] Move-Acquire-Shoot may be taken in any order, each once.** You
may shoot then move then acquire, or any order — the only limit is at most one
Move, one Acquire, and one Shoot per turn, and you may use different tokens for
each. You may omit any of them.

Activating a squadron **ends the turn** and is **mutually exclusive** with
Move-Acquire-Shoot that turn (you can't both generate forces and maneuver in the
same turn).

## Activating a Squadron

Flip a face-down Squadron Card face up and generate its tokens onto the board:

- **Fighters** spawn on the side's front band (`BAND_A` for US, `BAND_E` for
  PRC). **UAS (drones)** may spawn on any band. **AEW and Bombers** spawn on the
  front band **or** the side's Standoff container. **ADA** spawns on the Airbase
  or CL where the squadron sits. **Carrier J-15s** (from the Shandong enabler)
  may spawn on any band.
- **Contingency Location generation is risky:** a squadron activated from the US
  CL rolls a D4 — only that many of its aircraft generate (`min(roll, size)`);
  the rest stay **grounded** on the card (vulnerable, can't act). Exceptions that
  generate **all** aircraft with no roll: the **ACE** posture, or the **Flying
  Crew Chief** enabler naming that squadron. The roll only bites **multi-token
  squadrons** (fighters/drones): a **single-token squadron** (bomber, AEW, ADA)
  always generates its one token from the CL (`min(roll, 1) = 1`), so the CL roll
  is irrelevant for it.
- **[app ruling] Token losses persist:** a squadron re-fields only its surviving
  complement (`full_count − tokens_lost`). Destroyed tokens do not come back
  except via specific enablers.
- **[app ruling] Recovered-squadron reactivation is risky:** a squadron brought
  back by Rapid Resupply returns to the airbase flagged "recovered". When you
  activate it, roll a D4 — on a **1** every aircraft is "broken" (surrendered to
  the enemy on the ground; the card itself is not scored and is removed);
  **2–4** activates normally at full surviving strength.

## Move

Move **one** token per turn up to its **move range** (in bands). Notes:

- Grounded and Winchester tokens can't take a voluntary move.
- **[app ruling] Ships move** like any token, up to their move range of **1**,
  among the on-map bands (they can't enter base/standoff bands).
- A squadron token moved **back onto its own base** lands and grounds for the
  rest of the ATO (it re-arms next cycle). If that base's card is already
  destroyed, the token is lost.
- Placing a token via an Enabler Card, or a Winchester token returning to base,
  is **not** a move action (it's free).

## Acquire

Attempt to identify one face-down enemy token so you can shoot it. With one of
your tokens that has an acquire range, pick an enemy token within that range and
roll:

- Success if the roll (+ the acquirer's acquire bonus) **≥ the target's
  acquisition value**. On success the target flips **face-up** and stays
  identified for the rest of the ATO.
- **AEW and Recon UAS roll twice** per acquire attempt (take the first success);
  AEW also has a **+2** bonus and range 3, making it the premier sensor.
- **Grounded tokens cannot be acquired**, with one exception: **ADA** can always
  be engaged on its base (it must be acquired then shot; a base strike never hits
  it — see below).
- Enemy tokens **on a base or in Standoff** may be engaged **without**
  acquisition (bases and standoff aircraft are open targets for surface fire).
- Several enabler cards acquire tokens directly (cyber/space/SOF reconnaissance).

## Shoot

Shoot **one** token per turn (or via certain enablers). Three kinds:

**Air-to-air** (`shoot_air`): an air token with an air-attack value fires at an
**acquired** enemy **air** token within its air-attack range. Roll ≥ the
attacker's air threshold to destroy it. Air-to-air is a **single-hit kill** (no
damage roll).

**Surface vs a ship / standoff aircraft** (`shoot_surface` at a token): fire at
an **acquired** enemy **ship** (or an aircraft sitting in a Standoff container).
Ships are single-hit kills. A hit on a standoff aircraft lands on its Squadron
Card (2 hits kills the card and everything on it).

**Base strike** (`shoot_surface` at a band): fire at an enemy **Airbase / CL**
within surface-attack range — **no acquisition needed**. On a hit:

- **Exploding-die** tokens (B-52, H-6K, all the guided-missile ships, the
  Flotilla) roll a D4 for **damage**; non-exploding tokens deal a flat **1**.
- You **distribute** the damage across valid targets at that base: enemy Squadron
  **Cards** deployed there (2 hits each), any cardless enemy tokens there
  (1 hit), the enemy **airbase VP boxes** (3 total, worth VP), and an **Infantry
  Battalion** marker if present.
- **[app ruling] Base strikes target Squadron *Cards*, not their grounded
  flight tokens** (the tokens die with the card). **ADA is never hit by a base
  strike** — it must be acquired and shot like an aircraft.
- **Contingency Location:** only **one** Squadron Card (and its assets) may be
  hit per attack; there are **no VP boxes** at a CL and no spillover — excess
  damage is lost.

**[app ruling] Advantage/disadvantage applies to the hit (to-hit) roll only —
except Missile Defense.** For token strikes, buffs like EW, EC-130 jamming, or
the ACE posture bias the **hit** roll; the exploding-die **damage** roll is a
plain single die. The **one exception** is Missile Defense, which applies
disadvantage to **both** the hit and damage rolls. (Enabler-card strikes always
roll a plain single die for damage — see Enablers.)

## Winchester

A token is **Winchester** when out of ammo. It is driven by the **natural
to-hit (attack) roll ONLY** — the damage roll never affects ammo:

- Most tokens go Winchester on a roll **< 4** (a 4 means it didn't need all its
  weapons). **Attack UAS** go Winchester on **1–2** (they keep ammo on 3–4).
- **ADA, AEW, Recon UAS, EC-130 never go Winchester** (no threshold).
- **Ships** track **salvos** instead: each shot spends one salvo of the relevant
  magazine (air salvos = 4, surface salvos = 1) unless the natural roll is a 4; a
  ship is Winchester only when both magazines are empty. A ship can only provide
  missile defense while it has air salvos left.
- **[app ruling] An auto-hit strike never causes Winchester.** When
  **Forward Observers** (card 13) makes a surface/base strike auto-hit, there is
  **no to-hit roll**, so it counts as a **clean hit — equivalent to a natural 4**:
  the attacker does **not** go Winchester (and a ship spends **no** salvo), no
  matter what the damage roll is. This holds for exploding-die attackers too
  (B-52, H-6K, ships) — the damage die is irrelevant to ammo.

At the **start of your turn**, your Winchester **air** tokens return to their
Squadron Card (grounded, re-armed next cycle) — or, if that card is destroyed,
they're surrendered to the enemy. Winchester **ships** move off the board (out of
play, not destroyed). Returning to base is free (not a move).

**[app ruling] Winchester fighter relaunch:** when a **fighter** (only) returns
Winchester to a still-live squadron, you may spend your turn attempting a
relaunch — roll a D4: **1** = "broken" (destroyed on the ground, surrendered to
the enemy); **2–4** = relaunches as a fresh sortie (re-armed, no longer acquired,
back at your front band). A relaunch **ends the turn** like an activation.

## Missile Defense

An attack that crosses the **Weapon Engagement Zone (WEZ)** of an enemy air-
defense unit may be defended:

- **ADA** covering the shot path imposes **disadvantage automatically** (no cost,
  no declaration) on the attacker.
- A **ship** may be **declared** as a defender (`MD_DECLARE`) if the shot crosses
  its WEZ and it has air salvos left; declaring spends one air salvo and imposes
  disadvantage. It must be declared **before** the attacker rolls.
- **[app ruling] Missile Defense applies to air-to-air attacks too**, not just
  surface/base strikes.
- Disadvantage from Missile Defense falls on **both** the hit and damage rolls.
- **Unblockable** effects bypass Missile Defense entirely: the PRC "Unblockable"
  missile cards (Hypersonic, Maritime Strike Cruise) and the two SOF direct-
  action strikes (Sea Dragons, PLANMC). Cards like **Decoy Warheads** / **Air
  Launched Decoy** can *cancel* a declared missile-defense attempt.

## Enabler Cards

You may play **one** enabler on your own turn (some are also **responses** you
can play on the opponent's turn when their trigger fires). Enablers cover:

- **Token generators** — ships (DDG/CG/Flotilla), carrier J-15s, EC-130, ADA.
- **Base/anti-ship strikes** — HIMARS, Tomahawk, Ballistic/Cruise/Hypersonic
  missiles, submarine strikes, Marine Littoral, SOF raids.
- **Cyber** — raise your own rate, degrade/cancel the enemy's, remove enemy
  tokens or force discards, acquire tokens, counter-UAS.
- **Space / EW** — enduring advantage/disadvantage biases, cancels, recon.
- **Air support / mobility** — refueling (extra squadron), aerial recovery of
  lost aircraft, crew chief, reserves, elite pilots, munitions upgrade.
- **Base defense** — Red Horse / Resilient Bases (cancel a base attack), Infantry
  Battalion (SOF shield), missile defense generators.

Key mechanics:

- **[app ruling] Enabler-card strike damage is always a single plain die.**
  Advantage/disadvantage on an enabler strike affects only its hit/gate roll.
  Auto-hit / unblockable strikes have no roll for buffs to touch.
- **"Airbase"-worded strikes fill only the 3 VP boxes** (HIMARS, Tomahawk, Sea
  Dragons, PLANMC) — they never damage Squadron Cards. "Base"-worded strikes
  (Ballistic/Cruise/Hypersonic) distribute across cards + VP boxes like a bomb
  run.
- **Enduring** enablers (red pushpin) bias rolls for the whole ATO cycle
  (Improved Munitions, EW Spoofing, Defensive/Offensive EW, Space-Based EW,
  Badger Surge, Munitions Upgrade).
- **Response** enablers (yellow bolt) fire off a trigger: recover a just-lost
  aircraft, cancel a base attack, cancel a cyber/space/SOF/submarine/mobility
  card, cancel a hit or a missile-defense attempt, regenerate a wiped squadron
  (Reserves), re-roll a UAS acquire (UAS Proliferation).
- A **cancel** fully reverses the cancelled card's effect (damage, kills,
  acquisitions, cyber gains, placements), not just the play-log.
- **Recovered / regenerated units re-enter face-down (unacquired).** A recovered
  aircraft (Personnel Recovery / Quick-Turn), a regenerated squadron (Reserves),
  a Rapid-Resupply revival, or a Winchester fighter relaunch all come back as a
  **fresh sortie the enemy must re-acquire** — even if the unit was acquired
  before it was lost. (A *cancelled* attack is different: it undoes the shot as if
  it never happened, so any prior acquisition is preserved.)

See [`03_tokens_and_cards.md`](03_tokens_and_cards.md) for every card by id.

## Cyber and Intel

- Each side starts at **Cyber Rate 1**. To raise it, roll a D4 ≥ the access value
  between the current and next rate: **0→1 needs 2, 1→2 needs 3, 2→3 needs 4,
  3→4 needs 4.** Cyber cards and the initiative winner's bonus give raise
  attempts.
- **Reaching Cyber Rate 4 immediately wins the game.**
- Many cyber effects scale with your rate (acquire/remove N = rate; Joint
  Offensive Cyber = 2× rate).
- **Intel** (Normal/Advantage) marks the initiative winner; it gives an advantage
  roll during the Play Intel peek and matters for a few effects.

## Bases and damage

- The **Airbase** has **3 VP-damage boxes**. Filling them scores VP for the
  attacker; **[app ruling] they are permanent** (carry across ATO cycles, scored
  once each) and do **not** reduce base function.
- The **Contingency Location has no VP boxes** and no independent damage track.
- A **Squadron Card** takes **2 hits** to destroy; destroying a card also
  destroys every token still attached to it (grounded or never-generated).
- **[app ruling] Card partial damage resets each ATO cycle** (a card dinged for
  one box starts the next cycle fresh); a **fully destroyed** card is permanent
  and scored for the enemy.
- The **Infantry Battalion** enabler (US) sits on a base with 2 damage boxes and
  makes squadrons there immune to SOF raids until it's destroyed; the attacker
  scores nothing for damaging or destroying it.

## End of ATO and carryover

At end of ATO (both pass): airborne squadron tokens land on their cards (any
landing on a destroyed card are lost), end-of-ATO mission terms score, then the
board clears. Carryover into the next cycle:

- **Destroyed tokens stay destroyed** and scored (re-field fewer next cycle).
- **Partial card damage resets**; **destroyed cards stay out** (permanent).
- **Airbase VP boxes persist** (permanent, scored once).
- **Cyber Rate, Intel, and VP persist.**
- **Squadrons and enablers re-draft every cycle** (from your own deck — see
  [Setup & drafting](#setup-and-drafting)): surviving squadrons can be re-fielded
  (and re-placed Airbase/CL); played single-use enablers are gone for the
  campaign, unplayed single-use and all multi-use enablers return to **your**
  pool to be draftable again.

## Scoring by mission

VP comes from your (hidden) Mission Card. Capture-based missions score at game
end from the destroyed-unit log; the rest accrue each turn/ATO.

- **Attrition (US 51 / PRC 105):** +2 per enemy **Squadron Card**; +3 per **Ship,
  Bomber, ADA, AEW** token; +1 per any other token.
- **Interdiction (US 52 / PRC 106):** +4 per **Bomber, AEW, or Squadron Card**;
  +3 per **Ship or ADA**; +2 per any other token.
- **Economy of Force (US 50 / PRC 104):** +2 per drafted unit **fielded this ATO
  but not used** — a Squadron Card on the board not activated, or an unplayed
  token-generating Enabler still in hand. (Scored each ATO.)
- **N-K Dominance (US 53):** +3 × your **Cyber Rate**, plus +1 per EW / Cyber /
  Space / SOF card you played. (Scored each ATO.)
- **Enforce Rule of Law (US 54):** +2 per **Squadron activated** and +1 per token
  generated by an Enabler — scored **each turn**.
- **Three Dominances (PRC 107):** +2 × your **Cyber Rate**; +3 per **naval unit
  on the board** (ships + carrier J-15s); +1 per **naval enabler** played; +1 per
  **intact squadron** (fielded this ATO with zero token losses). (Scored each
  ATO.)
- **Counter-Intervention (PRC 108):** +3 per enemy **air token destroyed on the
  ground** (fighter/UAS/bomber/AEW); +1 per **PLARF** card played.
- **Universal:** +1 per enemy **airbase VP box** you hit (once each).

## Campaign specifics

- **Campaign 1 (Meeting Engagement):** 1 ATO, no enablers, Attrition + Standard
  only. You draft squadrons normally under the Standard posture (up to 4,
  near-max ≥3), but the draft **must include** the US **F-16** (#10) / PRC
  **J-10** (#60) card — it's a required pick, not the only one.
- **Campaign 2 (Tournament):** 2 ATOs, Attrition + Standard only. **You bid for
  initiative only in ATO 1 and cannot sacrifice cards; ATO-2 initiative goes to
  whoever did *not* hold it in ATO 1.**
- **Campaign 3 (Prolonged Combat):** 5 ATOs, everything allowed.
- **Campaign 4 (The World Watches):** 2 ATOs. **Bans** long-range missile & SOF
  enablers and long-range bomber squadrons. **+1 VP per enemy squadron wiped out
  entirely in the air** (max +2/ATO). **ATO-2 initiative goes to the side that
  *lost* more of its own tokens** in ATO 1.
- **Campaign 5 (Reserves):** 2 ATOs. **Bans** 5th-gen aircraft, bombers, and PRC
  long-range ADA. **+1 VP per intact Squadron Card at campaign end.**
