# LILA BLACK — Player Journey Visualization Tool
## Architecture Document

---

## Overview

A browser-based Streamlit application for Level Designers at Lila Games to explore 5 days of production gameplay data across 3 maps. The tool provides four views: spatial event mapping, density heatmaps, match replay timeline, and aggregate statistics.

---

## Repository Structure

```
player-journey-tool/
├── app.py                  # Main Streamlit application (single file)
├── preprocess.py           # One-time data consolidation script
├── requirements.txt        # Python dependencies
├── ARCHITECTURE.md         # This document
├── INSIGHTS.md             # Level design findings
├── ASSUMPTIONS.txt         # Technical decisions log
├── data/
│   └── all_events.parquet  # Preprocessed dataset (2.8MB, committed to repo)
├── assets/
│   └── minimaps/           # Map images (committed to repo for deployment)
│       ├── AmbroseValley_Minimap.png
│       ├── GrandRift_Minimap.png
│       └── Lockdown_Minimap.jpg
└── player_data/            # Raw source files (gitignored — not needed after preprocessing)
    ├── February_10/        # ~250 parquet files per day
    ├── February_11/
    ├── February_12/
    ├── February_13/
    ├── February_14/        # Partial day
    └── minimaps/           # Original minimap source (gitignored)
```

---

## Data Pipeline

### Step 1 — Raw Data
1,243 individual parquet files, one per player per match, across 5 day folders.

### Step 2 — Preprocessing (`preprocess.py`)
Run once before first launch:
```bash
python preprocess.py
```

What it does:
- Iterates all day folders
- Parses filenames to extract `user_id`, `match_id`, and `is_bot`
  - Human: `{uuid}_{uuid}.nakama-0` → user = UUID 1, match = UUID 2
  - Bot: `{number}_{uuid}.nakama-0` → user = numeric ID, match = UUID
- Decodes event bytes to strings
- Transforms world coordinates (x, z) → pixel coordinates (pixel_x, pixel_y)
- Tags each row with date, partial day flag, map ID
- Concatenates all frames into a single DataFrame
- Saves to `data/all_events.parquet`

### Step 3 — Application (`app.py`)
Loads the consolidated parquet at startup via `@st.cache_data`, serves all four tabs.

```
Raw parquet (1,243 files)
        ↓ preprocess.py
data/all_events.parquet (89,104 rows, 15 columns)
        ↓ load_data() [@st.cache_data]
In-memory DataFrame
        ↓
4 tabs: Map View · Heatmap · Timeline · Stats
```

---

## Dataset Schema

| Column | Type | Description |
|---|---|---|
| `user_id` | object | Raw user identifier from parquet |
| `match_id` | object | Raw match identifier |
| `map_id` | object | AmbroseValley / GrandRift / Lockdown |
| `x` | float32 | World X coordinate |
| `y` | float32 | World Y coordinate (vertical) |
| `z` | float32 | World Z coordinate |
| `ts` | float64 | Match-relative elapsed time in seconds |
| `event` | object | Event type string |
| `user_id_from_file` | object | Cleaned user ID from filename |
| `match_id_clean` | object | Match ID with `.nakama-0` stripped |
| `is_bot` | bool | True if bot player |
| `date` | datetime64 | Calendar date |
| `date_str` | object | Formatted date e.g. "Feb 10" |
| `is_partial_day` | bool | True for Feb 14 (incomplete data) |
| `pixel_x` | float32 | Mapped X pixel coordinate [0–1024] |
| `pixel_y` | float32 | Mapped Y pixel coordinate [0–1024] |

### Event Types
| Event | Category | Description |
|---|---|---|
| Position | Movement | Human player GPS ping |
| BotPosition | Movement | Bot GPS ping |
| Kill | Combat | Human kills human |
| Killed | Combat | Human killed by human |
| BotKill | Combat | Human kills bot |
| BotKilled | Combat | Human killed by bot |
| KilledByStorm | Combat | Player eliminated by storm |
| Loot | Interaction | Player picks up loot |

### Coordinate Transform
```python
u = (x - origin_x) / scale
v = (z - origin_z) / scale
pixel_x = u * 1024
pixel_y = (1 - v) * 1024   # Y axis flipped
```

Map-specific parameters:
| Map | Scale | Origin X | Origin Z |
|---|---|---|---|
| AmbroseValley | 900 | -370 | -473 |
| GrandRift | 581 | -290 | -290 |
| Lockdown | 1000 | -500 | -500 |

---

## Application Architecture (`app.py`)

### Module-Level Constants
```
EVENT_COLORS     — colour per event type
EVENT_SYMBOLS    — Plotly marker shape per event
EVENT_SIZES      — marker size per event
ALL_EVENTS       — full event list
MOVE_EVENTS      — [Position, BotPosition]
COMBAT_EVENTS    — all non-movement events
OVERLAY_INFO     — heatmap overlay descriptions
HEATMAP_EVTS     — heatmap overlay → event list + colorscale
HEATMAP_BINS     — adaptive bin count per map
HEATMAP_EVT_LABELS — reliability bar labels
MAP_CONFIG       — minimap filenames per map
```

### Key Functions

