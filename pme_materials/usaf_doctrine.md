---
title: "Air Force Doctrine Context for Air Force Wargame Indo-Pacific"
subtitle: "An LLM-Ready Operational Doctrine Reference"
version: "1.0"
current_as_of: "2026-08-04"
source_authority: "Curtis E. LeMay Center for Doctrine Development and Education"
source_domain: "https://www.doctrine.af.mil/"
intended_use: "Context file for doctrine-informed analysis of Air Force Wargame Indo-Pacific board states and possible plays"
classification: "Unclassified; derived only from publicly available LeMay Center doctrine publications"
---

# Air Force Doctrine Context for Air Force Wargame Indo-Pacific

## Purpose

This document provides a detailed, operationally focused overview of United States Air Force doctrine for use as context in a large language model (LLM). It is designed to accompany:

1. a separate file containing the rules of **Air Force Wargame Indo-Pacific**;
2. a text description of the current board state; and
3. a player's question about possible actions, priorities, risks, or doctrinal relationships.

This document explains how the Air Force thinks about airpower, command and control, planning, targeting, mission integration, force protection, sustainment, and Agile Combat Employment. It does **not** replace the game rules and should not be used to invent game mechanics. When doctrine and game abstractions differ, the LLM should explain the doctrinal relationship while applying the game rules exactly as written.

All substantive sourcing in this document comes exclusively from the **Curtis E. LeMay Center for Doctrine Development and Education** through the official Air Force doctrine website at `https://www.doctrine.af.mil/`. The principal index is the **Air Force Doctrine Smart Book**, updated 4 July 2026. The Smart Book states that the full source publications take precedence.[SRC-01]

---

# Instructions to the LLM

When this file is attached with game rules and a board state, follow these rules.

## Separate four kinds of information

Clearly distinguish:

- **Doctrine:** authoritative Air Force principles and recommended ways of thinking about operations.
- **Game rules:** binding mechanics that determine what a player may do and how the game resolves actions.
- **Board-state facts:** the pieces, locations, damage, missions, cards, resources, threats, and timing actually present.
- **Inference:** your interpretation of how a possible play relates to doctrine.

Never present an inference as an official rule or official doctrine.

## Use doctrine as a lens, not as an extra rules engine

Doctrine can help assess whether a play:

- supports the commander's objective;
- creates or preserves freedom of action;
- concentrates effects at the right place and time;
- balances offense, defense, protection, and sustainment;
- imposes dilemmas on the opponent;
- preserves combat power for future turns;
- exploits speed, range, flexibility, and persistence;
- accounts for command-and-control limits;
- integrates intelligence, targeting, mobility, and protection;
- creates a coherent sequence rather than an isolated tactical action.

Doctrine does not authorize the LLM to add movement, attacks, effects, victory points, cards, capabilities, or exceptions that are not in the game rules.

## Cite this document specifically

Doctrine advice is only useful if it is traceable. Whenever you use a doctrinal idea, **cite it specifically**: name the section by its number and heading and quote the exact passage. This document is numbered (`## 21. Counterair operations`, `### 21.2 Offensive counterair`) and tags its sources `[SRC-NN]`, so a citation looks like:

> *§21.2 "Offensive counterair": "prevent, disrupt, or destroy air and missile threats as close to their source as possible."*

Quote **verbatim** from this document (a few words up to one sentence). **Never invent** section numbers, headings, quotations, or `[SRC-NN]` tags — if you cannot find supporting text, reason qualitatively and say so rather than manufacturing a citation. Prefer two or more citations when several ideas apply.

## Recommended response structure

When analyzing a proposed play, use this structure:

1. **Rules legality:** Is the action legal under the provided game rules?
2. **Immediate effect:** What changes on the board if it succeeds?
3. **Doctrinal purpose:** Which objective, function, mission, or tenet does it support?
4. **Operational integration:** What enabling actions are required before, during, or after it?
5. **Risk and opportunity cost:** What becomes exposed, delayed, unsupported, or unavailable?
6. **Adversary response:** What is the opponent's most dangerous and most likely reaction?
7. **Assessment:** What observable result would show that the action worked?
8. **COAs:** Offer the player two to four doctrinally cohesive options — each a *sequence of actions* with the medium-to-longer-term arc of the ATO in view (the step available now plus its intended follow-on and branch points), not a single move — each grounded in a **specific doctrine-text citation** (section number + heading + a short verbatim quote; never invented), with their tradeoffs and assumptions, rather than dictating one. The player decides which line is best.

## Confidence language

Use:

- **High confidence** when the game rule and doctrinal relationship are explicit.
- **Moderate confidence** when the doctrine is clear but the board state is incomplete.
- **Low confidence** when the recommendation depends on uncertain hidden information, ambiguous rules, or inferred opponent intent.

---

# Part I — Foundations of Air Force Doctrine

## 1. What doctrine is

Air Force doctrine is an agreed-upon and operationally relevant body of principles and best practices informed by history, debate, analysis, exercises, wargames, and contingency operations. It is **authoritative but not directive**: doctrine normally provides the best starting point, but commanders may depart from it when compelling operational reasons justify doing so.[SRC-02]

Doctrine is different from policy and strategy:

- **Policy** governs the use of force and establishes legal or administrative boundaries.
- **Strategy** connects ends, ways, means, and risk.
- **Doctrine** supplies a common frame of reference and an informed starting point for organizing, planning, and employing forces.

For game analysis, this distinction matters. A doctrinally attractive move may still be prohibited by the rules, strategically irrelevant to the victory conditions, or too risky given the current board state.

## 2. Airpower

Airpower is the ability to project military power through control and exploitation **in, from, and through the air**.[SRC-03] Airmen support joint all-domain operations principally through operations in, from, and through:

- the air;
- the information environment; and
- the electromagnetic spectrum.

Airpower is not merely the use of aircraft to attack targets. It includes the command, intelligence, mobility, protection, sustainment, information, and enabling systems that make air operations possible.

### 2.1 The Airman's perspective

The Airman's perspective emphasizes several recurring ideas.[SRC-03]

**Control of the air enables the joint force.** Control of the air is a necessary precondition for effective control of the surface. It need not mean permanent air supremacy everywhere. It means obtaining the degree of control required at the relevant place and time.

**Airpower can create strategic effects.** Air operations may affect leadership, command systems, logistics, fielded forces, infrastructure, behavior, and an adversary's ability or willingness to continue.

**Airpower combines mass and maneuver.** Aircraft and other capabilities can converge effects rapidly without permanently massing large forces in one physical location.

**Airpower reaches across a theater.** It is not naturally confined to land-component boundaries. Its range and speed allow effects to be created throughout an operational area.

**Airpower attacks systems, not only objects.** The value of striking a target depends on the target's function, its relationship to other nodes, and the effect required by the commander's objective.

**Airpower provides lethal and nonlethal effects.** Intelligence, mobility, electronic warfare, information activity, deterrence, surveillance, command and control, and presence may be as important as physical destruction.

**Airpower requires protection and sustainment.** Aircraft without fuel, munitions, maintenance, usable airfields, communications, intelligence, and defended bases do not constitute usable combat power.

**Airpower requires effective integration.** People, capabilities, weapons, bases, logistics, data, communications, and supporting infrastructure must work as a system.

**Airpower should be centrally commanded by an Airman.** Centralized command promotes unity of effort, coherent prioritization, and the ability to concentrate effects across a theater.

## 3. The competition continuum

Airpower is applied during enduring competition that includes cooperation, adversarial competition, and armed conflict.[SRC-04] The same force may simultaneously reassure allies, deter adversaries, posture for crisis, collect intelligence, defend bases, and prepare for combat.

A game move should therefore be examined at more than one level:

- Does it win the immediate engagement?
- Does it improve or degrade the next turn?
- Does it reveal intentions or capabilities?
- Does it preserve escalation options?
- Does it strengthen or weaken allied access?
- Does it affect the adversary's expectations and risk calculations?
- Does it create a favorable operational position even if it scores no immediate points?

## 4. Coercion: deterrence and compellence

AFDP 3-0 describes coercion as encompassing deterrence and compellence.[SRC-05]

- **Deterrence** seeks to prevent an adversary from taking an action.
- **Compellence** seeks to cause an adversary to begin, modify, or stop an action.

Compellence may operate through:

- **Denial:** convincing the adversary that it cannot achieve its objective.
- **Risk:** placing something the adversary values at credible risk.
- **Punishment:** imposing costs until behavior changes.
- **Combinations:** integrating denial, risk, and punishment.

