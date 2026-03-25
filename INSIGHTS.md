# LILA BLACK — Level Design Insights
## Player Behaviour Analysis: Feb 10–14, 2026

---

## Dataset Summary

| Metric | Value |
|---|---|
| Total records | 89,104 |
| Date range | Feb 10–14, 2026 (Feb 14 partial) |
| Maps | AmbroseValley, GrandRift, Lockdown |
| Unique matches | ~796 |
| Human players | ~245 unique |
| Bots | ~71 unique |
| Event types | 8 |

---

## How to Read These Insights

These findings are derived from 5 days of production gameplay data. All observations should be validated against larger datasets before making design changes. Where sample sizes are small (e.g. single-day or single-match views), treat findings as hypotheses to investigate rather than confirmed conclusions.

**Feb 14 data is incomplete** — it represents a partial day of recording. Any comparisons involving Feb 14 should account for the lower event volume.

---

## Finding 1 — Storm Deaths Are a Design Signal

Across all maps, a meaningful percentage of deaths are caused by the storm rather than by other players or bots. This is worth monitoring closely.

**Why it matters for Level Design:**
- A high storm death rate (>20%) suggests the playable zone shrinks too aggressively — players are being eliminated by the environment rather than by gameplay decisions
- A very low storm death rate (<5%) suggests the storm is not creating enough pressure to drive player movement and encounters
- The ideal range creates tension without feeling unfair

**What to do:** Use the Stats tab → filter by individual map → check the Quick Read summary for storm death percentage per map. Compare across maps to identify which map's storm timing may need tuning.

---

## Finding 2 — Bot Kill Ratio Varies by Map

The ratio of human kills to bot kills differs noticeably across maps, suggesting bot difficulty or spawn density is not consistent across the three environments.

**Why it matters for Level Design:**
- If bots kill humans far more than humans kill bots on a specific map, that map's bot placement, bot AI aggression, or cover distribution may be giving bots an advantage
- The reverse — humans dominating bots completely — means bots aren't creating meaningful challenge and the map may feel empty once human opponents are eliminated

**What to do:** Use the Stats tab → filter by each map individually → check the "Are bots and humans balanced?" section. The insight callout shows the kill counts and a balance verdict directly.

---

## Finding 3 — Kill Clustering Indicates Hot Zones

The Map View and Heatmap tabs consistently reveal that kills are not distributed evenly across maps. They cluster in specific areas, which is expected but worth monitoring for extremity.

**Why it matters for Level Design:**
- Moderate clustering around cover, chokepoints, and high-loot areas is healthy — it creates memorable moments and predictable engagement zones
- Extreme clustering (one area accounts for >40% of kills) suggests a dominant position that overshadows the rest of the map — players who control that zone have a disproportionate advantage
- Dead zones (large map areas with no kills at all) may indicate poor pathing incentives or lack of loot that draws players there

**What to do:** Open the Heatmap tab → select Kill Zones → compare across dates. Persistent hotspots that appear across all 5 days are structural map features, not noise.

---

## Finding 4 — Loot Distribution Should Mirror Traffic

The Loot Zones heatmap should roughly correlate with the High Traffic heatmap. Where players spend time, loot should be available. When these two maps diverge significantly, it suggests a mismatch between player movement and resource placement.

**Why it matters for Level Design:**
- If players traffic an area heavily but loot density is low there, players are moving through without finding resources — potentially frustrating
- If loot is concentrated in an area players don't naturally visit, the loot placement is wasted and may need to be redistributed

**What to do:** Toggle between High Traffic and Loot Zones overlays on the Heatmap tab for the same map. Look for areas where one is high and the other is low.

---

## Finding 5 — Match Duration Distribution

The Timeline tab reveals how long matches actually last. A healthy match duration provides enough time for multiple combat engagements without overstaying.

**Why it matters for Level Design:**
- Very short matches (under 2 minutes) suggest the storm closes too fast or initial spawns are placing players too close together
- Very long matches (over 15 minutes) may indicate too much map area, low player density, or a storm that moves too slowly

**What to do:** Load several matches in the Timeline tab and observe the slider range (match duration). Compare across maps — some maps may systematically produce shorter or longer matches.

---

## Finding 6 — Player Activity Drops at Match Start and End

The Event Density histogram in the Timeline tab consistently shows a pattern: low activity at the very start of a match (players landing and looting), a peak activity phase (combat), and a drop-off at the end (fewer surviving players).

**Why it matters for Level Design:**
- The opening phase length tells you how long players take to arm themselves before first contact — if this is too long, early game feels passive
- The peak activity timing tells you when most combat occurs — this should ideally not be too early (players haven't found gear) or too late (map is too large)

**What to do:** Load a representative match in the Timeline tab. Observe the histogram — the first visible spike of kill events marks the end of the opening phase. Scrub to that point on the map to see where first contact happens.

---

## Finding 7 — Cross-Midnight Match

One match spans both Feb 10 and Feb 11 (it started late on Feb 10 and finished on Feb 11). This match appears in the dropdown with both dates in its label. When selecting only Feb 10 or only Feb 11, this match is visible in both — this is expected behaviour, not a data error.

This match may have extended match duration or unusual player retention worth investigating in the Timeline tab.

---

## Recommendations for Level Designers

### Immediate Actions

1. **Identify dominant kill zones on each map** — use Heatmap → Kill Zones → compare all 5 days. Any zone that appears consistently hot across all days is a structural issue, not a statistical quirk.

2. **Check storm death percentage per map** — use Stats tab → filter by map → read the Quick Read callout. Maps with storm death >20% may need storm timing adjustment.

3. **Compare loot vs traffic distribution** — use Heatmap → toggle between High Traffic and Loot Zones for each map. Identify mismatches.

### Investigations to Conduct

1. **Replay the highest-kill matches** — use Stats tab → Top 10 Human Killers → Player ID Lookup → copy UUID → use in Timeline tab to watch that player's match. Outlier performers may be exploiting positional advantages.

2. **Compare maps side by side** — run Stats tab filtered to each map in separate browser tabs. The Quick Read callout gives instant KD ratio, bot ratio, and storm death percentage for direct comparison.

3. **Look at Feb 14 data in isolation** — it's a partial day so volume is lower, but the patterns that appear may be earlier-day players who return consistently, which is a useful engagement signal.

---

## Limitations of This Dataset

- **5 days is a short window** — patterns may reflect a specific meta, patch state, or player cohort rather than stable behaviour
- **Bot behaviour is scripted** — bot kills and deaths reflect AI tuning, not organic player decisions. Weight human-vs-human events more heavily for design decisions
- **Feb 14 is partial** — all Feb 14 event counts are lower than other days by definition
- **Match timestamps are player-relative** — the Timeline tab normalizes per player, meaning players who joined mid-match have their timeline starting from their join point, not the match start
- **No session-level data** — we can't tell if a player played multiple matches per day or if they won/lost, only what events occurred
