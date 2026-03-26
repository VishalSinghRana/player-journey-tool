# LILA BLACK — Architecture One-Pager

---

## What I Built With and Why

| Tool | Why I Picked It |
|---|---|
| **Streamlit** | Browser-based with no frontend code — Level Designers can use it without installing anything. Deploys to a public URL in minutes. |
| **Plotly** | Interactive maps and charts out of the box — scroll to zoom, hover tooltips, click-to-filter. No JavaScript needed. |
| **Pandas** | All filtering is boolean masking on an in-memory DataFrame — fast enough for 89K rows, no database needed. |
| **NumPy** | `np.histogram2d` for heatmap density calculation — one function call, no custom binning logic. |
| **Parquet** | Columnar format — reading only the columns needed is 10x faster than CSV for this schema. |
| **Streamlit Community Cloud** | Free, auto-deploys on every `git push`, no DevOps required. Right tool for a prototype. |

---

## How Data Flows from Parquet Files to the Screen

```
1,243 raw parquet files  (one per player per match, across 5 day folders)
         ↓
   preprocess.py  — run once
         • Parses filenames → extracts user_id, match_id, is_bot
         • Decodes event bytes to strings
         • Transforms world coordinates → pixel coordinates
         • Tags each row with date, map_id, is_partial_day
         • Concatenates all files → saves data/all_events.parquet
         ↓
   data/all_events.parquet  (89,104 rows · 15 columns · 2.8MB)
         ↓
   load_data()  — runs once per session, cached with @st.cache_data
         • Reads parquet into memory
         • Converts ts column to numeric (see Assumptions)
         • Creates date_str column ("Feb 10" etc.)
         • Sorts by ts
         ↓
   In-memory DataFrame  — shared across all 4 tabs
         ↓
   Tab renders  — each tab filters the DataFrame, caches results in
   session state, and builds Plotly figures on demand
```

---

## How I Mapped Game Coordinates to the Minimap

The game engine stores positions as world coordinates `(x, z)` — a 3D space where `y` is vertical height and is ignored for 2D map overlay. Each map has a different origin point and scale, so a direct pixel mapping would place events in the wrong location.

**The transform:**

```
u       = (x − origin_x) / scale          # normalise to [0, 1]
v       = (z − origin_z) / scale          # normalise to [0, 1]
pixel_x = u × 1024
pixel_y = (1 − v) × 1024                  # Y axis flipped — game Z increases upward,
                                           # screen Y increases downward
```

**The Y flip was the tricky part.** In the game engine, increasing Z moves the player "north" (up on the minimap). On screen, increasing Y moves pixels downward. Without `(1 − v)`, every event would appear mirrored vertically — kills at the top of the map would show at the bottom of the image.

**Per-map parameters:**

| Map | Scale | Origin X | Origin Z |
|---|---|---|---|
| AmbroseValley | 900 | −370 | −473 |
| GrandRift | 581 | −290 | −290 |
| Lockdown | 1000 | −500 | −500 |

These values were derived by cross-referencing known landmark positions in the game with their minimap image coordinates and solving for origin and scale.

---

## Assumptions I Made Where the Data Was Ambiguous

**1. The `ts` timestamp column**
The parquet schema tagged `ts` as `datetime64[ms]`. When pandas read it that way, a match of 480 seconds appeared to last 480 milliseconds — making every match duration show as under 1 second. I overrode the schema with `pd.to_numeric()` at load time, treating `ts` as plain float seconds. Confirmed correct by checking that median match duration (362s) aligns with expected battle royale gameplay length.

**2. Per-player timestamp normalisation**
Each player's parquet file records `ts` starting from when that player joined — not from a shared match clock. A player who joined 30 seconds late starts at `ts ≈ 0`, not `ts ≈ 30`. I normalised per player: `elapsed_s = ts − ts.min()` per `user_id_from_file`. This means "elapsed seconds since that player started" rather than "elapsed seconds since match started" — a limitation acknowledged in the documentation.

**3. Bot detection**
The raw data has no `is_bot` column. I inferred it from filename format: UUID-format user IDs are human players, numeric user IDs are bots. This assumption holds across all 1,243 files and is consistent with 94 unique bots and 245 unique humans — plausible numbers for the dataset.

**4. February 14 partial day**
Feb 14 has significantly fewer events than other days. I flagged it as `is_partial_day = True` and excluded it from daily trend percentage calculations rather than treating the lower count as a player behaviour signal. Stats tab annotates the Feb 14 bar explicitly.

**5. Cross-midnight match**
One match has events tagged with both Feb 10 and Feb 11 dates. Rather than arbitrarily assigning it to one day, I show it in both individual date selections and display its label as "Feb 10 & Feb 11". When both dates are selected together it appears once (337 matches, not 338 — correct).

---

## Major Tradeoffs

| Decision | Option Considered | What I Chose | Why |
|---|---|---|---|
| **Data storage** | Database (DuckDB, SQLite) | In-memory pandas DataFrame | 89K rows fits comfortably in RAM. No query latency, simpler deployment — no DB file to manage. |
| **Map figure rendering** | Rebuild on every interaction | Cache figure in session state by filter hash | Rebuilding a Plotly figure with 50K+ path points takes 3–8 seconds. Caching makes the UI feel instant after first load. |
| **Timeline playback** | Full video export (MP4) | Scrub slider + jump buttons | Video export requires kaleido + imageio, takes 3–8 minutes to generate, and needs background processing. Slider gives immediate interactivity with zero wait time. Deferred video export to v2. |
| **Path rendering** | One trace per player | Two traces (human + bot) with None separators | One trace per player = hundreds of Plotly traces = slow render. Batching into 2 traces with None gaps (Plotly convention for line breaks) reduces render time by ~10x. |
| **Heatmap colours** | Custom transparent-to-colour scales | Named Plotly scales (Reds, Oranges, Blues, Greens) | Transparent scales were prototyped but looked unclear at low event counts. Named scales are less elegant on dark backgrounds but more readable. Reverted based on visual review. |
| **Bot aggression insight** | Flag as a data issue | Flag as a P0 product issue | Only 3 PvP kills across 796 matches is statistically consistent — bot kill tracking is working fine. The near-zero PvP rate is a design signal, not a data collection failure. |
| **Single file vs modules** | Split into tabs/map_view.py etc. | Single app.py (2,200 lines) | For a prototype assessed by one team, a single file is easier to deploy, review, and share. Modularisation deferred to v2 if the tool is productionised. |
