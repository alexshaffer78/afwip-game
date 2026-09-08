# AFWIP — Game Overview

*Air Force Wargame: Indo-Pacific (AFWIP)* is a two-player, near-future air and
multi-domain wargame set in the Indo-Pacific. One player is the **United States
(US, blue)**, the other the **People's Republic of China (PRC, red)**. It is an
introduction to airpower and multi-domain combat: alongside aircraft and ships,
you wield **cyber, space, electronic-warfare, and special-operations** effects.
This overview orients you; [`02_rules_reference.md`](02_rules_reference.md) is
the detailed authority.

## The board

A single map of **range bands** between the two homelands:

```
US_STANDOFF · US_AIRBASE · US_CONTINGENCY_LOCATION | BAND_A BAND_B BAND_C BAND_D BAND_E | PRC_AIRBASE · PRC_STANDOFF
```

- The five center bands (`BAND_A`..`BAND_E`) are the contested airspace. Each
  side numbers them from its own edge (US: Band 1 = `BAND_A` … Band 5 = `BAND_E`;
  PRC mirrors it). See the geometry table in
  [`04_state_encoding.md`](04_state_encoding.md).
- Each side has an **Airbase** (its home), a **Standoff** container (for bombers
  and AEW firing/loitering from deep rear), and the US additionally has a
  **Contingency Location (CL)** — a dispersed operating site (Agile Combat
  Employment).
- Each side tracks a **Cyber Rate** (0–4) and an **Intel Track**
  (Normal/Advantage) on its side of the board.
- **Range** between locations is just the count of bands between them.

## What you command

- **Squadron Cards** generate **tokens** onto the board. Each card takes 2 hits
  to destroy and generates a fixed complement when activated: **4** for a
  fighter or attack-drone squadron, **2** for a recon-drone squadron, and **1**
  for a bomber, AEW, or ADA squadron. (Only the B-52 has two squadron cards —
  one token each; see [`03_tokens_and_cards.md`](03_tokens_and_cards.md).)
- **Enabler Cards** deliver multi-domain effects: maritime strikes and ships,
  land fires, space, cyber, electronic warfare, special operations, extra air
  support, base defense. Some generate tokens; many are one-shot effects,
  responses, or enduring buffs.
- **Tokens** are the units that actually move and fight: fighters, bombers,
  UAS (drones), AEW (airborne radar), EW aircraft, ADA (ground air-defense), and
  ships. Each has printed stats — move range, acquire range, attack ranges and
  thresholds, missile defense — catalogued in
  [`03_tokens_and_cards.md`](03_tokens_and_cards.md).

## How you win

You pick a **Mission Card** (hidden until game end) that defines how you score
**Victory Points (VP)**; the higher total after all ATO cycles wins. Missions
reward different things — destroying units (Attrition/Interdiction), preserving
force (Economy of Force), non-kinetic dominance, killing enemy air on the ground
(Counter-Intervention), etc.

There is one **sudden-death** condition: reaching **Cyber Rate 4 immediately
wins the game**, regardless of VP.

## Structure of play

A game is a **Campaign** of one or more **ATO Cycles** (Air Tasking Order
cycles). The predefined campaigns:

| # | Name | ATO cycles | Notes |
|---|---|---|---|
| 1 | Meeting Engagement | 1 | Intro. No enablers; a normal Standard squadron draft that **must include** the US F-16 / PRC J-10 card; Attrition + Standard only. |
| 2 | Tournament | 2 | Balanced/short. Attrition + Standard only; initiative alternates; no bid sacrifices. |
| 3 | Prolonged Combat | 5 | Everything allowed; the deep game. |
| 4 | The World Watches | 2 | Bans long-range missiles/SOF/bombers; +1 VP per air kill (max +2/ATO); ATO-2 initiative to whoever *lost* more tokens. |
| 5 | Reserves | 2 | No 5th-gen, no bombers, no PRC long-range ADA; +1 VP per intact squadron at campaign end. |

### An ATO cycle, in order

1. **Setup / Draft.** Each side (this repeats every cycle) picks a **Posture**
   (sets how many squadron and enabler cards you get, plus restrictions/bonuses),
   drafts that many **Squadron Cards** (deployed face-down to Airbase or CL) and
   **Enabler Cards** (kept hidden in hand). Each side drafts from its **own
   separate deck** (54 US / 54 PRC cards); there is **no shared or contested
   pool** — the opponent can't take or deny your cards, and you draft your whole
   roster in one sequence, not alternating with them. See
   [`02_rules_reference.md`](02_rules_reference.md#setup-and-drafting).
2. **Bid for Initiative.** Each side rolls a D4 (optionally sacrificing enablers
   for +1 each, except in Tournament). Winner takes **Intel Advantage**, chooses
   who goes first, and gets one **Cyber-Rate** raise attempt.
3. **Play Intel.** Each side rolls to see some of the opponent's hand (winner
   rolls at advantage); at least one enemy card always stays hidden.
4. **Turns.** Players alternate turns until **both pass in succession**. On your
   turn you may play **one Enabler**, and either **activate one squadron** *or*
   do a **Move-Acquire-Shoot** action — see below.
5. **End / Cleanup.** Score end-of-ATO mission terms, clear the board, recycle
   cards for the next cycle. After the last cycle, reveal missions and total VP.

### A turn

On your turn you may do **both** of the following (in either order), or pass:

- **Play one Enabler Card** (optional, at most one per turn). Some enablers are
  *responses* you can also play on the opponent's turn.
- **One of:**
  - **Activate a Squadron** — flip it face-up and generate its tokens onto the
    board. *This ends your turn.*
  - **Move-Acquire-Shoot (MAS)** — up to **one Move, one Acquire, and one Shoot**,
    each at most once, **in any order**, with any of your tokens. You may omit
    any of them.

**Move** a token up to its move range. **Acquire** flips a face-down enemy token
face-up (roll ≥ its acquisition value) so you can target it. **Shoot** an
acquired enemy token (air or surface) or an enemy base. Combat is D4-based;
details, Winchester (out-of-ammo), and Missile Defense are in the rules doc.

## Where to go next

- To reason about a specific position, read
  [`04_state_encoding.md`](04_state_encoding.md) (the pasted-state format) and
  keep [`03_tokens_and_cards.md`](03_tokens_and_cards.md) handy for unit stats.
- For legality and edge cases, [`02_rules_reference.md`](02_rules_reference.md).
- For *how to advise*, [`05_advisor_guide.md`](05_advisor_guide.md).