In a wargame, an attack is not automatically strategically useful because it destroys a unit. Its doctrinal value depends on whether it denies an objective, changes the opponent's choices, protects friendly freedom of action, or contributes to a broader operational effect.

## 5. Tenets of airpower

AFDP 1 identifies seven tenets of airpower.[SRC-03]

### 5.1 Mission command

Mission command empowers subordinate decision-making within the commander's intent. It is discussed in detail in Part II.

### 5.2 Flexibility and versatility

Airpower can shift rapidly among missions, locations, targets, and levels of war. Flexibility is the ability to redirect effort; versatility is the ability to perform multiple kinds of missions.

**Game implication:** preserve options when the situation is uncertain. A force committed too early to one mission may lose the advantage that airpower's adaptability should provide.

### 5.3 Synergistic effects

The combined effect of capabilities can exceed the sum of isolated actions. Intelligence enables targeting; counterair enables mobility and strike; electronic warfare improves survivability; mobility sustains dispersed forces; protection preserves sortie generation.

**Game implication:** evaluate packages and sequences, not just the strongest individual token or card.

### 5.4 Persistence

Airpower can maintain influence over time through recurring presence, surveillance, alert, patrol, replenishment, or repeated attack. Persistence is not identical to permanence; it may be achieved by rotating forces and capabilities.

**Game implication:** a one-turn advantage that exhausts the force may be inferior to a sustainable posture that constrains the opponent across several turns.

### 5.5 Concentration

Airpower can concentrate effects without permanently concentrating forces. The purpose is to generate decisive effects at the required place and time.

**Game implication:** dispersal for survival and concentration for effect are not opposites. A dispersed force can converge on a priority target.

### 5.6 Priority

Resources are finite. Commanders must establish priorities so that the most important objectives receive sufficient effort.

**Game implication:** do not distribute scarce aircraft, munitions, enablers, or defensive capacity evenly merely because several needs exist. Determine the main effort.

### 5.7 Balance

Commanders balance competing demands: offense and defense, concentration and dispersion, present and future requirements, effectiveness and efficiency, mission and force risk, centralized direction and subordinate initiative.

**Game implication:** there is rarely a doctrinally perfect move. The question is whether the tradeoff supports the commander's objective at acceptable risk.

## 6. Core Air Force functions

AFDP 3-0 organizes Air Force contributions around five core functions.[SRC-04]

1. **Air Superiority**
2. **Global Precision Attack**
3. **Rapid Global Mobility**
4. **Global Intelligence, Surveillance, and Reconnaissance**
5. **Command and Control**

These functions are mutually supporting. A strike package may require intelligence to find the target, counterair to reach it, mobility to refuel it, command and control to synchronize it, and sustainment to generate later sorties.

---

# Part II — Mission Command and Command and Control

## 7. Mission command

Mission command is the Airman's philosophy for leadership and the command and control of airpower. It empowers Airmen to operate in uncertain, complex, and rapidly changing environments through trust, shared awareness, and understanding of commander's intent.[SRC-06]

The Air Force executes mission command through:

> **Centralized Command — Distributed Control — Decentralized Execution (CC-DC-DE)**

### 7.1 Centralized command

Centralized command gives a commander responsibility and authority for planning, directing, coordinating, and prioritizing an operation.

Centralization is especially important for airpower because scarce capabilities can be shifted rapidly across a theater. Without coherent theater-level prioritization, subordinate units may optimize local engagements while undermining the joint force's main effort.

### 7.2 Distributed control

Distributed control delegates authorities for planning, coordination, execution, and assessment to dispersed organizations. It improves span of control, resilience, and the ability to continue operating when communications are degraded.[SRC-07]

Distributed control is not simple independence. It requires:

- explicit authorities;
- clear command relationships;
- capable subordinate command elements;
- trained personnel;
- appropriate communications and data;
- shared understanding of the operational design;
- resources sufficient to execute delegated responsibilities.

### 7.3 Decentralized execution

Decentralized execution empowers subordinate decision-makers to act with flexibility, initiative, and responsiveness. It is effective only when subordinates understand:

- the mission;
- the purpose;
- the commander's intent;
- the desired end state;
- operational priorities;
- delegated authorities;
- constraints and restraints;
- available resources;
- acceptable risk.

### 7.4 Principles of mission command

AFDP 1-1 identifies six principles.[SRC-06]

#### Commander's intent

Commander's intent explains the purpose of the operation, the desired military end state, and the broad approach. It allows subordinates to adapt actions without losing unity of purpose.

#### Shared understanding

Participants need a common picture of the problem, friendly and adversary systems, objectives, priorities, and relevant constraints. Shared understanding does not require identical information at every echelon.

#### Disciplined initiative

Subordinates act when existing orders no longer fit the situation, provided their actions remain consistent with the commander's intent.

#### Mutual trust

Commanders must trust subordinates to exercise judgment; subordinates must trust that reasonable initiative will be supported.

#### Accept prudent risk

Risk cannot be eliminated. Commanders deliberately accept risk where doing so creates opportunity or protects higher priorities.

#### Mission-type orders

Mission-type orders emphasize what must be accomplished and why, rather than prescribing every detail of how to do it.

### 7.5 The Five C's of mission-command culture

AFDP 1-1 describes five attributes required to sustain mission command.[SRC-06]

- **Character**
- **Competence**
- **Capability**
- **Cohesion**
- **Capacity**

An organization cannot rely on decentralized execution if its people lack the competence, resources, shared habits, or capacity to act.

## 8. The command-and-control function

AFDP 3-0.1 describes command and control as the central and synchronizing joint function. C2 includes four major elements.[SRC-08]

### 8.1 Commander

The commander is the core element. Commanders continuously:

1. understand;
2. visualize;
3. decide; and
4. direct.

### 8.2 Framework

The framework establishes command relationships and delegates authority. CC-DC-DE guides how authority is retained, distributed, or delegated.

### 8.3 Process

The C2 process consists of four continuous and overlapping activities:

1. **Planning**
2. **Preparing**
3. **Executing**
4. **Assessing**

The air tasking cycle, targeting cycle, and airlift cycle operate within this larger process.

### 8.4 Systems

A C2 system is the integrated network of:

- personnel;
- organizations;
- facilities;
- equipment;
- communications;
- data;
- procedures; and
- decision-support technology.

C2 is therefore not synonymous with a radio, data link, headquarters, or software tool. Loss of one component may degrade the system without eliminating command.

## 9. Air component command relationships

AFDP 3-0 explains that Air Force forces are presented as a Service component under the senior Air Force commander.[SRC-04]

The air component commander may perform two distinct roles:

- **Commander, Air Force Forces (COMAFFOR):** commands Air Force forces and fulfills Service responsibilities.
- **Joint Force Air Component Commander (JFACC):** plans and directs joint air operations using forces made available by the joint force commander.

The same individual commonly serves in both roles, but the authorities and responsibilities are conceptually distinct.

### 9.1 Why the distinction matters

A unit may be administratively an Air Force organization while being operationally tasked through a joint air plan. Service responsibilities such as readiness, sustainment, discipline, force protection, and organizing Air Force forces remain important even when sorties support joint objectives.

### 9.2 Supported and supporting relationships

A supported commander has primary responsibility for an assigned objective or mission. Supporting commanders provide capabilities or actions that enable the supported commander's success.

A doctrinal analysis should ask:

- Who owns the objective?
- Which component is supported?
- Which components provide supporting effects?
- Are support requirements explicit?
- Does a local action help the supported commander's priority or consume resources needed elsewhere?

## 10. The Air Operations Center and theater air control system

The Air Operations Center (AOC) is the senior element of the theater air control system and the principal organization through which the air component commander plans, directs, and assesses air operations.[SRC-09]

At a conceptual level, the AOC:

- translates objectives and guidance into an air component approach;
- integrates component and partner requirements;
- develops and updates plans;
- prioritizes targets and effects;
- allocates capabilities;
- produces tasking;
- monitors execution;
- redirects missions when necessary;
- assesses results.

The theater air control system connects operational-level command with tactical control and execution. In a wargame abstraction, this relationship can be represented by command capacity, mission cards, tasking limits, communication status, or the player's ability to coordinate multiple actions.

## 11. C2 in degraded communications

AFDP 3-0.1 emphasizes that exclusive reliance on theater-level integration creates vulnerabilities. Distributed C2 can allow subordinate forces to build and execute options during periods of denied or degraded communication.[SRC-07]

A resilient approach requires preplanned answers to questions such as:

- What authorities transfer when communication is lost?
- Which objectives remain highest priority?
- What information is essential?
- How long may a subordinate continue under the last order?
- What actions require higher approval?
- What branches or sequels are preauthorized?
- What conditions trigger movement, attack, withdrawal, or reconstitution?
- How will forces reestablish shared understanding?

**Wargame implication:** a plan dependent on perfect connectivity is fragile. A doctrinally stronger plan remains coherent after a headquarters, relay, enabler, or key node is disrupted.

---

# Part III — Planning, Operational Design, and Assessment

## 12. Planning as a command activity

AFDP 5-0 defines planning as the process through which Airmen frame problems and develop solutions to achieve military objectives. Planning is the first major activity in the C2 process and provides guidance for preparation, execution, and assessment.[SRC-10]

Planning supports decentralized execution by producing:

- a clear mission;
- commander's intent;
- tasks and purposes;
- priorities;
- coordinating instructions;
- authorities;
- resources;
- decision points;
- branches and sequels;
- assessment criteria.

## 13. The Air Force Planning Process

The Air Force Planning Process (AFPP) is a commander-led method used by Air Force commanders and staffs at multiple echelons.[SRC-10]

The seven steps are:

1. **Planning Initiation**
2. **Mission Analysis**
3. **Course of Action Development**
4. **Course of Action Analysis and Wargaming**
5. **Course of Action Comparison**
6. **Course of Action Approval**
7. **Plans and Orders Development**

The process is iterative. Time pressure may compress activities and products, but the logic should not be discarded.

### 13.1 Planning initiation

Planning begins in response to higher guidance, a changed situation, or a locally identified problem. The staff:

- alerts participants;
- gathers doctrine, orders, intelligence, maps, rules, and estimates;
- begins understanding the operational environment;
- assesses time and resources;
- frames the initial problem;
- identifies required coordination;
- receives the commander's initial guidance.

### 13.2 Mission analysis

Mission analysis determines what must be accomplished and why. It normally includes:

- analysis of higher headquarters' mission and intent;
- specified, implied, and essential tasks;
- constraints and restraints;
- facts and assumptions;
- friendly and adversary capabilities;
- operational environment;
- risk;
- information requirements;
- initial force requirements;
- identification of the essential problem;
- development of a restated mission;
- commander's intent and planning guidance.

### 13.3 Course of action development

A course of action (COA) describes a feasible way to accomplish the mission. A useful COA should be:

- suitable for the objective;
- feasible with available resources;
- acceptable in risk and cost;
- distinguishable from alternatives;
- complete enough to analyze.

A COA should explain more than a target list. It should describe the main effort, supporting efforts, sequencing, task organization, command relationships, key effects, decision points, sustainment, and risk.

### 13.4 COA analysis and wargaming

The staff tests each COA against adversary actions and operational friction. It should examine:

- the adversary's most likely COA;
- the adversary's most dangerous COA;
- friendly action;
- adversary reaction;
- friendly counteraction;
- critical events;
- decision points;
- resource shortfalls;
- timing;
- synchronization;
- branches;
- risks to mission and force.

For LLM game analysis, this is the most important discipline. Do not recommend a move based only on the friendly action. Simulate at least one plausible opponent reaction.

### 13.5 COA comparison and approval

COAs are compared using criteria linked to the mission, commander's guidance, and risk. The commander selects, modifies, or rejects a COA.

### 13.6 Plans and orders development

The approved COA is converted into a plan or order that communicates:

- situation;
- mission;
- execution;
- administration and logistics;
- command and signal.

Mission-type orders should preserve subordinate flexibility while conveying sufficient purpose, priority, and boundaries.

## 14. Operational design

Operational design frames the problem and provides the conceptual foundation for a campaign, operation, plan, or order.[SRC-10] Air component design applies adaptive thinking to an Air Force problem within the joint force's broader operational design.

AFDP 5-0 identifies design elements including:

- objective;
- desired end state;
- root cause;
- effects;
- culmination;
- physical characteristics of the operational environment;
- lines of operation and lines of effort;
- decisive points;
- direct and indirect approaches;
- operational reach;
- arrangement of operations;
- anticipation;
- forces and functions.

### 14.1 Objective

An objective is the clearly defined, decisive, and attainable goal toward which an operation is directed.

A tactical action should be traceable to an objective. If the LLM cannot explain what objective an attack, move, or card supports, it should question the action's value.

### 14.2 Desired end state

The desired end state describes conditions that should exist when the operation is complete. It should not be confused with an activity such as “conduct strikes.”

### 14.3 Effects

An effect is a physical or behavioral state resulting from an action, set of actions, or another effect. The Airman's planning perspective seeks a coherent link:

> **End state → Objectives → Effects → Tasks → Actions**

A target is not an objective. Destroying a target is not necessarily the desired effect. The target matters because of the function it performs and the operational change expected from engaging it.

### 14.4 Culmination

Culmination occurs when a force can no longer continue its form of operations. Air forces may culminate because of:

- munitions depletion;
- maintenance limits;
- damaged runways;
- insufficient fuel;
- tanker losses;
- command disruption;
- aircrew fatigue;
- loss of access;
- excessive attrition;
- inability to protect bases;
- insufficient logistics throughput.

### 14.5 Operational reach

Operational reach is the distance and duration across which a force can successfully employ military capabilities. In the Indo-Pacific, reach is shaped by geography, basing, tankers, airlift, logistics, airfield capacity, protection, and communications.

### 14.6 Direct and indirect approaches

A direct approach attacks an adversary's principal strength or center of gravity more directly. An indirect approach attacks vulnerabilities, enabling systems, relationships, or conditions that make the strength usable.

A player may obtain a greater effect by attacking:

- tankers rather than fighters;
- runways rather than aircraft in flight;
- sensors rather than shooters;
- logistics rather than forward units;
- command links rather than every subordinate force;
- access and timing rather than raw combat strength.

## 15. Adaptive thinking

Adaptive thinking is the ability to analyze information critically, think creatively, make decisions, and solve problems dynamically throughout planning.[SRC-10]

An LLM should not mechanically equate doctrine with a fixed checklist. It should use doctrinal principles to understand a changing problem, identify assumptions, and adapt the recommendation when the board state changes.

## 16. Risk

Risk includes both:

- **risk to mission:** the possibility of failing to achieve the objective; and
- **risk to force:** the possibility of losing people, capabilities, position, or future combat power.

These risks often trade against each other. Excessive protection may make the force irrelevant; excessive aggression may leave no force able to exploit success.

A doctrinal recommendation should state:

- what risk is being accepted;
- why it is prudent;
- what higher priority it protects;
- how the risk will be mitigated;
- what condition would make the risk unacceptable.

## 17. Assessment

Assessment determines whether operations are producing the intended effects and whether the plan should continue or change.

Useful measures include:

- **Measures of performance:** Did the force execute the assigned action?
- **Measures of effectiveness:** Did the action create the desired operational condition?

Examples:

- “Sorties launched” is a measure of performance.
- “Enemy missile attacks reduced” is a measure of effectiveness.
- “Runway struck” is performance.
- “Enemy sortie generation delayed for two turns” is effectiveness.

Assessment must inform replanning. A plan that continues after its assumptions fail is not adaptive.

## 18. Civilian harm mitigation and legal legitimacy

AFDP 5-0 directs commanders and staffs to incorporate civilian harm mitigation and response throughout planning.[SRC-10] Legal and moral considerations are not separate from effectiveness. Civilian harm can undermine legitimacy, coalition cohesion, freedom of action, and strategic objectives.

Even when a commercial game abstracts civilian considerations, an LLM discussing real doctrine should recognize that:

- military necessity does not eliminate legal obligations;
- target value must be connected to an objective;
- feasible precautions matter;
- proportionality and distinction shape targeting;
- strategic consequences may exceed immediate physical effects.

---

# Part IV — Intelligence, Targeting, and Major Operational Missions

## 19. Intelligence and ISR

AFDP 2-0 describes intelligence as both the product and the activities through which information about foreign nations, hostile forces, and operational areas is collected, processed, integrated, evaluated, analyzed, and interpreted.[SRC-11]

Intelligence enables decision advantage by reducing uncertainty, identifying opportunities, and warning of threats. It does not eliminate uncertainty.

### 19.1 Intelligence, surveillance, and reconnaissance

ISR integrates the planning and operation of sensors, assets, and processing, exploitation, and dissemination systems in support of current and future operations.

Key air-component intelligence functions include:

- battlespace characterization;
- collection operations;
- targeting support;
- intelligence mission data production;
- support to capability development and acquisition.

### 19.2 PCPADE

