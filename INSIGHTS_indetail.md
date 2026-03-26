# LILA BLACK — Level Design Insights
## Player Behaviour Analysis: Feb 10–14, 2026

---

## Dataset at a Glance

| Metric | Value |
|---|---|
| Total records | 89,104 |
| Game events (excl. movement) | 16,045 |
| Unique matches | 796 |
| Human players | 245 |
| Bots | 94 |
| Date range | Feb 10–14 (Feb 14 partial) |

---

## ⚠️ The Single Biggest Finding: Humans Are Not Killing Each Other

Across all 796 matches and 245 human players, **only 3 human-vs-human kills were recorded** out of 2,418 total kills.

**99.9% of all kills were bots killing players (BotKill: 2,415).**

This is not a balancing issue — this is a **fundamental design question**: is LILA BLACK intended to be a PvP game or a PvE game? If PvP combat is a design goal, it is effectively not happening in production. This is the most important finding in this entire report and should be escalated immediately.

---

## Finding 1 — Bots Are Dominating the Kill Economy

| Event | Count | % of kills |
|---|---|---|
| BotKill (bot kills player) | 2,415 | 99.8% |
| Kill (human kills human) | 3 | 0.1% |

Players are almost exclusively being killed by bots, not each other. With 245 humans vs 94 bots, humans outnumber bots 2.6x — yet bots account for virtually all kills. Bots are either too aggressive, too accurate, or positioned too advantageously relative to human spawns.

**Recommendation:**
- Audit bot AI aggression settings — particularly aim accuracy and engagement range
- Review bot spawn locations relative to human spawn points on all three maps
- Decide as a product team: is the intended engagement loop PvP-first or PvE-first, and tune accordingly

---

## Finding 2 — Player Engagement Is Declining Sharply Every Day

| Date | Game Events | Change |
|---|---|---|
| Feb 10 | 6,170 | baseline |
| Feb 11 | 4,110 | −33% |
| Feb 12 | 2,951 | −28% |
| Feb 13 | 1,969 | −33% |
| Feb 14 | 845 | partial day |

**In 4 days, daily game events dropped by 68%.** A consistent one-third daily decline is not noise — this is a retention signal that needs immediate attention.

**Recommendation:**
- Identify the drop-off point in the player journey — is it after the first session or the second?
- Cross-reference with any patches deployed between Feb 10–13
- Bot difficulty (Finding 1) is the most likely cause — players being killed relentlessly by bots and not returning

---

## Finding 3 — Kill Zones Are Heavily Centralised on Every Map

All three maps show kills concentrated in the central zone (400–600px × 400–600px).

| Map | Central zone kills | % of all kills |
|---|---|---|
| AmbroseValley | 614 | **34.1%** |
| GrandRift | 64 | **33.2%** |
| Lockdown | 184 (two adjacent zones) | **43.2%** |

One-third to nearly half of all kill activity happens in a small central region of every map. The outer thirds are effectively dead zones — players have no incentive to spread out.

**Recommendation:**
- Place high-value loot in outer map zones to incentivise peripheral movement
- Review cover distribution — central zones may offer the best cover, making them self-reinforcing
- GrandRift shows a secondary cluster at the south-central corridor — examine for chokepoints

---

## Finding 4 — GrandRift Has Effectively Become a Bot-Only Map

| Map | Humans | Bots | Ratio | Matches |
|---|---|---|---|---|
| AmbroseValley | 217 | 51 | 0.2x | 566 |
| Lockdown | 79 | 41 | 0.5x | 169 |
| **GrandRift** | **29** | **30** | **1.0x** | **59** |

GrandRift is the only map where bots match or outnumber humans. With only 29 unique humans across 59 matches, it averages roughly 0.5 humans per match. Players are avoiding this map entirely.

**Recommendation:**
- Investigate why human players are not choosing GrandRift — map visibility in the UI, difficulty, or early negative experience
- With a 9.6% storm death rate (highest of all maps), GrandRift may feel doubly punishing — bot pressure plus storm pressure
- Consider temporarily reducing GrandRift bot count to attract human players back

---

## Finding 5 — Storm Deaths Signal Pacing Problems on Two Maps

| Map | Storm Death % | Assessment |
|---|---|---|
| AmbroseValley | 3.4% | ✅ Healthy — storm is background pressure |
| Lockdown | 9.2% | ⚠️ Storm may be closing too fast |
| GrandRift | 9.6% | ⚠️ Storm combined with bot pressure feels unfair |

AmbroseValley's 3.4% is the benchmark — the storm creates urgency without being the primary killer. Lockdown and GrandRift at ~9-10% suggest players are being caught by the storm rather than choosing to engage.

**Recommendation:**
- Extend the safe zone timer on Lockdown and GrandRift by 15–20%
- For GrandRift specifically, players under constant bot pressure shouldn't also be racing the storm

---

## Finding 6 — Loot Per Match Is Reasonable but GrandRift Players Can't Reach It

| Map | Loot Pickups | Per Match |
|---|---|---|
| AmbroseValley | 9,955 | 17.6 |
| Lockdown | 2,050 | 12.1 |
| GrandRift | 880 | 14.9 |

