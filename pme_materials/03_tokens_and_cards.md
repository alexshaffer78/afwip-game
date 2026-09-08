# AFWIP Tokens & Cards Reference

Look here when the pasted state names a unit or card. Stats are the values the
app's engine uses. Ranges are in **bands**. "AV" = acquisition value (roll an
enemy needs to acquire it; higher = stealthier). Thresholds are "roll ≥ N".

## How to read attack stats

- **Gen** — how many tokens you get **each time the unit is fielded**: per
  **squadron card** for squadron tokens, or per **enabler card** for
  enabler-generated tokens (EC-130, US ADA, ships, carrier J-15). It is **not**
  the number of copies of that unit in the game. Example: each B-52 **squadron
  card** generates **1** B-52 — and there are **two** B-52 squadron cards
  (#2 and #7), so up to 2 B-52 tokens can be in play, one per activated card.
- **Air atk** `range/thr` — air-to-air: max range and the to-hit threshold.
- **Surf atk** `range/thr` — surface/base attack; **✸** = exploding die (rolls
  D4 for damage instead of a flat 1).
- **Acq** `range(+bonus)×rolls` — sensor: acquire range, bonus, and how many
  dice per attempt (AEW/Recon roll ×2).
- **MD** = provides Missile Defense. **Winch** = Winchester threshold (roll below
  it → out of ammo; "—" = never goes Winchester; ships use salvos).

## US Tokens

| Token | Gen | Move | Acq | Air atk | Surf atk | MD | Winch | AV |
|---|---|---|---|---|---|---|---|---|
| **F-22** | 4 | 2 | 2(+1) | 1 / 2 | — | — | 4 | **4** |
| **F-35A** | 4 | 2 | 2 | 1 / 2 | 1 / 2 | — | 4 | **4** |
| **F-15C** | 4 | 2 | 2 | 1 / 2 | — | — | 4 | 2 |
| **F-15E** | 4 | 2 | 2 | 1 / 2 | 1 / 2 | — | 4 | 2 |
| **F-16C** | 4 | 2 | 2 | 1 / **3** | 1 / 2 | — | 4 | 2 |
| **B-52** (bomber) | 1 | 1 | 2 | — | **6 / 2 ✸** | — | 4 | 2 |
| **AEW** | 1 | 1 | 3(+2)×2 | — | — | — | — | 2 |
| **EC-130** (EW) | 1 | 1 | — | — | — | — | — | 3 |
| **ADA** (ground) | 1 | 0 | 2(+1) | 1 / 2 | — | ✔ | — | 2 |
| **Attack UAS** (drone) | 4 | 1 | 2 | — | 1 / **3** | — | **3** | 3 |
| **Recon UAS** (drone) | 2 | 1 | 2(+1)×2 | — | — | — | — | 3 |
| **DDG 115 / DDG 81** (ship) | 1 ea | 1 | 2(+1) | 3 / 2 | **3 / 2 ✸** | ✔ | salvos 4air/1surf | 2 |

- **The B-52 has two squadron cards** (69th #2, 23rd #7); each generates **1**
  B-52 (so at most 2 B-52 tokens, one per activated card). Every other US
  squadron token type has a single card. US **ADA** and **EC-130** come from
  enabler cards / the Hedgehog posture (1 token each), not from a squadron.
- B-52 and AEW spawn on the front band **or US Standoff**. ADA spawns on the
  Airbase/CL. Fighters spawn on `BAND_A`.
- Stealth (F-22/F-35, AV 4) is hard for the enemy to acquire; F-16 has a weak
  air threshold (needs 3+).

## PRC Tokens

| Token | Gen | Move | Acq | Air atk | Surf atk | MD | Winch | AV |
|---|---|---|---|---|---|---|---|---|
| **J-20B** (5th-gen) | 4 | 2 | 2(+1) | 1 / 2 | — | — | 4 | **4** |
| **J-16** | 4 | 2 | 2 | 1 / 2 | 1 / 2 | — | 4 | 2 |
| **J-15** (carrier) | 4 | 2 | 2 | 1 / 2 | 1 / 2 | — | 4 | 2 |
| **J-10** | 4 | 2 | 2 | 1 / **3** | 1 / 2 | — | 4 | 2 |
| **JH-7** | 4 | 2 | 2 | 1 / **3** | 1 / 2 | — | 4 | 2 |
| **H-6K** (bomber) | 1 | 1 | 2 | — | **6 / 2 ✸** | — | 4 | 2 |
| **AEW** | 1 | 1 | 3(+2)×2 | — | — | — | — | 2 |
| **Long-Range ADA** | 1 | 0 | 2(+1) | **3** / 2 | — | ✔ | — | 2 |
| **Mid-Range ADA** | 1 | 0 | 2(+1) | 1 / 2 | — | ✔ | — | 2 |
| **Attack UAS** (drone) | 4 | 1 | 2 | — | 1 / **3** | — | **3** | 3 |
| **Recon UAS** (drone) | 2 | 1 | 2(+1)×2 | — | — | — | — | 3 |
| **Nanning #162 / Dalian #105** (ship) | 1 ea | 1 | 2(+1) | 3 / 2 | **3 / 2 ✸** | ✔ | salvos 4air/1surf | 2 |
| **Missile Boat Flotilla** (ship) | 1 | 1 | 2 | — | **2 / 3 ✸** | — | salvos —/1surf | 3 |

- J-20B is the PRC stealth fighter (AV 4). Long-Range ADA reaches 3 bands (strong
  area denial). The carrier J-15 comes from an enabler and spawns on any band.

## Squadron Cards

Each squadron card takes **2 hits**. US 1–10, PRC 55–64. The count in parentheses
is what **one card** generates when activated: fighter/attack-drone squadrons
field **4** tokens, recon-drone squadrons **2**, and bomber / AEW / ADA squadrons
**1**. (The B-52 is the only token with two squadron cards — see below.)

**US:** 1 = 124th Attack Sq (4× Attack UAS) · 2 = 69th Bomb Sq (**1× B-52**) ·
3 = 99th Recon Sq (2× Recon UAS) · 4 = 960th AEW Sq (1× AEW) · 5 = 90th Fighter Sq
(4× F-22) · 6 = 44th Fighter Sq (4× F-15C) · 7 = 23rd Bomb Sq (**1× B-52**) ·
8 = 34th Fighter Sq (4× F-35A) · 9 = 391st Fighter Sq (4× F-15E) · 10 = 480th
Fighter Sq (4× F-16C). — **Two** B-52 squadron cards (#2, #7), one B-52 each.

**PRC:** 55 = UAS Air Regiment (4× Attack UAS) · 56 = 3rd Air Defense Bde
(1× Mid-Range ADA) · 57 = UAS Air Bde (2× Recon UAS) · 58 = AEW Regiment (1× AEW) ·
59 = 5th Air Defense Regt (1× Long-Range ADA) · 60 = 124th Air Bde (4× J-10) ·
61 = 8th Bomber Div (1× H-6K) · 62 = 5th Air Bde (4× J-20B) · 63 = 26th Air Bde
(4× J-16) · 64 = 126th Air Bde (4× JH-7).

## Enabler Cards

Type key: **1U** single-use, **MU** multi-use, **Resp** response (yellow bolt),
**End** enduring (red pushpin). Effects summarized; the rules doc has the
mechanics.

### US enablers (11–44)

| # | Name | Type | Effect |
|---|---|---|---|
| 11 | AC-130 Gunship Attack | 1U Resp | Cancel a PRC SOF card. |
| 12 | Personnel Recovery | 1U Resp | Recover a just-lost US aircraft to Band 1 (not destroyed); it re-enters fresh and **face-down** — the enemy must re-acquire it. |
| 13 | Forward Observers | 1U Resp | Your next surface strike auto-hits (no to-hit roll → counts as a clean hit, so the shooter never goes Winchester). |
| 14 | SOF Reconnaissance | 1U | Roll D4, acquire that many PRC tokens; on a 4, +1 Cyber. |
| 15 | SOF Cyber Infiltration | 1U | Roll to raise your Cyber Rate. |
| 16 | Aerial Refueling | MU | Place one extra Squadron beyond the posture limit. |
| 17 | Quick-Turn Mobility | 1U Resp | Recover a just-lost US aircraft (like Personnel Recovery; returns face-down). |
| 18 | Rapid Resupply | 1U | Recover any discarded Squadron/Enabler card; usable immediately. |
| 19 | Improved Munitions | 1U End | US air-to-air rolls at advantage this ATO. |
| 20 | Flying Crew Chief | MU End | One CL squadron generates max aircraft (no roll) this ATO. |
| 21 | Cyber Reconnaissance | MU | Acquire PRC tokens equal to your Cyber Rate. |
| 22 | Cyber Infiltration | MU | Roll to raise your Cyber Rate. |
| 23 | Defensive Cyber | MU Resp | Cancel a PRC cyber card (as response) OR degrade PRC Cyber by 1. |
| 24 | Offensive Cyber | 1U | Remove PRC tokens = Cyber Rate, OR force that many enabler discards. |
| 25 | Cyber Counter-UAS | 1U | Destroy PRC UAS tokens = your Cyber Rate. |
| 26 | EW Spoofing | 1U End | All PRC **acquisition** rolls at disadvantage this ATO. |
| 27 | Defensive EW | 1U End | All PRC **attack** rolls at disadvantage this ATO. |
| 28 | Offensive EW | 1U End | All US **attack** rolls at advantage this ATO. |
| 29 | Air Launched Decoy | 1U Resp | Cancel a PRC hit, or a PRC missile-defense attempt. |
| 30 | EC-130 Compass Call | 1U | Generate EC-130; PRC attacks in its band at disadvantage. |
| 31 | Space Reconnaissance | MU | Roll D4, acquire that many PRC tokens. |
| 32 | Counter Space | 1U Resp | Cancel a PRC space card. |
| 33 | Joint Defensive Cyber | 1U | Degrade PRC Cyber Rate by 2. |
| 34 | Joint Offensive Cyber | 1U | Remove PRC tokens = 2× your Cyber Rate. |
| 35 | Space-Based EW | 1U End | PRC **base**-attack rolls at disadvantage this ATO. |
| 36 | Land-Based Missile Defense | 1U | Generate 1 ADA on the US Airbase/CL. |
| 37 | Maritime Missile Defense | 1U | Generate DDG 81 in any band. |
| 38 | Red Horse Squadron | 1U Resp | Cancel all damage from a PRC attack on your base. |
| 39 | Resilient Bases | 1U Resp | Cancel all damage from a PRC attack on your base. |
| 40 | Infantry Battalion | 1U | Place on a base; shields squadrons there from SOF (2 boxes). |
| 41 | HIMARS | 1U | Roll 2+, then D4 damage to the PRC **airbase** (VP boxes only). |
| 42 | Tomahawk Strike | 1U | Generate DDG 115; roll 2+, D4 to the PRC **airbase** (VP boxes). |
| 43 | Submarine Strike | MU | Auto-kill a PRC surface combatant, OR (response) cancel a PRC sub card. |
| 44 | Marine Littoral Regiment | 1U | Auto-kill a PRC surface combatant. |

### PRC enablers (65–98)

| # | Name | Type | Effect |
|---|---|---|---|
| 65 | Anti-Access/Area Denial | 1U Resp | Cancel a US mobility/maintenance card. |
| 66 | Aerial Refueling | 1U | Place one extra Squadron beyond the posture limit. |
| 67 | Reserves | 1U Resp | Fully regenerate a squadron that lost all its tokens. |
| 68 | UAS Proliferation | 1U Resp | After a UAS acquire roll: an extra acquisition attempt. |
| 69 | Elite Pilots | 1U | Next PRC air-to-air attack at advantage. |
| 70 | Ground-Based Radar | 1U | Roll D4, acquire that many US tokens. |
| 71 | Badger Surge | 1U End | H-6K rolls at advantage this ATO. |
| 72 | Special Mission Aircraft | 1U | Roll D4 & acquire that many, OR next air-to-air at advantage. |
| 73 | SOF Reconnaissance | 1U | Roll D4, acquire that many US tokens. |
| 74 | Munitions Upgrade | 1U End | One PRC fighter squadron shoots air-to-air at range 4 this ATO. |
| 75 | Ballistic Missile Strike | 1U | Roll 2+, D4 damage to the US base (cards + VP boxes). |
| 76 | Land Attack Cruise Missile | 1U | Roll 2+, D4 damage to the US base. |
| 77 | Maritime Strike Cruise Missile | 1U | **Unblockable**: destroy one US surface combatant. |
| 78 | Hypersonic Missile | 1U | **Unblockable**: roll D4, US base takes that damage. |
| 79 | Decoy Warheads | 1U Resp | Cancel a declared US missile-defense attempt. |
| 80 | Cyber Infiltration | MU | Roll to raise your Cyber Rate. |
| 81 | Offensive Cyber Operations | 1U | Remove US tokens = Cyber Rate, OR force that many discards. |
| 82 | Defensive Cyber Operations | MU Resp | Cancel a US cyber card (response) OR degrade US Cyber by 1. |
| 83 | Cyber Reconnaissance | MU | Acquire US tokens equal to your Cyber Rate. |
| 84 | Cyber Counter-UAS | 1U | Destroy US UAS tokens = your Cyber Rate. |
| 85 | Shandong J-15 Squadron | 1U | Generate 4× J-15 (carrier) in any band. |
| 86 | Guided Missile Cruiser | 1U | Generate the Dalian #105 (CG) in any band. |
| 87 | Guided Missile Destroyer | 1U | Generate the Nanning #162 (DDG) in any band. |
| 88 | Missile Boat Flotilla | 1U | Generate the Flotilla in any band. |
| 89 | Diesel-Submarine Strike | 1U | Auto-kill a US surface combatant, OR (response) cancel a US sub card. |
| 90 | Space-Based EW | 1U End | All US attack rolls (bases & tokens) at disadvantage this ATO. |
| 91 | Constellation Reconstitution | 1U | Return a spent PLASSF card to the deck for next ATO. |
| 92 | Counter Space | 1U Resp | Cancel a US space card. |
| 93 | Anti-Satellite Strike | 1U Resp | Cancel a US space card. |
| 94 | Space Reconnaissance | MU | Roll D4, acquire that many US tokens. |
| 95 | Sea Dragons Strike | 1U | **Unblockable** SOF: roll D4 damage to the US airbase (VP boxes). |
| 96 | PLANMC Raid | 1U | **Unblockable** SOF: roll D4 damage to the US airbase (VP boxes). |
| 97 | SOF Cyber Infiltration | MU | Roll to raise your Cyber Rate. |
| 98 | SOF Reconnaissance | 1U | Roll D4, acquire that many US tokens; on a 4, +1 Cyber. |

## Postures

Postures set your **enabler / squadron** card counts and add restrictions or
bonuses. You can't repeat a non-Standard posture across cycles.

**US (45–49):** 45 ACE (5 en / 3 sq — strikes on US airbases at disadvantage, CL
always generates max) · 46 Surge (7 / 6 — no CL this campaign) · 47 Hedgehog
(6 / 4 — free ADA token) · 48 Standoff (6 / 3 — both B-52 squadrons free) · 49
Standard (6 / 4 — always legal).

**PRC (99–103):** 99 PLAAF (5 / 6 — all enablers must be PLAAF) · 100 Joint
Operations (9 / 3 — all squadrons must be flying) · 101 ADA (6 / 4 — both ADA
squadrons free) · 102 Standoff (6 / 3 — +1 PLARF enabler and the H-6K squadron
free) · 103 Standard (6 / 4 — always legal).

## Missions (hidden until game end)

**US (50–54):** 50 Economy of Force · 51 Attrition · 52 Interdiction · 53 N-K
Dominance · 54 Enforce Rule of Law.

**PRC (104–108):** 104 Economy of Force · 105 Attrition · 106 Interdiction · 107
Three Dominances · 108 Counter-Intervention.

Scoring for each is in [`02_rules_reference.md`](02_rules_reference.md#scoring-by-mission).