The Air Force describes the joint intelligence process with the acronym **PCPADE**:[SRC-11]

1. Planning and Direction
2. Collection
3. Processing and Exploitation
4. Analysis and Production
5. Dissemination and Integration
6. Evaluation and Feedback

A sensor without processing and dissemination may not create decision advantage. Likewise, collecting more information is not automatically useful if it arrives too late to affect a decision.

### 19.3 Game-analysis implications

Ask:

- What is known, inferred, or unknown?
- Which uncertainty most affects the decision?
- What collection action could reduce it?
- Is the information timely enough?
- What deception or concealment might distort the picture?
- What intelligence must be shared with other forces?
- What decision can be made despite uncertainty?

## 20. Targeting

AFDP 3-60 defines targeting as selecting and prioritizing targets and matching appropriate responses to them, considering operational requirements and capabilities.[SRC-12]

A target is an entity or object that performs a function for the adversary and is considered for possible engagement.

### 20.1 Principles of targeting

Targeting is:

- **Objectives-based:** connected to the commander's objectives and desired end state.
- **Effects-based:** seeks physical or behavioral effects, lethal or nonlethal.
- **Interdisciplinary:** integrates operators, intelligence, planners, legal advisors, and other specialists.
- **Systemic:** examines targets as parts of systems and uses a structured, iterative process.
- **Estimative:** predicts outcomes and adversary responses.

### 20.2 Deliberate and dynamic targeting

- **Deliberate targeting** addresses targets developed in time for planned tasking.
- **Dynamic targeting** addresses targets identified too late for the deliberate cycle or not previously selected.

Dynamic targeting is not impulsive targeting. It still requires identification, authorization, capability matching, legal review as applicable, and consideration of the commander's priorities.

### 20.3 Target-system thinking

The LLM should examine:

- the target's function;
- dependencies;
- redundancy;
- replacement time;
- repairability;
- adversary adaptation;
- second-order effects;
- the duration of the desired effect;
- whether a nonlethal or indirect action could work better;
- whether the target is worth scarce munitions and exposure.

### 20.4 The find-fix-track-target-engage-assess logic

Although specific tactical processes vary, a useful conceptual sequence is:

1. Find the relevant entity.
2. Fix its location and identity.
3. Track it as necessary.
4. Select and prioritize it.
5. Engage with an appropriate capability.
6. Assess the result and reattack requirement.

A game may compress these steps into cards, detection states, legal-action lists, or attack rolls. The doctrinal logic remains that effects require a functioning chain.

## 21. Counterair operations

AFDP 3-01 defines counterair as the integration of offensive and defensive operations to attain and maintain the desired degree of control of the air and protect forces by neutralizing or destroying threats from all domains that challenge that control.[SRC-13]

### 21.1 Degrees of control

- **Air parity:** neither side has control.
- **Air superiority:** one force can conduct operations at a particular time and place without prohibitive interference from air and missile threats.
- **Air supremacy:** the opposing force cannot effectively interfere within the operational area using air and missile threats.

Control is relative, geographically bounded, and time dependent. A force does not need air supremacy across the theater to create a local and temporary window for another mission.

### 21.2 Offensive counterair

Offensive counterair seeks to prevent, disrupt, or destroy air and missile threats as close to their source as possible. Potential target categories include:

- aircraft;
- missiles;
- launchers;
- airfields;
- command and control;
- sensors;
- fuel and munitions;
- maintenance and support;
- integrated air defense nodes.

### 21.3 Defensive counterair

Defensive counterair protects friendly forces and areas from air and missile attack. It includes active and passive measures.

Active defense may include detection, interception, engagement, and electronic action. Passive defense may include dispersal, hardening, camouflage, concealment, deception, warning, redundancy, and rapid recovery.

### 21.4 Integrated air and missile defense

Integrated air and missile defense combines capabilities and overlapping operations to reduce the effectiveness of adversary air and missile threats. No defense is perfect. Commanders must prioritize what to protect and accept risk elsewhere.

### 21.5 Counterair planning questions

- What degree of control is actually required?
- Where and when is it required?
- Which threat most directly prevents friendly freedom of action?
- Is the best response offensive, defensive, passive, or combined?
- Which assets must be protected to preserve the campaign?
- Does the plan include assessment and reattack?
- Is the air component commander properly prioritizing theater-wide needs?

## 22. Strategic attack

AFDP 3-02 describes strategic attack as offensive action against a military, political, economic, or other target selected specifically to achieve strategic objectives.[SRC-14]

Strategic attack is defined by intended effect, not by platform, weapon, distance, or target appearance. A tactical platform may create a strategic effect; a long-range strike may produce only a tactical effect.

Strategic attack often focuses on high-level adversary systems, centers of gravity, leadership, command mechanisms, critical capabilities, or sources of national power. Because effects may be politically sensitive, command and control may be retained at high levels.

### 22.1 Wargame implications

Before calling a strike “strategic,” ask:

- Which strategic objective does it support?
- What adversary system is affected?
- How does physical damage translate into behavior or capability change?
- Is the target truly critical, or merely visible?
- What redundancy or substitution exists?
- Could the strike create escalation or coalition costs?
- Is the effect durable?

## 23. Counterland operations

AFDP 3-03 describes counterland as airpower operations against enemy land-force capabilities to create effects that achieve joint force commander objectives.[SRC-15]

The two principal forms are:

- **Air interdiction:** air operations to divert, disrupt, delay, or destroy enemy military potential before it can be effectively used against friendly forces, or otherwise to achieve joint objectives.
- **Close air support:** air action against hostile targets near friendly forces that requires detailed integration with the fire and movement of those forces.

Counterland requires unity of effort between air and land components. The air component should not merely service target requests; commanders should collaborate on which effects best support the joint objective.

## 24. Countersea operations

AFDP 3-04 defines countersea as operations conducted to attain and maintain a desired degree of maritime superiority by destroying, disrupting, delaying, diverting, or otherwise neutralizing threats in the maritime environment.[SRC-16]

The maritime domain includes oceans, seas, bays, estuaries, islands, coastal areas, littorals, and the airspace above them.

Airpower contributes through speed, range, precision, flexibility, surveillance, strike, mining-related support, protection, and integration with surface and subsurface forces.

### 24.1 Countersea purposes

Countersea actions may:

- support lodgment or access;
- deny an area or facility;
- protect sea lines of communication;
- attack naval forces;
- support maritime interception;
- provide surveillance and reconnaissance;
- protect friendly naval and air forces;
- create maritime superiority in a specific time and place.

### 24.2 Indo-Pacific implications

Maritime distances and island geography make countersea, counterair, ISR, mobility, and access inseparable. An action against a ship may also be a counterair action if that ship carries air-defense sensors or missiles; an airfield attack may support maritime superiority by reducing long-range anti-ship capability.

## 25. Air mobility operations

AFDP 3-36 explains rapid global mobility as the ability to employ and sustain military forces so joint force commanders can conduct decisive operations across the competition continuum.[SRC-17]

Air mobility includes:

- airlift;
- air refueling;
- aeromedical evacuation;
- mobility support;
- related command-and-control and en-route systems.

### 25.1 Airlift

Airlift moves forces, equipment, and supplies. Its operational value depends on:

- usable departure, en-route, and arrival locations;
- aircraft availability;
- throughput;
- threat;
- loading and unloading capacity;
- ground handling;
- airspace access;
- prioritization;
- onward movement.

### 25.2 Air refueling

Air refueling extends range, payload, persistence, and flexibility. Tankers are high-value enabling assets whose loss or displacement may sharply reduce combat reach.

### 25.3 Aeromedical evacuation

Aeromedical evacuation transports patients under medical supervision and contributes to force preservation and confidence.

### 25.4 Mobility as a limiting system

In a theater of great distances, the number of combat aircraft may not be the true limiting factor. The binding constraint may be tanker availability, airfield throughput, ramp space, fuel distribution, cargo handling, or protection of mobility corridors.

## 26. Special operations

AFDP 3-05 describes Air Force special operations as specially organized, trained, and equipped capabilities used to achieve military, political, economic, or informational objectives by unconventional means in hostile, denied, or politically sensitive environments.[SRC-18]

Air Force special operations can provide:

- precision strike;
- specialized air mobility;
- intelligence and reconnaissance;
- special tactics;
- personnel recovery support;
- air advising;
- information-related capabilities;
- access and preparation of the operational environment.

Special operations should be integrated into the joint campaign and not treated as an isolated set of raids.

## 27. Force protection

AFDP 3-10 defines force protection as measures to prevent or mitigate enemy and insider actions against personnel, resources, facilities, and critical information.[SRC-19]

