# LILA BLACK — Player Journey Visualization Tool

A browser-based analytics tool for Level Designers to explore player behaviour across 3 maps using 5 days of production gameplay data from LILA BLACK.

Built with Streamlit + Plotly. Deployed on Streamlit Community Cloud.

---

## Live Demo

🚀 [Open the App](https://player-journey-tool-2slkely888zqtueappg6wba.streamlit.app/)

---

## What It Does

Four interactive tabs:

| Tab | Purpose |
|---|---|
| 🗺️ Map View | Overlay player paths and events on the minimap. Filter by map, date, match, player type, and event type. |
| 🔥 Heatmap | Density heatmap for Kill Zones, Death Zones, High Traffic, and Loot Zones. |
| ⏱️ Timeline | Replay a single match second-by-second. Scrub slider + jump buttons. Player Activity Gantt chart. |
| 📊 Stats | Aggregate charts with insight callouts: event distribution, engagement by day, human vs bot balance, top killers. |

---

## Setup

### Prerequisites
- Python 3.9+
- The raw `player_data/` folder (not committed — obtain separately)

### Install dependencies

```bash
pip install -r requirements.txt
```

### Preprocess data (run once)

```bash
python preprocess.py
```

This consolidates 1,243 raw parquet files into `data/all_events.parquet` (~2.8MB).

### Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Project Structure

```
player-journey-tool/
├── app.py                  # Main Streamlit application
├── preprocess.py           # One-time data consolidation script
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── ARCHITECTURE.md         # Technical architecture details
├── INSIGHTS.md             # Level design findings
├── ASSUMPTIONS.txt         # Technical decisions log
├── data/
│   └── all_events.parquet  # Preprocessed dataset (committed)
└── assets/
    └── minimaps/           # Map images (committed)
        ├── AmbroseValley_Minimap.png
        ├── GrandRift_Minimap.png
        └── Lockdown_Minimap.jpg
```

> `player_data/` is gitignored. Only `data/all_events.parquet` and `assets/minimaps/` are committed.

---

## Data

- **Source:** 1,243 parquet files across 5 day folders (Feb 10–14, 2026)
- **After preprocessing:** 89,104 rows × 15 columns
- **Maps:** AmbroseValley, GrandRift, Lockdown
- **Event types:** Position, BotPosition, Kill, Killed, BotKill, BotKilled, KilledByStorm, Loot
- **Feb 14** is a partial day — lower event counts are expected

---

## Dependencies

```
streamlit==1.40.2
pandas>=2.0.0
pyarrow>=14.0.0
plotly>=5.18.0
Pillow>=10.0.0
numpy>=1.24.0
```

---

## Deployment

Hosted on **Streamlit Community Cloud** (free tier). Auto-redeploys on every push to `main`.

```bash
git add .
git commit -m "your message"
git push
```

Streamlit Cloud picks up the push and redeploys in ~1–2 minutes.

---

## Documentation

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — Full technical reference: data pipeline, schema, coordinate transform, per-tab design decisions
- [`INSIGHTS.md`](INSIGHTS.md) — Level design findings and recommendations derived from the data
- [`ASSUMPTIONS.txt`](ASSUMPTIONS.txt) — Log of every technical decision made during development

---

## Built With

- [Streamlit](https://streamlit.io) — UI framework
- [Plotly](https://plotly.com/python/) — Interactive charts and maps
- [Pandas](https://pandas.pydata.org) — Data manipulation
- [NumPy](https://numpy.org) — Heatmap histogram computation

NOTE:- The Screenshots are in the Screenshot folder. THe legends in the Map are clickable, Selecting/Deselecting which will make the event appear/disappear from the map.