| Function | Purpose |
|---|---|
| `load_data()` | Load parquet, convert ts to numeric, sort by ts. Cached. |
| `get_dates_list()` | Sorted unique date_str values. Cached. |
| `get_map_matches()` | Match IDs filtered by map + dates. Cached. |
| `get_match_summaries()` | Match labels with date + player counts. Cached. |
| `get_minimap_b64()` | Base64-encode minimap PNG. Cached. |
| `run_map_query()` | Filter df by map/dates/match/player type/events. |
| `run_match_query()` | Filter df to single match. |
| `build_map_fig()` | Build Plotly scatter map with paths and event markers. |
| `build_heatmap_fig()` | Build Plotly heatmap with minimap underlay. |
| `hm_data_hash()` | Hash function for heatmap stale detection. |
| `match_label()` | Format match UUID as short readable label. |

### Tab Render Functions

| Function | Tab |
|---|---|
| `render_map_view(df)` | Tab 1 — spatial event overlay on minimap |
| `render_heatmap(df)` | Tab 2 — density heatmap by overlay type |
| `render_timeline(df)` | Tab 3 — per-match scrub replay |
| `render_stats(df)` | Tab 4 — aggregate statistics and charts |

### Session State Pattern
All tabs use the same pattern:
1. Render filter widgets
2. Compute a filter hash for stale detection
3. Show stale banner if hash changed since last load
4. On button click: query data → store in session state → `st.rerun()`
5. On rerun: read from session state → render charts

This pattern ensures:
- No double-click needed (rerun commits state before rendering)
- Stale detection works correctly
- Chart caches are deterministic

---

## Tab 1 — Map View

**Purpose:** Overlay player paths and events on the minimap. Filter by map, date, match, player type, and event type.

**Key design decisions:**
- Paths batched into 2 `Scattergl` traces (human + bot) using `None` separators — avoids one trace per player
- Figure cached in session state by `mv_fig_hash` — only rebuilds when filters change
- Map View uses low path opacity (0.3/0.2) and thin lines (width=1) to show density patterns across many matches
- Sticky Show Map button fixed to viewport bottom

---

## Tab 2 — Heatmap

**Purpose:** Show event density as a 2D histogram overlaid on the minimap. Four overlay types: Kill Zones, Death Zones, High Traffic, Loot Zones.

**Key design decisions:**
- `np.histogram2d` with adaptive bin counts per map (AmbroseValley=48, GrandRift=40, Lockdown=32)
- Minimap rendered at 50% opacity so heatmap shows through
- Figure cached by `str((hm_filters_hash, htype))` — overlay type change rebuilds figure without re-querying data
- `hm_data_hash()` excludes overlay type from stale detection — changing overlay triggers figure rebuild but no stale banner
- Named colorscales: Reds / Oranges / Blues / Greens

---

## Tab 3 — Timeline

**Purpose:** Replay a single match second-by-second. Slider controls playback position. Player Activity Gantt chart shows combat events per player over time. Event Density histogram shows activity distribution.

**Key design decisions:**
- `ts` is stored as float seconds in parquet (game-elapsed time, not wall clock). `pd.to_numeric()` used to avoid the parquet schema tagging it as `datetime64[ms]` which would misinterpret 480.0s as 480ms.
- Per-player timestamp normalization: `elapsed_s = ts - ts.min()` per `user_id_from_file` — handles late-joiners whose `ts=0` doesn't align with match start
- `gantt_base` and `hfig_base` pre-built at Load Match time — each slider move only does `copy.deepcopy(base)` + `add_vline(playback_s)`
- Player labels: `👤 P1/P2…`, `🤖 B1/B2…` assigned after `sorted()` of UUIDs — ensures consistent ordering with Gantt Y-axis
- Jump buttons (+1s, +5s, +10s, +30s, +60s, -10s, -30s, reset) use `on_click` callbacks to write to session state before rerun
- Back buttons disabled when `cur_pos <= 0.0`, forward buttons disabled when `cur_pos >= total_s`
- Timeline uses bold paths (width=2.5, opacity=0.85/0.65) for single-match legibility vs Map View thin/transparent for density
- 1 cross-midnight match spans Feb 10 and Feb 11 — appears once in combined selection (337 = 200 + 138 - 1, correct)

---

## Tab 4 — Stats

**Purpose:** Aggregate statistics across filtered data. Four charts with question-based section headers and insight callouts. Quick Read summary at top.

**Key design decisions:**
- "Game Events" metric excludes Position/BotPosition movement pings
- Chart 1 (Event Distribution) also excludes movement events — they would dwarf all game events
- All 4 charts cached together as `st_charts` tuple
- `st_insight` dict computed once and cached — never recomputed on rerun
- Top 10 Killers: readable "Player N" labels + UUID in hover tooltip + lookup table expander
- Feb 14 annotated as partial day on Events per Day chart
- `event_verb` dict provides natural language phrasing in Quick Read callout

---

## Deployment

**Platform:** Streamlit Community Cloud (free tier)

**Repository:** GitHub — auto-redeploys on every `git push` to main branch

**Requirements:**
```
streamlit==1.40.2
pandas>=2.0.0
pyarrow>=14.0.0
plotly>=5.18.0
Pillow>=10.0.0
numpy>=1.24.0
```

**Notes:**
- `data/all_events.parquet` committed to repo (2.8MB — within GitHub limits)
- Minimap images in `assets/minimaps/` committed to repo (not in `.gitignore`)
- `player_data/` in `.gitignore` — raw 1,243 parquet files not needed after preprocessing
- Streamlit pinned to `1.40.2` to avoid JS module fetch errors from version mismatches
- `>=` version pins for all other packages — avoids wheel compilation failures on Python 3.12