### 27.1 Airman's perspective on force protection

- Every Airman contributes.
- Protection is multidimensional and layered.
- Protection must be integrated with operations.
- Threats include direct attack, missiles, unmanned systems, sabotage, insider threats, cyber effects, electromagnetic attack, and information compromise.
- Protection supports mission continuation, not merely survival.

### 27.2 Active, passive, and responsive measures

A balanced approach may include:

- active defense;
- access control and security;
- dispersal;
- hardening;
- camouflage, concealment, and deception;
- redundancy;
- warning;
- counter-unmanned aircraft measures;
- emergency response;
- rapid repair;
- reconstitution;
- movement;
- operational security.

### 27.3 Protection prioritization

Not every asset can receive maximum protection. Priorities should reflect:

- criticality to the objective;
- vulnerability;
- threat;
- redundancy;
- recovery time;
- consequences of loss;
- ability to relocate;
- ability to deceive the adversary.

## 28. Engineer operations and airfield recovery

AFDP 3-34 emphasizes that engineers enable operations by establishing, operating, protecting, sustaining, and recovering bases and infrastructure.[SRC-20]

Engineer capabilities include:

- general engineering;
- geospatial engineering;
- installation support;
- explosive ordnance disposal;
- fire and emergency services;
- emergency management;
- heavy construction and repair;
- rapid airfield damage repair.

For Agile Combat Employment, engineers enable maneuver and resilience through:

- site assessment;
- runway and pavement repair;
- expedient facilities;
- utilities;
- hardening;
- passive defense;
- damage recovery;
- explosive hazard mitigation.

A base that survives an attack but cannot generate missions has not been effectively protected.

## 29. Airspace control

AFDP 3-52 defines airspace control as the exercise of delegated authority over designated airspace and users through procedures and coordination measures to maximize operational effectiveness.[SRC-21]

The goal is not simply flight safety. Airspace control enables joint and multinational operations by allowing diverse users to operate with reduced interference and fratricide risk.

Airspace control must balance:

- positive control and procedural control;
- flexibility and order;
- civilian and military requirements;
- fires and aviation;
- speed and deconfliction;
- centralized policy and decentralized execution.

In a contested environment, airspace control may be degraded. Preplanned procedures, identification measures, authorities, and communication-loss actions become essential.

## 30. Cyberspace operations

AFDP 3-12 presents the Air Force approach to operating in, through, and from cyberspace.[SRC-22] Cyberspace capabilities can support Air Force and joint operations by creating effects, defending mission systems, and enabling command, intelligence, targeting, logistics, and weapons employment.

A doctrinal analysis should avoid treating “cyber” as a magic effect. It should ask:

- What system is being affected?
- What access is required?
- What authority is required?
- What operational effect is desired?
- How long will the effect last?
- How will the adversary detect and respond?
- What friendly dependence creates vulnerability?
- Is the cyber action synchronized with physical or informational action?

## 31. Electromagnetic spectrum operations

AFDP 3-85 defines electromagnetic spectrum operations as coordinated military actions to exploit, attack, protect, and manage the electromagnetic environment in support of commander's objectives.[SRC-23]

### 31.1 Electromagnetic warfare divisions

- **Electromagnetic attack:** uses electromagnetic energy, directed energy, or anti-radiation weapons to deceive, disrupt, degrade, or destroy enemy capability.
- **Electromagnetic protection:** reduces friendly vulnerability to intentional and unintentional electromagnetic effects.
- **Electromagnetic support:** searches for, intercepts, identifies, and locates radiated energy to support awareness, targeting, warning, and countermeasures.

### 31.2 Spectrum management

Friendly forces also compete with themselves for spectrum. Effective management prevents interference and preserves access for communications, sensing, navigation, weapons, and command systems.

### 31.3 Wargame implications

An electronic action should be connected to a purpose such as:

- opening a strike corridor;
- protecting a package;
- degrading detection;
- disrupting command;
- locating emitters;
- inducing adversary emissions;
- preserving friendly communications;
- supporting deception.

## 32. Information in Air Force operations

AFDP 3-13 addresses how the Air Force plans and integrates activities in the information environment.[SRC-24] Information effects may influence perceptions, behavior, decision-making, and the ability to command and operate.

Information considerations should be integrated from the beginning, not added after physical actions are chosen.

Questions include:

- What will friendly, adversary, allied, and neutral audiences observe?
- What narrative does the action support or undermine?
- Does the action reveal capabilities or intentions?
- Can deception create a false picture of force posture?
- Will operational security be compromised?
- How might the adversary exploit the event?
- Are words, images, posture, and actions consistent?

## 33. Space support

AFDP 3-14 focuses on Air Force roles and responsibilities in supporting joint space operations and integrating airpower and spacepower.[SRC-25]

Air operations depend on space-enabled capabilities such as:

- positioning, navigation, and timing;
- missile warning;
- communications;
- environmental monitoring;
- intelligence and surveillance;
- command support.

These services may be degraded, denied, or contested. Airmen should plan alternate methods, degraded-mode procedures, and priorities for limited support.

## 34. Sustainment

AFDP 4-0 describes sustainment as the logistics and personnel support required to maintain operations through mission accomplishment and redeployment.[SRC-26]

Air Force sustainment supports:

- force posture;
- basing;
- protection;
- mission generation;
- mission support;
- continued operations;
- recovery and reconstitution.

Core processes include:

- readying the force;
- preparing the operational environment;
- positioning the force;
- employing the force;
- sustaining and recovering the force;
- reconstituting the force.

### 34.1 Mission generation

Combat power is generated through maintenance, munitions, fuel, aircrew, data, support equipment, spares, communications, engineering, security, and medical support.

### 34.2 Logistics under attack

Contested logistics requires:

- dispersion;
- redundancy;
- pre-positioning;
- alternate routes;
- smaller and tailorable packages;
- repair;
- substitution;
- demand reduction;
- prioritization;
- visibility of critical stocks;
- protection of throughput nodes.

### 34.3 The minimum-footprint tension

AFDP 4-0 encourages the minimum footprint consistent with effective operations.[SRC-26] A smaller footprint can improve agility and reduce exposure, but excessive reduction may eliminate resilience, maintenance capacity, repair capability, or endurance.

## 35. Personnel recovery

AFDP 3-50 defines personnel recovery as the combined military, diplomatic, and civil effort to prepare for and execute the recovery and reintegration of isolated personnel and to prevent, plan for, and respond to isolating events.[SRC-27]

Personnel recovery includes:

- preparation;
- planning;
- execution;
- adaptation;
- reintegration.

Recovery operations may require rescue aircraft, special tactics, intelligence, refueling, escort, suppression of enemy defenses, electronic warfare, space support, weather, and coalition capabilities.

Personnel recovery affects operational risk. Commanders may accept greater mission risk when credible recovery capability exists, but recovery missions can also expose additional forces.

## 36. Weather operations

AFDP 3-59 emphasizes two functions:[SRC-28]

- **Environmental characterization:** understanding past, present, and future conditions.
- **Exploitation:** adjusting friendly operations to gain advantage from environmental effects.

Weather affects:

- aircraft performance;
- sensors;
- weapons;
- communications;
- airfields;
- mobility;
- concealment;
- maritime conditions;
- adversary behavior;
- sortie generation.

Weather should be integrated into planning, execution, and assessment. It is not merely a reason to cancel operations; it can create asymmetrical opportunity.

## 37. Legal support

AFDP 3-84 directs legal advisors to integrate throughout planning and execution.[SRC-29] Legal support includes advice on:

- authorities;
- command relationships;
- rules of engagement;
- law of war;
- intelligence law;
- cyber law;
- international law;
- contracts and fiscal law;
- operational access and agreements.

Legal review helps commanders understand available options and constraints. It should not be reduced to a final veto after the plan is complete.

## 38. Public affairs

AFDP 3-61 treats public affairs as an operational capability that contributes to public understanding, credibility, and communication.[SRC-30]

Public communication should be:

- timely;
- accurate;
- aligned with operations;
- coordinated without being misleading;
- attentive to multiple audiences.

Actions communicate even when no statement is issued. Inconsistency between stated intent and observed behavior can create strategic costs.

## 39. Countering weapons of mass destruction

AFDP 3-40 addresses Air Force contributions to deterring WMD use, defending against WMD threats, prevailing in contaminated environments, and cooperating with allies and partners.[SRC-31]

Relevant activities include:

- understanding threats and vulnerabilities;
- deterrence;
- protection;
- consequence management;
- control, defeat, disable, and disposal support;
- recovery of operational capability;
- strategic messaging;
- technical expertise.

