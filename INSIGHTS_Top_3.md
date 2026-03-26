# LILA BLACK — Level Design Insights
## Three Things the Data Revealed About the Game

> Derived from 5 days of production gameplay data (Feb 10–14, 2026) across 3 maps,
> 796 matches, 245 human players, and 89,104 recorded events.

---

## Insight 1 — The Game Is Not Being Played as a PvP Game

### What caught my eye

When I filtered the Stats tab to show only Kill and BotKill events side by side, something immediately looked wrong. The "Human vs Bot Events" chart was almost entirely one colour. I pulled the raw numbers: **3 human-vs-human kills across 796 matches and 245 players.** That is not a rounding error — it is a near-total absence of PvP.

### Back it up

| Event | Count | % of all kills |
|---|---|---|
| BotKill — human kills bot | 2,415 | 99.9% |
| Kill — human kills human | 3 | 0.1% |

Humans outnumber bots 2.6x (245 humans vs 94 bots). Despite this, bots account for essentially every kill in the game. To put it another way: across 796 matches, the average match produced **0.004 human-vs-human kills.** Players are not encountering each other — or if they are, they are not surviving long enough to fight.

The Map View heatmap reinforces this. Kill zones cluster in the map centre (34.1% of all AmbroseValley kills in one central 200×200px zone), which is exactly where bots spawn and patrol. Human players are being eliminated by bots before they can reach other humans.

### What is actionable

**Metrics that will be affected:**
- Human-vs-human kill rate (current: 0.1% → target: above 5%)
- Daily active event count (currently declining 33%/day — likely linked)
- Player retention (players killed repeatedly by bots do not return)

**Actionable items:**
1. Reduce bot aim accuracy and engagement range by 20–30% and retest KD ratio
2. Review bot spawn density in central zones — move some bots to map periphery
3. Conduct a design alignment session: is LILA BLACK PvP-first or PvE-first? The answer changes everything about bot tuning, map layout, and spawn logic

### Why a Level Designer should care

Map design is built around the assumption of where player interactions happen. If PvP is the goal, the current map layouts are failing it — bots are eliminating players before human encounters develop. Every sightline, chokepoint, and cover placement decision was presumably made to serve player-vs-player combat. Right now none of it is being tested by real gameplay. A Level Designer cannot iterate meaningfully on PvP encounter design when there are effectively zero PvP encounters happening.

---

## Insight 2 — GrandRift Is Being Abandoned and the Data Shows Why

### What caught my eye

When I used the date filter on the Timeline tab and compared match counts by map, one number stood out immediately: GrandRift had 59 matches across 5 days. AmbroseValley had 566. I then checked the bot ratio on the Stats tab and found something that should not be possible in a game designed for human players — GrandRift has more unique bots than unique human players.

### Back it up

| Map | Human Players | Bots | Bot:Human Ratio | Matches |
|---|---|---|---|---|
| AmbroseValley | 217 | 51 | 0.2x | 566 |
| Lockdown | 79 | 41 | 0.5x | 169 |
| **GrandRift** | **29** | **30** | **1.0x** | **59** |