Loot per match is broadly consistent across maps. However given GrandRift's near-zero human population (Finding 4), low absolute loot numbers suggest humans are being eliminated before collecting loot — not that loot is absent.

**Recommendation:**
- Move some GrandRift loot closer to human spawn points to give players a fighting chance before first bot contact
- Use the Heatmap tool (Loot Zones vs High Traffic overlay) to verify loot placement aligns with where players actually travel

---

## Finding 7 — Match Duration Is Healthy on AmbroseValley, Slow on Lockdown

| Map | Median Duration | Min | Max |
|---|---|---|---|
| AmbroseValley | **362s (6 min)** | 13s | 890s |
| GrandRift | 422s (7 min) | 30s | 732s |
| Lockdown | **448s (7.5 min)** | 32s | 825s |

The very short minimum durations (13–32s) are likely disconnections or instant eliminations — outliers, not genuine sessions. Excluding these, match durations are reasonable. Lockdown's higher median combined with its higher storm death rate (Finding 5) suggests matches run long enough that the storm becomes a significant factor.

---

## Finding 8 — One Player Accounts for 9.4% of All Bot Kills

| Player | Kills | % of all BotKills |
|---|---|---|
| 94d042cb... | 227 | 9.4% |
| 10648aa3... | 201 | 8.3% |
| a0738c7c... | 79 | 3.3% |
| e7ac0138... | 69 | 2.9% |
| f4e072fa... | 65 | 2.7% |

The top 2 players alone account for **17.7% of all bot kills** in the entire dataset. Given that total human-vs-human kills are only 3, these are almost entirely PvE kills. This level of concentration suggests either a dominant map position is being exploited, or these players represent an extreme skill ceiling that is unreachable for the average player.

**Recommendation:**
- Use the Timeline tab to replay matches involving player 94d042cb (94d042cb-a0f...) and observe movement patterns
- If they are consistently exploiting a specific position, address that zone's cover and sightlines
- Consider whether the skill gap between top and average players is too wide for a healthy matchmaking pool of 245 players

---

## Map Comparison at a Glance

| Metric | AmbroseValley | Lockdown | GrandRift | Best |
|---|---|---|---|---|
| Matches | 566 | 169 | 59 | AmbroseValley |
| Human players | 217 | 79 | 29 | AmbroseValley |
| Bot:Human ratio | 0.2x | 0.5x | 1.0x | AmbroseValley |
| KD ratio | 3.56 | 2.30 | 3.71 | — |
| Storm death % | 3.4% | 9.2% | 9.6% | AmbroseValley |
| Loot per match | 17.6 | 12.1 | 14.9 | AmbroseValley |
| Median match duration | 362s (6 min) | 448s (7.5 min) | 422s (7 min) | AmbroseValley |
| Central zone kill % | 34.1% | 43.2% | 33.2% | GrandRift (least concentrated) |

**AmbroseValley is the healthiest map across almost every dimension.** GrandRift is the most concerning — equal bot:human ratio, highest storm death rate, fewest matches, and fewest human players. Lockdown sits in between but has a storm pacing problem. If the team can only fix one map before next review, **GrandRift** should be the priority.

---

## Priority Action List

| Priority | Action | Success Metric | Finding |
|---|---|---|---|
| 🔴 P0 | Clarify PvP vs PvE design intent — only 3 human kills recorded | Decision documented within 1 sprint | Finding 1 |
| 🔴 P0 | Investigate 33%/day engagement decline — retention emergency | Identify root cause within 1 week; halt decline within 2 weeks | Finding 2 |
| 🔴 P0 | Reduce bot AI aggression on all maps | Human-vs-human kill rate above 5%; daily event drop halted | Finding 1 |
| 🔴 P0 | Investigate GrandRift abandonment — 29 humans vs 30 bots | Human player count on GrandRift doubles within 2 weeks of fix | Finding 4 |
| 🟡 P1 | Redistribute loot and cover to peripheral map zones | Central zone kill % drops below 25% on all maps | Finding 3 |
| 🟡 P1 | Extend storm timer on Lockdown and GrandRift by 15–20% | Storm death % drops to below 5% on both maps | Finding 5 |
| 🟡 P1 | Replay player 94d042cb matches — investigate position exploit | Confirm or rule out exploit within 3 days | Finding 8 |
| 🟢 P2 | Move GrandRift loot closer to human spawn points | Loot per match on GrandRift reaches 15+ | Finding 6 |
| 🟢 P2 | Review Lockdown match pacing | Median match duration reduces to under 400s | Finding 7 |

---

## Data Limitations

- **5 days is a short window** — trends may reflect launch volatility, not stable long-term behaviour
- **Feb 14 is a partial day** — event counts are lower by definition, excluded from daily trend analysis
- **Bot behaviour is scripted** — bot kill/death patterns reflect AI tuning, not organic player decisions
- **No session continuity data** — we cannot confirm whether the daily decline reflects the same players churning or different players each day
- **3 human kills total** — PvP analysis is statistically meaningless at this sample size; this is a product signal, not a statistical finding worth modelling