## 40. Nuclear operations

AFDP 3-72 addresses Air Force nuclear operations and nuclear command, control, and communications.[SRC-32] Nuclear employment is authorized only by the President, and nuclear planning and command relationships differ significantly from conventional operations.

For a conventional Indo-Pacific wargame, nuclear doctrine should be used primarily to understand:

- escalation;
- strategic deterrence;
- survivable command and control;
- assurance;
- the political significance of certain targets and actions;
- the need to preserve national decision time.

Do not infer nuclear authorization, effects, or options unless explicitly present in the game rules and scenario.

---

# Part V — Agile Combat Employment in an Indo-Pacific Context

## 41. Definition and purpose of ACE

Air Force Doctrine Note 1-21 defines Agile Combat Employment (ACE) as:

> A proactive and reactive operational scheme of maneuver executed within threat timelines to increase resiliency and survivability while generating combat power.[SRC-33]

ACE responds to the vulnerability of operating from a small number of large, predictable bases. It shifts toward a network of dispersed locations that complicates adversary planning, creates more options, and allows forces to generate effects from multiple points.

ACE is not dispersal for its own sake. It is maneuver to preserve and generate combat power.

## 42. ACE logic

ACE seeks to:

- complicate enemy targeting;
- reduce the value of a single successful attack;
- create uncertainty about force location and intent;
- outpace the adversary's decision cycle;
- preserve sortie generation;
- create multiple dilemmas;
- reaggregate effects when required;
- maintain operations under degraded communications;
- expand friendly options.

## 43. ACE enablers

AFDN 1-21 highlights three principal enablers.[SRC-33]

### 43.1 Expeditionary and multi-capable Airmen

Multi-capable Airmen can perform tasks outside a narrow traditional specialty within trained and authorized limits. The purpose is to reduce footprint and increase flexibility, not to eliminate expertise.

### 43.2 Mission command

Dispersed operations require clear intent, delegated authority, shared understanding, and the ability to continue when communications are disrupted.

### 43.3 Tailorable force packages

Force packages should be sized and configured for specific locations, missions, threats, and support conditions. A package may include aircraft, maintenance, munitions, fuel, security, communications, engineering, medical, and command elements.

## 44. ACE operational framework

The Smart Book summarizes ACE through several mutually supporting areas.[SRC-33]

### Posture

Forces require access to multiple locations, integrated capabilities, interoperability, and preparation before crisis.

### Command and control

Mission command supplies the framework. Authorities and communication-loss procedures should be established in advance.

### Movement and maneuver

Forces move within threat timelines to achieve positions of advantage, complicate targeting, and disrupt adversary decision-making.

### Protection

Protection requires layered active and passive defense against aircraft, missiles, unmanned systems, electromagnetic threats, sabotage, and other attacks.

### Sustainment

Innovative logistics and pre-positioned materiel are essential. Dispersal that cannot be supplied becomes self-defeating.

### Information

Movement, posture, deception, signature control, and communication shape adversary perceptions and targeting.

### Intelligence

Intelligence and counterintelligence support rapidly changing basing, warning, threat assessment, and operations in degraded environments.

### Fires

Fires remain connected to objectives and targeting, but mission-type orders and delegated authorities may be necessary to sustain tempo.

## 45. Base clusters and contingency locations

AFDN 1-21 describes a base cluster as a geographically grouped collection of bases organized for mutual protection and ease of command and control.[SRC-34] A cluster may include an enduring location and one or more contingency locations.

A location's value depends on more than runway existence. Consider:

- runway length and condition;
- ramp and parking;
- fuel;
- munitions;
- maintenance;
- communications;
- protection;
- engineering;
- cargo handling;
- access agreements;
- local infrastructure;
- medical support;
- ability to conceal or deceive;
- distance to missions;
- ability to recover from attack.

## 46. Conditions-based authorities

Conditions-based authorities are delegated in advance and become active when specified conditions occur.[SRC-34]

Examples of conditions might include:

- loss of communication;
- missile warning;
- airfield closure;
- loss of a command node;
- a defined adversary movement;
- fuel falling below a threshold;
- a designated target emerging;
- a time limit expiring.

For game analysis, conditions-based logic is useful even when the game does not model formal authorities. A player can formulate branches:

- If the base is threatened, disperse.
- If tankers are lost, shorten the strike plan.
- If air defenses are suppressed, commit the main package.
- If the target moves, shift from deliberate to dynamic targeting.
- If communications are cut, continue under the last priority.

## 47. ACE tradeoffs

ACE creates new costs and risks.

- More locations increase logistics complexity.
- Small teams may have limited repair and defensive capacity.
- Movement consumes time and lift.
- Dispersed stocks can be difficult to protect and track.
- Communications and shared awareness may degrade.
- Some locations have limited sortie-generation capacity.
- Frequent movement can reveal patterns.
- Excessive dispersion can prevent concentration of effects.
- Coalition access may carry political constraints.

Therefore, “disperse” is not automatically the doctrinal answer. The question is whether movement improves survivability and operational options enough to justify the cost.

## 48. Indo-Pacific operational considerations

The Indo-Pacific accentuates doctrinal relationships among:

- distance;
- maritime geography;
- limited basing;
- allied and partner access;
- air and missile threat;
- tanker dependence;
- airlift and sealift constraints;
- fuel and munitions distribution;
- runway repair;
- contested communications;
- space and electromagnetic dependence;
- time-sensitive targeting;
- coalition command and control.

A strong plan treats bases, tankers, airlift, fuel, munitions, C2, sensors, and combat aircraft as one operational system.

---

# Part VI — Doctrine-Informed Analysis of Game Plays

## 49. Start with the objective

Before comparing actions, identify:

- the scenario objective;
- current victory conditions;
- the player's operational objective for this turn;
- the most important condition to create or preserve;
- the main effort;
- the acceptable level of risk.

Do not begin with “What can each unit attack?” Begin with “What must change on the board?”

## 50. Build a board-state operational picture

Extract:

### Friendly system

- combat forces;
- support forces;
- bases and contingency locations;
- damage;
- fuel, munitions, or readiness;
- command and control;
- intelligence and detection;
- mobility;
- protection;
- enablers;
- mission requirements;
- legal actions remaining;
- forces required for future turns.

### Adversary system

- threats to air control;
- strike capability;
- sensors and command nodes;
- bases;
- mobility and logistics;
- high-value enabling assets;
- defended targets;
- likely objectives;
- possible responses.

### Operational environment

- geography and range;
- maritime and land relationships;
- airspace;
- weather if modeled;
- access;
- timing;
- communications;
- rules constraints;
- uncertainty.

## 51. Identify the operational problem

State the problem as a tension, not as a desired action.

Weak formulation:

> “We need to attack the enemy base.”

Stronger formulation:

> “The enemy's protected base is generating sorties that prevent our mobility force from sustaining the forward location, but committing the available strike package would leave our main base exposed.”

The stronger formulation reveals competing requirements and supports COA development.

## 52. Develop at least two distinct COAs

Examples:

### COA A — Gain a temporary air-control window

Prioritize counterair and electromagnetic support, then move or strike during the window.

### COA B — Attack the enabling system

Avoid a costly fighter engagement and target tanker, sensor, logistics, runway, or command dependencies.

### COA C — Disperse and preserve combat power

Use ACE logic to complicate targeting, accept reduced immediate output, and prepare a stronger later turn.

### COA D — Concentrate for a decisive effect

Accept local risk and mass scarce capabilities against the objective that most changes the campaign.

COAs should be truly different, not minor variations of the same target list.

## 53. Wargame each COA

For each COA, walk through:

1. Friendly action.
2. Opponent's most likely response.
3. Friendly counteraction.
4. Opponent's most dangerous response.
5. Resulting board state.
6. Sustainment and readiness next turn.
7. Whether the objective is closer.
8. Whether the force can exploit success.

## 54. Evaluate with doctrinal criteria

Use the following rubric.

### Objective alignment

Does the play directly support the scenario objective or a necessary condition?

### Freedom of action

Does it increase friendly freedom of action or reduce the adversary's?

### Control of the air

Does it obtain the required degree of control at the right time and place?

### Concentration of effects

Does it combine capabilities on the priority, or fragment effort?

### Flexibility

Does it preserve useful options if the situation changes?

### Synergy

Do intelligence, C2, protection, mobility, fires, and sustainment reinforce one another?

### Tempo and initiative

Does the play force the opponent to react, or merely respond to the opponent?

### Dilemmas