29 unique humans across 59 matches = an average of **0.5 humans per match.** Many GrandRift matches had zero human players — they were bot-only sessions. Compounding this, GrandRift has the highest storm death rate (9.6% vs AmbroseValley's 3.4%), meaning the players who do join face both immediate bot aggression and a fast-closing storm. The map is the hardest environment in the game and it has the fewest players.

The Heatmap tab (Kill Zones overlay, GrandRift selected) shows kills concentrated in a narrow central corridor — 33.2% of kills in one zone, with a secondary cluster in the south-central corridor at 15.5%. Players are being funnelled into a killing field.

### What is actionable

**Metrics that will be affected:**
- GrandRift match count (current: 59 → target: comparable to Lockdown at 169+)
- Human player count on GrandRift (current: 29 → target: 60+ within 2 weeks of fix)
- Storm death % on GrandRift (current: 9.6% → target: below 5%)

**Actionable items:**
1. Extend GrandRift storm timer by 20% — players need more time to establish before the zone closes
2. Reduce bot count on GrandRift temporarily (from 30 to 15 unique bots) to give human players room to survive
3. Add high-value loot near human spawn points — the current loot distribution (880 pickups, 14.9/match) is reasonable but players are being eliminated before they reach it
4. Investigate the south-central kill corridor in the Heatmap — there may be a structural chokepoint creating a spawn-camp scenario

### Why a Level Designer should care

GrandRift is functionally not being played by humans. Any design work done on this map — cover placement, loot distribution, sightlines, verticality — is being tested only by bots following scripted behaviour. That means the Level Designer is receiving no real signal about whether the map works. Until human retention on GrandRift improves, design iteration on this map is flying blind. Fixing the bot count and storm timer is not just a game balance fix — it is a prerequisite for getting any useful design feedback on this map at all.

---

## Insight 3 — Player Engagement Is in Freefall and the Window to Act Is Narrow

### What caught my eye

The Events per Day chart on the Stats tab showed a pattern I have not seen in healthy game data: a perfectly consistent one-third drop every single day. Not a weekend dip, not a one-day anomaly — a sustained, steep, daily decline starting from day one of the dataset.

### Back it up

| Date | Game Events | Daily Drop | Cumulative Drop |
|---|---|---|---|
| Feb 10 | 6,170 | baseline | — |
| Feb 11 | 4,110 | −33% | −33% |
| Feb 12 | 2,951 | −28% | −52% |
| Feb 13 | 1,969 | −33% | −68% |

In three days the game lost **68% of its daily activity.** This is not noise. A random fluctuation would produce uneven drops — some days flat, some down, maybe one up. Three consecutive drops of approximately one-third each point to a systematic cause. The most likely candidate — supported by Insight 1 — is that players try the game, are killed repeatedly by bots without meaningful counterplay, and do not come back.

Cross-referencing with the Timeline tab: match durations on AmbroseValley (median 362s, max 890s) show that some players are persisting for meaningful sessions. The players who stay are having a different experience than the players who leave. The gap between the top 5 killers (Player 1: 227 kills, Player 2: 201 kills) and the average player strongly suggests a skill or knowledge gap that new players cannot bridge.

### What is actionable

**Metrics that will be affected:**
- Daily active events (current trajectory: near-zero by Feb 17 if unchanged)
- D1 retention rate (estimated below 33% based on Feb 10 → Feb 11 drop)
- Match count per day (directly tracks whether intervention works)

**Actionable items:**
1. **Immediate (this week):** Reduce bot aggression across all maps — this is the highest-probability cause and the lowest-effort fix. Recheck daily event counts after 3 days
2. **Short term (2 weeks):** Add a tutorial or first-match protection mode — new players should not face the same bot density as experienced players
3. **Measurement:** Instrument distinct user sessions per day (the current dataset does not distinguish new vs returning players — this data gap should be closed in the next build)
4. **Cross-reference:** Pull server deployment logs for Feb 10–13 to rule out a patch-related cause before committing to a bot tuning sprint

### Why a Level Designer should care

Retention data is the most direct feedback a Level Designer can receive about whether their maps are working. A 68% drop in 3 days means that whatever experience the maps are creating, it is not compelling enough to bring players back. Level Designers often receive feedback in the form of playtests or qualitative notes — this is quantitative evidence that something in the first-session experience is broken. Until retention stabilises, every other design metric (kill zone distribution, loot placement, match duration) is being measured on a shrinking and unrepresentative player population. Fixing retention is not just a growth concern — it is a prerequisite for collecting reliable design data.

---

## Dataset Limitations

- **5 days only** — trends may reflect launch volatility rather than stable behaviour
- **Feb 14 is partial** — excluded from daily trend analysis
- **No new vs returning player distinction** — cannot confirm if the decline is the same players churning or no new players joining
- **Bot deaths not recorded as victim events** — KD ratios are not directly comparable to PvP games
- **3 human kills total** — PvP analysis has no statistical significance; treated as a product signal only
