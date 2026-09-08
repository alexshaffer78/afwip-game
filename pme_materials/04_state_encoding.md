# AFWIP State Encoding — the "Copy state for AI" format

When you click **"📋 Copy state for AI"** in the app, you copy a rigid,
line-oriented text block that describes the game **from your side's
perspective** (fog of war already applied) and lists your **legal actions**.
This document is the spec for that block. The advisor should parse it exactly as
written here and never assume fields that aren't present.

## General grammar

- The block is **line-oriented**. Each line is one of:
  - a **banner**: `=== SECTION ===` (may carry a parenthetical note),
  - a **comment/legend**: begins with `#` — human hints; ignore for parsing,
  - a **record**: `PREFIX: key=value key=value ...`,
  - a blank line (section separator).
- **Structured field values** (`key=value`) contain no spaces.
- **Free-text values** — `name`, `label`, `prompt`, `type`, `token` — are
  wrapped in double quotes and may contain spaces, `#`, `->`, etc.
- Sentinels:
  - `-` = **not applicable / null** (e.g. no initiative yet; an action with no
    target).
  - `?` = **unknown to you** because of fog of war (e.g. an unacquired enemy
    token's type).
  - `1` / `0` = true / false.
- The block always starts with `=== AFWIP STATE v1 ===` and ends with
  `=== END ===`. The `v1` is the schema version.

## Header records

```
GAME: id=<hex> rev=<int> mode=<agent_v_agent|human_v_agent|hotseat> terminal=<0|1>
CAMPAIGN: num=<1-5> name="<campaign name>" ato=<n>/<N> turn=<int> phase=<PHASE> active=<US|PRC> initiative=<US|PRC|->
VIEWER: side=<US|PRC|->
SIDE US:  mission=<name|-> posture=<name|-> cyber=<0-4> vp=<int> intel=<NORMAL|ADVANTAGE|-> airbase_dmg=<0-3>/3
SIDE PRC: mission=<name|-> posture=<name|-> cyber=<0-4> vp=<int> intel=<NORMAL|ADVANTAGE|-> airbase_dmg=<0-3>/3
```

- `rev` increases by 1 on every decision in the game; use it to order a
  sequence of pastes into a play-by-play.
- `VIEWER: side=US` means **"you" are the US side** — every `owner=US` /
  `owner=you`-equivalent record is yours; `owner=PRC` is the enemy. (In spectator
  exports `VIEWER: side=-` and both sides are just labeled US/PRC.)
- `phase` is one of `ATO_SETUP`, `BID_INITIATIVE`, `PLAY_INTEL`, `PLAYER_TURN`,
  `END_CLEANUP`. Most decisions you copy will be in `PLAYER_TURN`.
- `mission` and `posture` are **public** for both sides once chosen, so the
  enemy's are shown too.
- `airbase_dmg=1/3` = one of the three permanent airbase VP-damage boxes on that
  side's airbase has been hit (worth VP to the attacker; the boxes carry across
  ATO cycles and don't reduce base function).
- `intel=ADVANTAGE` marks the side that won initiative this cycle.

## `=== BOARD ===`

The banner notes the band orientation. One `TOKEN:` line per token on the map:

```
TOKEN: band=<BandID> owner=<US|PRC> uid=<int> type="<name>|?" av=<int> acquired=<0|1> winchester=<0|1|?> grounded=<0|1|?>
```

- `uid` is the token's stable id — actions reference it in `actor=`/`target=`.
- `av` = **acquisition value**: the die roll (D4) needed to acquire this token.
  For an **enemy** token this is what *you* must roll ≥ to acquire it (higher =
  stealthier — F-22/F-35/J-20 are `av=4`). For **your** token it's what the enemy
  needs to acquire *you*.
- `acquired=1` means the token is face-up (identified) and can be shot; enemy
  tokens must be acquired before you can shoot them (base/standoff attacks and a
  few enabler effects excepted — see the rules doc).
- **Fog:** an enemy token you have **not** acquired shows `type="?"` and
  `winchester=?`, `grounded=?` — you know only its position and `av`. Do not
  guess its identity. Your own tokens and acquired enemy tokens show full data.

### Band geometry (important for range and positioning)

Bands, left (US rear) to right (PRC rear):

```
US_STANDOFF · US_AIRBASE · US_CONTINGENCY_LOCATION · BAND_A · BAND_B · BAND_C · BAND_D · BAND_E · PRC_AIRBASE · PRC_STANDOFF
```

The five contested range bands map to each side's own "Band 1..5" like this:

| Encoding | US calls it | PRC calls it | Nearest to |
|---|---|---|---|
| `BAND_A` | US Band 1 | PRC Band 5 | US airbase |
| `BAND_B` | US Band 2 | PRC Band 4 | |
| `BAND_C` | US Band 3 | PRC Band 3 | center |
| `BAND_D` | US Band 4 | PRC Band 2 | |
| `BAND_E` | US Band 5 | PRC Band 1 | PRC airbase |

- **US advances toward `BAND_E`** (the PRC home side); **PRC advances toward
  `BAND_A`**.
- **Range = number of bands between two locations** (adjacent = 1). Each side's
  airbase/standoff/CL sit just outside their nearest band (US bases are adjacent
  to `BAND_A`; PRC base is adjacent to `BAND_E`). So a US airbase-to-`BAND_A`
  strike is range 1; airbase to `BAND_E` is range 5; airbase to `PRC_AIRBASE` is
  range 6 (why the B-52's range-6 bomb run reaches from `US_STANDOFF`).

## `=== SQUADRONS ===`

```
SQUADRON: owner=<US|PRC> card=<id> name="<squadron name>" token="<token type>" status=<ready|active|out|destroyed> damage=<0-2>/2 tokens_lost=<int> loc=<AIRBASE|CL> grounded_tokens=<int>
FACEDOWN_SQUADRONS: side=<US|PRC> count=<int>
OFFBOARD_NAVAL: side=<US|PRC> count=<int>
```

- `status`: `ready` = deployed face-down this cycle, not yet activated;
  `active` = activated (tokens generated); `out` = not fielded this cycle;
  `destroyed` = killed (gone for the campaign).
- `damage=1/2` = one of the two hits needed to destroy the card (card damage
  resets between ATO cycles; a **destroyed** card is permanent).
- `tokens_lost` = how many of this squadron's tokens have been permanently
  destroyed this campaign; the squadron re-fields `full_count - tokens_lost`
  tokens when activated.
- **Fog:** enemy squadrons appear only when their identity is public (once
  activated, that's permanent). Enemy squadrons still hidden face-down are
  aggregated as `FACEDOWN_SQUADRONS: side=PRC count=N` — you know *how many* but
  not which.
- `OFFBOARD_NAVAL` counts Winchester ships that moved off the board (not
  destroyed, just out of the fight).

## `=== HANDS ===`

```
HAND: owner=<US|PRC> card=<id> name="<enabler name>" revealed_to_opponent=<0|1>
HAND_HIDDEN: side=<US|PRC> count=<int>
SPENT: owner=<US|PRC> card=<id> name="<enabler name>"
```

- Your own hand is listed in full. `revealed_to_opponent=1` means the enemy saw
  that card during the Intel phase (so they know you hold it).
- **Fog:** the enemy's hand shows only the cards you legitimately know — ones
  *they* revealed to *you* during Intel. The rest are aggregated as
  `HAND_HIDDEN: side=PRC count=N`.
- **`SPENT`** lines list the enabler cards each side has already **played** — a
  one-shot spent this cycle, an enduring card in effect, or a single-use card
  burned for the campaign. Playing a card is a public act, so **both** your own
  and your opponent's spent cards are listed (identities included). Use them to
  track what each side has used and what threats are gone.

## `=== CAPTURES ===`

```
CAPTURE: owner=<US|PRC> kind=<token|squadron> label="<unit>" vp=<int> on_ground=<0|1>
```

- `owner` is the side that **destroyed** the unit (the capturing side); the
  `label` names the destroyed enemy unit; `vp` is its current value **under the
  owner's mission**. `on_ground=1` means it was destroyed on the ground (matters
  for the PRC Counter-Intervention mission).

## `=== DRAFT (in progress) ===`  (only during setup, only for you)

While you are drafting for an ATO (choosing posture, squadrons, and enablers),
your picks aren't finalized until the whole draft completes — so this section
mirrors what you've chosen **so far** this setup, which the `SQUADRONS` / `HANDS`
sections can't show yet. It appears only when you're mid-draft, and only your own
picks are shown (never the opponent's in-progress draft).

```
DRAFT: side=<US|PRC> posture=<"name"|->
DRAFT_SQUADRON: card=<id> name="<squadron>" token="<token type>" loc=<AIRBASE|CL|->
DRAFT_ENABLER: card=<id> name="<enabler name>"
```

- `DRAFT:` names the side drafting and the posture chosen (or `-` if not yet).
- Each `DRAFT_SQUADRON` is a squadron you've drafted this cycle and where you've
  placed it (`loc`); each `DRAFT_ENABLER` is an enabler you've drafted so far.
- The header `SIDE …: posture=-` may still read `-` here because the draft isn't
  committed to the game state yet — trust the `DRAFT` section for your
  in-progress choices. Once the draft finalizes, these move into the normal
  `SQUADRONS` and `HANDS` sections and the `DRAFT` block disappears.
- These are **your** picks from **your own deck**. Drafting is **not contested**:
  the opponent drafts separately from their own deck and cannot take or deny your
  cards, so pick order among your own cards costs you nothing (see
  [`02_rules_reference.md`](02_rules_reference.md#setup-and-drafting)). Don't
  advise as if a card could be "lost" to the enemy by picking something else first.

## `=== DECISION ===`  (your legal actions)

If it is your decision, you get:

```
NODE: type=<NodeType> side=<US|PRC> prompt="<what you're deciding>"
ACTION: index=<int> kind=<kind> actor=<uid|-> target=<uid|-> band=<BandID|-> label="<human description>"
ACTION: ...
```

- **Choose exactly one action by its `index`.** In the app, click the choice
  with the same index/label.
- `kind` on a normal turn is one of: `pass`, `activate`, `move`, `acquire`,
  `shoot_air`, `shoot_surface`, `play_enabler`, `relaunch`. On setup / response /
  allocation decisions it may be a generic selector (`pick`, `done`, `skip`, a
  branch choice); in those cases **rely on `label`**, which fully describes the
  option.
- `actor` = your token taking the action (uid); `target` = the enemy token
  targeted (uid); `band` = destination or target band. `-` where not applicable.
- **Fog in labels:** an `acquire` action names its target only as
  `?#<uid>(av<N>)` — acquiring is exactly the attempt to identify it, so the type
  stays hidden until you succeed.

`NodeType` values you may see: `MISSION_PICK`, `POSTURE_PICK`, `SQUADRON_PICK`,
`SQUADRON_BASE`, `ENABLER_PICK`, `BID_SACRIFICE`, `FIRST_PLAYER`,
`INTEL_REVEAL`, `TURN_ACTION` (a normal turn), `SPAWN_BAND`, `ENABLER_BRANCH`
(pick an "OR" card's option), `MD_DECLARE` (declare missile defense against an
incoming strike), `RESPONSE` (play a reaction card or decline), `ALLOC_POINT`
(assign one point of base-strike damage).

If there is **no decision for you** right now (the opponent or the AI is acting):

```
NONE: reason="<why>"
```

If the **game is over**, instead of a decision you get:

```
=== RESULT ===
WINNER: <US|PRC|->
FINAL_VP: US=<int> PRC=<int>
```

## Worked example

```
=== AFWIP STATE v1 ===
GAME: id=42af7fbe rev=18 mode=human_v_agent terminal=0
CAMPAIGN: num=2 name="Tournament" ato=1/2 turn=7 phase=PLAYER_TURN active=US initiative=PRC
VIEWER: side=US
SIDE US:  mission=ATTRITION posture=STANDARD cyber=1 vp=3 intel=NORMAL airbase_dmg=0/3
SIDE PRC: mission=ATTRITION posture=STANDARD cyber=2 vp=5 intel=ADVANTAGE airbase_dmg=1/3

=== BOARD === (bands left->right: US rear .. front .. PRC rear; US advances toward BAND_E, PRC toward BAND_A)
# TOKEN fields: band owner uid type av acquired winchester grounded
TOKEN: band=BAND_C owner=US uid=5 type="F-35A" av=4 acquired=0 winchester=0 grounded=0
TOKEN: band=BAND_D owner=PRC uid=8 type="?" av=4 acquired=0 winchester=? grounded=?

=== DECISION ===
NODE: type=TURN_ACTION side=US prompt="Your turn — choose an action"
# ACTION fields: index kind actor target band label
ACTION: index=0 kind=pass actor=- target=- band=- label="Pass / end turn"
ACTION: index=1 kind=move actor=5 target=- band=BAND_D label="Move F-35A#5 -> BAND_D"
ACTION: index=2 kind=acquire actor=5 target=8 band=- label="Acquire ?#8(av4) with #5"
=== END ===
```

Reading it: you're US at Attrition, it's your turn. Your F-35 (`#5`, stealthy,
`av=4`) is at `BAND_C`. A **fogged** enemy at `BAND_D` (`av=4` — could be a
J-20, but you don't know) is one band away. You can pass (0), close to `BAND_D`
(1), or attempt to acquire the unknown contact (2). You cannot shoot it yet — it
must be acquired first, and no `shoot_air` option is listed.