Does it present multiple credible threats that cannot all be answered?

### Protection and survivability

Does it preserve critical forces and mission systems?

### Sustainment

Can the force continue after the action?

### Command resilience

Can the plan function with disrupted communications or loss of a node?

### Assessment

Will the player know whether the action achieved its purpose?

### Risk

Is risk accepted deliberately and connected to a higher priority?

## 55. Common doctrinal errors in game analysis

### 55.1 Equating destruction with success

Destroying units is useful only if it creates the required effect.

### 55.2 Treating every available action as equally important

Priority requires deliberately under-resourcing lower-value tasks.

### 55.3 Ignoring enabling assets

Tankers, airlift, sensors, C2, runways, maintenance, and fuel may be more important than shooters.

### 55.4 Seeking air supremacy everywhere

The objective may require only local, temporary superiority.

### 55.5 Overconcentrating forces physically

Physical mass may create a lucrative target. Airpower seeks concentration of effects.

### 55.6 Dispersing without a mission-generation plan

A dispersed force that cannot be fueled, armed, repaired, commanded, or protected is not resilient.

### 55.7 Assuming communications will work

Plans should include degraded-mode actions and delegated decisions.

### 55.8 Ignoring the next turn

A move that spends all munitions, readiness, protection, or mobility may culminate before the objective is secured.

### 55.9 Using doctrine to override the rules

Doctrine explains relationships and tradeoffs. The game's written rules determine legality and resolution.

### 55.10 Treating uncertainty as certainty

State assumptions and identify what information would change the recommendation.

## 56. Mapping common game actions to doctrinal concepts

| Game action or state | Principal doctrinal lens | Questions |
|---|---|---|
| Attack enemy aircraft | Counterair | Does this create the required degree of control, or is the threat regenerated elsewhere? |
| Strike an airbase | Counterair, strategic attack, force generation | Is the effect aircraft destruction, runway denial, sortie delay, or coercion? How durable is it? |
| Attack a surface vessel | Countersea | Does it contribute to maritime superiority, access, protection, or denial? |
| Move to a forward base | ACE, mobility, operational reach | Does the location improve mission options, and can it be sustained and protected? |
| Disperse aircraft | ACE, force protection | Does dispersal reduce vulnerability without making the force ineffective? |
| Use airlift | Rapid global mobility, sustainment | What critical force or supply does it move, and what is the throughput constraint? |
| Use tankers or refueling | Mobility, operational reach | Which missions become possible, and how exposed is the tanker system? |
| Employ ISR | Intelligence and targeting | Which decision uncertainty is reduced, and will information arrive in time? |
| Jam or suppress defenses | EMS operations, counterair, targeting | What corridor or effect does it enable, and for how long? |
| Protect a base | Force protection, counterair, engineer operations | Which mission-critical function is preserved? |
| Repair damage | Engineer operations, sustainment | How quickly does repair restore mission generation? |
| Hold forces in reserve | Flexibility, balance, risk | Which branch, sequel, or adversary response is the reserve intended to address? |
| Concentrate a strike package | Concentration, synergy, strategic attack | Is the target tied to the main objective, and are supporting effects adequate? |
| Recover isolated personnel | Personnel recovery | What additional risk and enabling forces are required? |
| Communicate or delegate orders | Mission command, C2 | Is intent clear, and can execution continue if communications fail? |
| Use deception or concealment | Information, force protection, EMS | What adversary perception or targeting decision is being manipulated? |

## 57. Suggested LLM output template

```markdown
## COAs (the player chooses)

[Present two to four doctrinally cohesive lines of effort. For each: a short
name; the doctrinal purpose with a **specific doctrine-text citation** — section
number + heading + a short **verbatim quote** (e.g. §21.2 "Offensive counterair":
"…"); the **step available now** (legal move by index); and the **intended
sequence** it opens across the ATO (enable → main effort → exploit → assess) with
its branch points. Every line is anchored to real quoted doctrine; never invent a
citation. Each is a plan with the medium-to-longer-term cycle in view, not a
single move. Lay out the tradeoffs and let the player decide — do not dictate a
single "best" line.]

## Rules Check

- Legal actions:
- Required prerequisites:
- Ambiguous rule:
- Assumption:

## Doctrinal Rationale

- Objective:
- Main effort:
- Relevant Air Force functions:
- Relevant tenets:
- Desired effect:
- Why this target/location/action matters:

## Operational Integration

- Intelligence:
- Counterair/protection:
- Command and control:
- Mobility:
- Sustainment:
- Electromagnetic/information support:
- Assessment:

## Adversary Response

- Most likely:
- Most dangerous:
- Friendly counteraction:

## Risk

- Risk to mission:
- Risk to force:
- Opportunity cost:
- Mitigation:

## Alternatives

1. COA A:
2. COA B:

## Confidence

[High / Moderate / Low, with reason.]
```

---

# Part VII — Glossary

**AADC — Area Air Defense Commander:** The commander responsible for overall air and missile defense planning and execution within the assigned area, normally the commander with the required C2 capability.

**ACA — Airspace Control Authority:** The commander designated to assume overall responsibility for airspace control within the joint operations area.

**ACE — Agile Combat Employment:** A proactive and reactive scheme of maneuver within threat timelines to increase resiliency and survivability while generating combat power.

**Air component commander:** The commander responsible for Air Force forces and/or joint air operations under delegated authorities.

**Air interdiction:** Air operations to divert, disrupt, delay, or destroy enemy military potential before it can be effectively used against friendly forces, or otherwise to achieve objectives.

**Air parity:** A condition in which no force has control of the air.

**Air superiority:** A degree of control that permits operations at a particular time and place without prohibitive interference from air and missile threats.

**Air supremacy:** A degree of control in which the opposing force cannot effectively interfere using air and missile threats in the operational area.

**Airpower:** The ability to project military power through control and exploitation in, from, and through the air.

**AOC — Air Operations Center:** The senior theater air-control-system element through which the air component commander plans, directs, and assesses air operations.

**Assessment:** The continuous determination of progress toward objectives and the need to adjust operations.

**C2 — Command and Control:** The exercise of authority and direction by a properly designated commander over assigned and attached forces in accomplishing the mission; doctrinally understood as commander, framework, process, and systems.

**CAS — Close Air Support:** Air action against hostile targets near friendly forces requiring detailed integration with their fire and movement.

**CC-DC-DE:** Centralized Command—Distributed Control—Decentralized Execution.

**COA — Course of Action:** A potential way to accomplish the mission.

**COMAFFOR — Commander, Air Force Forces:** The Air Force commander responsible for Air Force forces and Service responsibilities.

**Counterair:** Offensive and defensive operations to attain and maintain the desired degree of control of the air and protect forces.

**Counterland:** Airpower operations against enemy land-force capabilities to create effects supporting joint objectives.

**Countersea:** Operations to attain and maintain a desired degree of maritime superiority.

**Decentralized execution:** Empowerment of subordinate decision-making to improve flexibility, initiative, and responsiveness.

**Deliberate targeting:** Targeting of planned targets developed in time for a scheduled tasking cycle.

**Distributed control:** Delegation of authorities for planning, coordination, execution, or assessment to dispersed subordinate command elements.

**Dynamic targeting:** Targeting of targets identified too late for deliberate tasking or otherwise requiring action outside the planned cycle.

**Effect:** A physical or behavioral state resulting from an action, set of actions, or another effect.

**Electromagnetic attack:** Use of electromagnetic energy, directed energy, or anti-radiation weapons to deceive, disrupt, degrade, or destroy capability.

**Electromagnetic protection:** Actions that reduce friendly vulnerability to electromagnetic effects.

**Electromagnetic support:** Search, interception, identification, and location of radiated energy for awareness, warning, targeting, or countermeasures.

**End state:** The set of conditions that should exist when an operation is complete.

**Force generation:** The processes through which the Air Force makes ready and presents operational forces.

**Force protection:** Measures to prevent or mitigate hostile or insider actions against personnel, resources, facilities, and critical information.

**Global precision attack:** The ability to hold targets at risk or strike them to create precise effects across domains.

**ISR — Intelligence, Surveillance, and Reconnaissance:** Integrated planning and operation of sensors, assets, and processing and dissemination systems in support of operations.

**JFACC — Joint Force Air Component Commander:** The commander designated by the joint force commander to plan and direct joint air operations using made-available forces.

**JFC — Joint Force Commander:** A commander authorized to exercise command authority over a joint force.

**Main effort:** The designated action, unit, or area whose success is most important at a particular time.

