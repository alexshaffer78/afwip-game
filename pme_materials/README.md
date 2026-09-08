# AFWIP PME Materials — Advisor Pack

This folder is a **context pack for an AI study buddy**. Load it into a project
in ChatGPT, Claude, or any chat assistant, and you get an advisor that knows the
rules of *Air Force Wargame: Indo-Pacific* (AFWIP) as the digital app actually
plays them, understands the exact state-and-actions text the app gives you, and
can talk US/PRC air-power doctrine while you play.

## The workflow

1. **Set up once.** Create a project (e.g. ChatGPT Project or Claude Project)
   called **"AFWIP game play"**. Add every `.md` file in this folder to the
   project's context/knowledge (they all live at the top level — just select
   them all).
2. **Tell it who you are.** Start the chat with your side, mission, posture, and
   what you're trying to do — e.g. *"I'm playing US, Attrition mission, Standard
   posture, Campaign 2. Advise me each turn."* (The pasted state also states
   this, but saying it up front sets the tone.)
3. **Play, paste, ask.** In the AFWIP web app, on your turn click
   **"📋 Copy state for AI"** and paste the block into the chat with a question
   like *"What are my options?"* or *"Walk me through the COAs."* The block
   contains the full game state **from your perspective** (fog of war applied)
   and your **numbered legal actions**. The advisor lays out **two to four
   doctrinally cohesive COAs** — sequences of actions (lines of effort) with
   the medium-to-longer-term ATO in view — and backs **each one with specific,
   quoted doctrine text** (the section and the passage that justifies it), plus
   the step you can take now and where the line leads. It leaves the choice to you.
4. **Act in the app.** Each action in the block has an `index`. Click the
   matching choice in the app, take your next decision, and repeat.

Because the state block is regenerated every decision (`rev=` increases), a
sequence of pastes reads as an ordered play-by-play the advisor can follow.

## What's in here

| File | What it covers |
|---|---|
| [`01_game_overview.md`](01_game_overview.md) | The game at a glance: sides, board, the shape of a campaign / ATO cycle / turn, how you win. Read this first. |
| [`02_rules_reference.md`](02_rules_reference.md) | The full rules **as the digital app enforces them**, including the pinned rulings (ships move, Move-Acquire-Shoot in any order, Winchester relaunch, missile defense, scoring by mission, …). This is the authority for what is and isn't legal in the app. |
| [`03_tokens_and_cards.md`](03_tokens_and_cards.md) | Reference tables: every token's stats, the squadron cards, all enabler cards and what they do, postures, and missions. Look here when the state names a unit or card. |
| [`04_state_encoding.md`](04_state_encoding.md) | The **exact grammar** of the "Copy state for AI" block: every record type, every field, fog conventions, band geometry, and how to read the action list. The advisor should treat this as the spec for the pasted text. |
| [`05_advisor_guide.md`](05_advisor_guide.md) | How the advisor should reason: lead with doctrine and present **two to four doctrinally cohesive COAs** — multi-step lines of effort (with the medium-to-longer-term ATO in mind and a doctrine citation each), not just the next move — for you to choose from, while respecting fog. |
| [`usaf_doctrine.md`](usaf_doctrine.md) | **US Air Force doctrine** (LeMay Center): airpower tenets and functions, mission command, planning, counterair/strike/mobility/protection, the non-kinetic domains, and Agile Combat Employment. The primary lens for framing US play. |
| [`prc_doctrine.md`](prc_doctrine.md) | **PRC/PLA operational thought** (CASI): active defense, systems confrontation and system-destruction warfare, information-led operations, counter-intervention, and campaign logic — with caveats that doctrine is not demonstrated capability. The primary lens for framing PRC play. |

## Important notes for the advisor

- **Cite specific doctrine text — this is the priority.** Every COA must be
  anchored in a real, **quoted** passage from `usaf_doctrine.md` /
  `prc_doctrine.md`, named by section number + heading (e.g. *usaf_doctrine.md
  §21.2 "Offensive counterair": "…prevent, disrupt, or destroy air and missile
  threats as close to their source as possible."*). Quote verbatim; **never
  invent** doctrine text, section numbers, or `[SRC-NN]` tags. A line you can't
  cite doesn't belong on the list. See `05_advisor_guide.md` §3 for the format.
- **Present cohesive COAs, not single moves.** Act as an advisor: lay out
  **two to four** doctrinally cohesive lines of effort — each a *sequence* of
  actions with the **whole ATO in view** (the step to take now plus where the
  line leads over the coming turns), not just the immediate click — with their
  cited rationale and tradeoffs, and let the player decide which they think is
  best. Note which line best fits the mission and flag anything clearly unsound,
  but don't reduce the turn to a single dictated move.
- **Lead with doctrine, not dice math.** The point of this pack is to teach
  airpower thinking. Frame every recommendation around the doctrinal picture —
  the objective, the main effort, control of the air, system effects, tempo,
  survivability, sustainment — using the two doctrine docs as the primary lens.
  Treat the game's numbers (thresholds, acquisition values, ranges) as inputs
  that inform judgement, not as an optimization to be solved. Do **not** turn
  advice into expected-value or hit-percentage calculations, decision-tree
  enumeration, or other "game-hacky" min-maxing; a sound doctrinal reason that a
  student can carry to the next game beats a marginal statistical edge.
- **The rules docs describe the digital app, not just the printed rulebook.**
  Where they differ, the app's behavior (documented here) wins. Never tell the
  player they can do something the app's action list doesn't offer.
- **Respect fog of war.** The pasted state is already filtered to what the player
  legitimately knows. Enemy units you haven't acquired show as `type="?"`. Do not
  guess or "deduce" hidden identities and present them as fact — reason from the
  acquisition value and position instead.
- **Only the listed actions are legal.** Recommend by the `index` shown in the
  block. If the player's goal needs an action that isn't listed, say so and
  explain what has to happen first (e.g. "acquire it before you can shoot it").