**Mission command:** A philosophy of leadership and C2 that empowers Airmen through trust, shared awareness, and understanding of commander's intent.

**Mission-type order:** An order focused on the purpose and result to be achieved, allowing flexibility in execution.

**Objective:** A clearly defined, decisive, and attainable goal toward which an operation is directed.

**Operational reach:** The distance and duration across which a force can successfully employ capabilities.

**Persistence:** The ability to maintain influence or effects over time.

**Rapid global mobility:** The movement and sustainment of forces through airlift, air refueling, aeromedical evacuation, and supporting systems.

**Risk to force:** The chance of loss or damage to friendly forces and capabilities.

**Risk to mission:** The chance that the objective will not be achieved.

**Strategic attack:** Offensive action against a target specifically selected to achieve strategic objectives.

**Supported commander:** The commander with primary responsibility for an assigned mission or objective.

**Supporting commander:** A commander who provides capabilities or actions to aid the supported commander.

**Target:** An entity or object that performs a function for the adversary and is considered for possible engagement.

**Targeting:** Selecting and prioritizing targets and matching appropriate responses to them in light of operational requirements and capabilities.

**Tenets of airpower:** Mission command, flexibility and versatility, synergistic effects, persistence, concentration, priority, and balance.

---

# Part VIII — Source Notes and Official Publications

## Source policy

Only official Curtis E. LeMay Center materials hosted by `doctrine.af.mil` were used as substantive sources. Publication dates below reflect the official website or the 4 July 2026 Air Force Doctrine Smart Book. The full source publications take precedence over this synthesis.

## Principal sources

### [SRC-01] Air Force Doctrine Smart Book

Curtis E. LeMay Center for Doctrine Development and Education, **Air Force Doctrine Smart Book**, updated 4 July 2026.

- Landing page: https://www.doctrine.af.mil/Operational-Level-Doctrine/SmartBook/
- PDF: https://www.doctrine.af.mil/Portals/61/documents/SmartBook/AFDoctrineSmartBook.pdf

### [SRC-02] AFD35 Doctrine Primer

Curtis E. LeMay Center for Doctrine Development and Education, **AFD35 Doctrine Primer**.

- https://www.doctrine.af.mil/Home/AFD35/AFD35-Doctrine-Primer/

### [SRC-03] AFDP 1, The Air Force

**Air Force Doctrine Publication 1, The Air Force**, 10 March 2021.

- Landing page: https://www.doctrine.af.mil/Operational-Level-Doctrine/AFDP-1-The-Air-Force/AFDP-1-1-Mission-Command/
- PDF: https://www.doctrine.af.mil/Portals/61/documents/AFDP_1/AFDP-1.pdf

### [SRC-04] AFDP 3-0, Operations

**Air Force Doctrine Publication 3-0, Operations**, 22 January 2025.

- Landing page: https://www.doctrine.af.mil/Doctrine-Publications/AFDP-3-0-Operations/
- PDF: https://www.doctrine.af.mil/Portals/61/documents/AFDP_3-0/AFDP3-0Operations.pdf

### [SRC-05] AFDP 3-0, Operations — coercion discussion

Same publication as [SRC-04], especially the discussion of deterrence, compellence, denial, risk, and punishment.

### [SRC-06] AFDP 1-1, Mission Command

**Air Force Doctrine Publication 1-1, Mission Command**, 14 August 2023.

- Landing page: https://www.doctrine.af.mil/Operational-Level-Doctrine/AFDP-1-1-Mission-Command/
- PDF: https://www.doctrine.af.mil/Portals/61/documents/AFDP_1-1/AFDP%201-1%20Mission%20Command.pdf

### [SRC-07] AFDP 3-0.1, Command and Control — distributed control

**Air Force Doctrine Publication 3-0.1, Command and Control**, 22 January 2025.

- Landing page: https://www.doctrine.af.mil/Operational-Level-Doctrine/AFDP-3-01-Command-and-Control/
- PDF: https://www.doctrine.af.mil/Portals/61/documents/AFDP_3-0_1/AFDP3-0.1CommandandControl.pdf

### [SRC-08] AFDP 3-0.1, Command and Control — C2 function

Same publication as [SRC-07].

### [SRC-09] AFDP 3-0.1 and AFDP 3-01

The AOC and theater air control system discussion is synthesized from AFDP 3-0.1 and the Smart Book synopsis of AFDP 3-01.

### [SRC-10] AFDP 5-0, Planning

**Air Force Doctrine Publication 5-0, Planning**, 22 January 2025.

- Landing page: https://www.doctrine.af.mil/Operational-Level-Doctrine/AFDP-5-0-Planning/
- PDF: https://www.doctrine.af.mil/Portals/61/documents/AFDP_5-0/AFDP5-0Planning.pdf

### [SRC-11] AFDP 2-0, Intelligence

**Air Force Doctrine Publication 2-0, Intelligence**, 1 May 2026.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-12] AFDP 3-60, Targeting

**Air Force Doctrine Publication 3-60, Targeting**.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-13] AFDP 3-01, Counterair Operations

**Air Force Doctrine Publication 3-01, Counterair Operations**, 15 June 2023.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-14] AFDP 3-02, Strategic Attack

**Air Force Doctrine Publication 3-02, Strategic Attack**, 27 August 2025.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-15] AFDP 3-03, Counterland Operations

**Air Force Doctrine Publication 3-03, Counterland Operations**, 31 October 2024.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-16] AFDP 3-04, Countersea Operations

**Air Force Doctrine Publication 3-04, Countersea Operations**.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-17] AFDP 3-36, Air Mobility Operations

**Air Force Doctrine Publication 3-36, Air Mobility Operations**.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-18] AFDP 3-05, Special Operations

**Air Force Doctrine Publication 3-05, Special Operations**, 31 October 2024.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-19] AFDP 3-10, Force Protection

**Air Force Doctrine Publication 3-10, Force Protection**.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-20] AFDP 3-34, Engineer Operations

**Air Force Doctrine Publication 3-34, Engineer Operations**, 20 March 2026.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-21] AFDP 3-52, Airspace Control

**Air Force Doctrine Publication 3-52, Airspace Control**.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-22] AFDP 3-12, Cyberspace Operations

**Air Force Doctrine Publication 3-12, Cyberspace Operations**.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-23] AFDP 3-85, Electromagnetic Spectrum Operations

**Air Force Doctrine Publication 3-85, Electromagnetic Spectrum Operations**, 14 December 2023.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-24] AFDP 3-13, Information in Air Force Operations

**Air Force Doctrine Publication 3-13, Information in Air Force Operations**, 1 May 2026.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-25] AFDP 3-14, Space Support

**Air Force Doctrine Publication 3-14, Space Support**.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-26] AFDP 4-0, Sustainment

**Air Force Doctrine Publication 4-0, Sustainment**, 1 May 2026.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-27] AFDP 3-50, Personnel Recovery

**Air Force Doctrine Publication 3-50, Personnel Recovery**, 26 September 2025.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-28] AFDP 3-59, Weather Operations

**Air Force Doctrine Publication 3-59, Weather Operations**, 26 September 2025.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-29] AFDP 3-84, Legal Support

**Air Force Doctrine Publication 3-84, Legal Support**, 31 October 2024.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-30] AFDP 3-61, Public Affairs

**Air Force Doctrine Publication 3-61, Public Affairs**.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-31] AFDP 3-40, Countering Weapons of Mass Destruction Operations

**Air Force Doctrine Publication 3-40, Countering Weapons of Mass Destruction Operations**, 1 May 2026.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-32] AFDP 3-72, Nuclear Operations

**Air Force Doctrine Publication 3-72, Nuclear Operations**, 14 January 2026.

- Official publication index: https://www.doctrine.af.mil/
- Synopsis: [SRC-01]

### [SRC-33] AFDN 1-21, Agile Combat Employment

**Air Force Doctrine Note 1-21, Agile Combat Employment**, 23 August 2022.

- Landing page: https://www.doctrine.af.mil/Operational-Level-Doctrine/AFDN-1-21-Agile-Combat-Employment/
- PDF: https://www.doctrine.af.mil/Portals/61/documents/AFDN_1-21/AFDN%201-21%20ACE.pdf

### [SRC-34] AFDN 1-21 — base clusters and conditions-based authorities

Same publication as [SRC-33].

---

# Final Use Note

This file is a doctrine reference, not an official LeMay Center publication and not an official interpretation of Air Force Wargame Indo-Pacific. It is a structured synthesis intended to help an LLM reason more faithfully about airpower. When precision matters, consult the cited full publications at `doctrine.af.mil`.
