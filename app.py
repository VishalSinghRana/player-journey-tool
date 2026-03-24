"""
app.py — LILA BLACK Player Journey Visualization Tool
Each tab fully independent. All UX issues addressed.
"""

import os, io, base64
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LILA BLACK — Level Intelligence",
    page_icon="🎯", layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=Share+Tech+Mono&family=Inter:wght@300;400;500&display=swap');

html,body,[class*="css"]{font-family:'Inter',sans-serif;background:#0a0c10;color:#c9d1d9;}
.stApp{background:#0a0c10;}
h1,h2,h3{font-family:'Rajdhani',sans-serif;}

/* Tabs */
.stTabs [data-baseweb="tab"]{font-family:'Rajdhani',sans-serif;font-size:1rem;font-weight:600;color:#8b949e;}
.stTabs [aria-selected="true"]{color:#58a6ff!important;}
.stTabs [data-baseweb="tab-border"]{background:#58a6ff!important;}

/* Metrics */
div[data-testid="stMetric"]{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:12px 16px;}
div[data-testid="stMetric"] label{color:#8b949e!important;font-size:0.75rem;text-transform:none!important;letter-spacing:0!important;}
div[data-testid="stMetric"] div[data-testid="stMetricValue"]{font-family:'Share Tech Mono',monospace;color:#58a6ff;}

/* FIX 8: Remove ALL CAPS from form labels — restore normal case and readable size */
.stSelectbox label,.stMultiSelect label,.stSlider label,.stRadio label,.stCheckbox label{
  font-size:0.82rem!important;
  text-transform:none!important;
  letter-spacing:0!important;
  color:#8b949e!important;
  font-weight:500!important;
}

/* FIX 9: Filter group headers */
.filter-group-label{
  font-size:0.68rem;
  text-transform:uppercase;
  letter-spacing:0.1em;
  color:#444d56;
  margin-bottom:4px;
  font-family:'Share Tech Mono',monospace;
}

/* Stale banner */
.stale-banner{
  background:#21262d;
  border-left:3px solid #f0a500;
  border-radius:4px;
  padding:10px 16px;
  font-family:'Share Tech Mono',monospace;
  font-size:0.78rem;
  color:#f0a500;
  margin-bottom:10px;
}

/* FIX 5: Stale overlay on map — shown as a semi-transparent overlay hint */
.stale-map-hint{
  background:#21262d99;
  border:1px solid #f0a500;
  border-radius:6px;
  padding:8px 14px;
  font-family:'Share Tech Mono',monospace;
  font-size:0.75rem;
  color:#f0a500;
  text-align:center;
  margin-bottom:6px;
}

/* Event pills in legend */
.event-pill{
  display:inline-block;
  padding:3px 12px;
  border-radius:12px;
  font-size:0.75rem;
  font-family:'Share Tech Mono',monospace;
  margin:3px;
}

/* FIX 9: filter section group box */
.filter-group{
  background:#0d1117;
  border:1px solid #21262d;
  border-radius:8px;
  padding:14px 16px 10px;
  margin-bottom:10px;
}

/* Info/hint bar */
.info-bar{
  font-family:'Share Tech Mono',monospace;
  font-size:0.72rem;
  color:#8b949e;
  background:#161b22;
  border:1px solid #21262d;
  border-radius:6px;
  padding:8px 14px;
  margin-bottom:8px;
}

/* FIX 17: Empty state */
.empty-state{
  text-align:center;
  padding:60px 20px;
  color:#444d56;
}
.empty-state .title{
  font-family:'Rajdhani',sans-serif;
  font-size:1.4rem;
  color:#6e7681;
  margin-bottom:8px;
}
.empty-state .hint{
  font-size:0.85rem;
  color:#444d56;
  margin-bottom:4px;
}

/* FIX 16: softer divider */
.section-divider{
  border:none;
  border-top:1px solid #161b22;
  margin:16px 0;
}

hr{border-color:#21262d;}

/* Sticky Show Map bar — fixed to bottom of viewport */
.sticky-bar{
  position:fixed;bottom:0;left:0;right:0;z-index:9999;
  background:linear-gradient(to top,#0a0c10 70%,transparent);
  padding:12px 32px 16px;display:flex;align-items:center;gap:16px;
  border-top:1px solid #21262d;
}
/* Push page content up so sticky bar never covers legend */
.main .block-container{padding-bottom:90px!important;}
/* Clear all — small muted text, opposite side from Show Map */
div[data-testid="stButton"] button[kind="secondary"]{
  background:transparent!important;color:#444d56!important;
  border:1px solid #21262d!important;font-size:0.78rem!important;
}
div[data-testid="stButton"] button[kind="secondary"]:hover{
  color:#ff6b6b!important;border-color:#ff6b6b!important;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
DATA_PATH   = "data/all_events.parquet"
MINIMAP_DIR = os.path.join("assets", "minimaps")

MAP_CONFIG = {
    "AmbroseValley": {"img": "AmbroseValley_Minimap.png"},
    "GrandRift":     {"img": "GrandRift_Minimap.png"},
    "Lockdown":      {"img": "Lockdown_Minimap.jpg"},
}
MAPS = list(MAP_CONFIG.keys())

EVENT_COLORS = {
    "Kill":"#ff4444","Killed":"#ff8800",
    "BotKill":"#ff6666","BotKilled":"#ffaa44",
    "KilledByStorm":"#aa44ff","Loot":"#44ff88",
    "Position":"#58a6ff","BotPosition":"#8b949e",
}
EVENT_SYMBOLS = {
    "Kill":"star","Killed":"x",
    "BotKill":"triangle-up","BotKilled":"triangle-down",
    "KilledByStorm":"diamond","Loot":"circle",
    "Position":"circle","BotPosition":"circle",
}
EVENT_SIZES = {
    "Kill":14,"Killed":14,"BotKill":12,"BotKilled":12,
    "KilledByStorm":16,"Loot":10,"Position":4,"BotPosition":3,
}
ALL_EVENTS    = list(EVENT_COLORS.keys())
MOVE_EVENTS   = ["Position","BotPosition"]
COMBAT_EVENTS = [e for e in ALL_EVENTS if e not in MOVE_EVENTS]

# Heatmap overlay descriptions — module-level constant, never recreated on rerun
OVERLAY_INFO = {
    "Kill Zones":   ("🔴", "Where kills happened",         "Kill (PvP) + BotKill (player kills bot)"),
    "Death Zones":  ("🟠", "Where players died",           "Killed (PvP) + BotKilled (by bot) + KilledByStorm"),
    "High Traffic": ("🔵", "Where players spent time",     "Position + BotPosition movement pings"),
    "Loot Zones":   ("🟢", "Where loot was picked up",     "Loot pickup events only"),
}

# Map-specific heatmap bin resolution — larger map = more bins = finer detail
HEATMAP_BINS = {
    "AmbroseValley": 48,
    "GrandRift":     40,
    "Lockdown":      32,
}

# Heatmap overlay → events + colorscale (module level — never recreated on rerun)
HEATMAP_EVTS = {
    "Kill Zones":   (["Kill","BotKill"],                     "Reds"),
    "Death Zones":  (["Killed","BotKilled","KilledByStorm"], "Oranges"),
    "High Traffic": (["Position","BotPosition"],             "Blues"),
    "Loot Zones":   (["Loot"],                               "Greens"),
}

# Event label per overlay for reliability bar (module level)
HEATMAP_EVT_LABELS = {
    "Kill Zones":"kills", "Death Zones":"deaths",
    "High Traffic":"movement pings", "Loot Zones":"loot pickups",
}

def hm_data_hash(hm_map, hm_dates, hm_match_sel):
    """Stale hash for heatmap — data filters only, NOT overlay type."""
    return str((hm_map, tuple(hm_dates) if hm_dates else (), hm_match_sel))

# FIX 10: human-readable match label helper
def match_label(match_id):
    """Show enough of the UUID to be distinguishable, not just a fragment."""
    if match_id == "All Matches":
        return "All Matches"
    return f"{match_id[:8]}…{match_id[-4:]}"

# ── Session state ─────────────────────────────────────────────────────────────
def init_state():
    for k,v in {
        "mv_show":False, "mv_result":None,
        "mv_map_used":None, "mv_paths_used":True, "mv_markers_used":True,
        "mv_filters_hash":None, "mv_event_filter":None, "mv_building":False, "mv_fig":None, "mv_fig_hash":None,
        "hm_show":False, "hm_result":None,
        "hm_map_used":None, "hm_type_used":"Kill Zones",
        "hm_dates_used":None, "hm_match_used":"All Matches",
        "hm_filters_hash":None, "hm_fig":None, "hm_fig_hash":None, "hm_evt_count":0,
        "tl_show":False, "tl_data":None,
        "tl_map_used":None, "tl_match_used":None, "tl_total_s":1.0,
        "tl_combat":None, "tl_gantt_traces":None, "tl_n_rows":0,
        "tl_id_map":{}, "tl_gantt_base":None, "tl_hfig_base":None,
        "tl_filters_hash":None, "tl_dates":None,
        "tl_players_used":None, "tl_n_h":0, "tl_n_b":0,
        "st_show":False, "st_data":None,"st_filters_hash":None, "st_charts":None, "st_charts_hash":None,"st_map_used":"All Maps", "st_dates_used":None, "st_dates_label":"All dates", "st_insight":None,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── Data loaders ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading battle data...")
def load_data():
    if not os.path.exists(DATA_PATH):
        st.error("Run `python preprocess.py` first.")
        st.stop()
    df = pd.read_parquet(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    df["date_str"] = df["date"].dt.strftime("%b %d")
    df["is_bot"] = df["is_bot"].astype(bool)
    # ts is stored as seconds (float) in parquet — keep as numeric
    # DO NOT convert to datetime: the parquet schema tags it as datetime64[ms]
    # which would make pandas interpret 480.0 seconds as 480 milliseconds
    # We treat ts as raw seconds elapsed within the match
    df["ts"] = pd.to_numeric(df["ts"], errors="coerce")
    df = df.sort_values("ts").reset_index(drop=True)
    return df

@st.cache_data(show_spinner=False)
def get_minimap_b64(map_id):
    cfg  = MAP_CONFIG.get(map_id, {})
    path = os.path.join(MINIMAP_DIR, cfg.get("img",""))
    if not os.path.exists(path):
        return None
    img = Image.open(path).convert("RGBA").resize((1024,1024))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

@st.cache_data(show_spinner=False)
def get_dates_list(_df):
    return sorted(_df["date_str"].unique())

@st.cache_data(show_spinner=False)
def get_map_matches(_df, map_id, dates_tuple=None):
    sub = _df[_df["map_id"] == map_id]
    if dates_tuple:
        sub = sub[sub["date_str"].isin(dates_tuple)]
    return sorted(sub["match_id_clean"].unique())

# FIX 10: match summary with player + event count for the dropdown label
@st.cache_data(show_spinner=False)
def get_match_summaries(_df, map_id, dates_tuple=None):
    """Returns dict of match_id -> display label with player count."""
    sub = _df[_df["map_id"] == map_id]
    if dates_tuple:
        sub = sub[sub["date_str"].isin(dates_tuple)]
    summaries = {}
    for mid, grp in sub.groupby("match_id_clean"):
        n_humans = grp[~grp["is_bot"]]["user_id_from_file"].nunique()
        n_bots   = grp[grp["is_bot"]]["user_id_from_file"].nunique()
        # Show all dates this match spans — handles cross-midnight matches
        dates    = " & ".join(sorted(grp["date_str"].unique()))
        summaries[mid] = f"{mid[:8]}… | {dates} | {n_humans}P {n_bots}B"
    return summaries

# ── Query ─────────────────────────────────────────────────────────────────────
def run_map_query(df, map_id, dates, match_id, humans, bots, event_filter, show_paths):
    """
    Returns (combined_df, marker_df, path_df).
    - path_df    : Position/BotPosition rows matching player-type filter
    - marker_df  : combat+loot rows matching player-type AND event filter
    - combined_df: path_df (if show_paths) + marker_df — what the map renders
    """
    empty = pd.DataFrame()
    if not humans and not bots:
        return empty, empty, empty

    mask = df["map_id"] == map_id
    if dates:
        mask &= df["date_str"].isin(dates)
    if match_id:
        mask &= df["match_id_clean"] == match_id
    if humans and not bots:
        mask &= df["is_bot"] == False
    elif bots and not humans:
        mask &= df["is_bot"] == True

    base = df[mask]

    is_move   = base["event"].isin(MOVE_EVENTS)
    path_df   = base[is_move].copy()
    marker_df = base[~is_move].copy()

    if event_filter:
        marker_df = marker_df[marker_df["event"].isin(event_filter)]

    if show_paths and not path_df.empty:
        combined = pd.concat([path_df, marker_df], ignore_index=True)
    else:
        combined = marker_df.copy()

    return combined, marker_df, path_df


def run_match_query(df, match_id):
    return df[df["match_id_clean"] == match_id].copy()

# ── Figure builders ───────────────────────────────────────────────────────────
def _map_layout(fig):
    fig.update_layout(
        xaxis=dict(range=[0,1024],showgrid=False,zeroline=False,showticklabels=False),
        yaxis=dict(range=[1024,0],showgrid=False,zeroline=False,showticklabels=False),
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        # Plotly legend — top-right inside the map, dark styled
        showlegend=True,
        legend=dict(
            bgcolor="rgba(13,17,23,0.85)",
            bordercolor="#21262d",
            borderwidth=1,
            font=dict(color="#c9d1d9", size=11),
            x=0.99, y=0.80,          # lowered from 1.0 to clear zoom/pan toolbar
            xanchor="right", yanchor="top",
        ),
        margin=dict(l=0,r=0,t=0,b=0), height=680, dragmode="pan",
    )

def build_map_fig(df_in, map_id, show_paths=True, show_events=True,
                  active_events=None, path_width=1, path_opacity_human=0.3,
                  path_opacity_bot=0.2):
    """
    path_width: line width for player paths. Default 1 (Map View). Use 2+ for Timeline.
    path_opacity_human/bot: opacity for path lines. Lower = more transparent.
    """
    fig = go.Figure()

    b64 = get_minimap_b64(map_id)
    if b64:
        fig.add_layout_image(
            source=f"data:image/png;base64,{b64}",
            xref="x", yref="y", x=0, y=0,
            sizex=1024, sizey=1024,
            sizing="stretch", opacity=1.0, layer="below",
        )

    if df_in is None or df_in.empty:
        _map_layout(fig)
        return fig

    if show_paths:
        pos = df_in[df_in["event"].isin(MOVE_EVENTS)]
        if not pos.empty:
            for is_bot_flag, label, base_color, opacity in [
                (False, "Human Paths", "88,166,255", path_opacity_human),
                (True,  "Bot Paths",   "139,148,158", path_opacity_bot),
            ]:
                subset = pos[pos["is_bot"] == is_bot_flag]
                if subset.empty:
                    continue
                color = f"rgba({base_color},{opacity})"
                xs, ys = [], []
                for _, grp in subset.groupby(
                    ["user_id_from_file","match_id_clean"], sort=False
                ):
                    xs.extend(grp["pixel_x"].tolist() + [None])
                    ys.extend(grp["pixel_y"].tolist() + [None])
                fig.add_trace(go.Scattergl(
                    x=xs, y=ys, mode="lines", name=label,
                    line=dict(color=color, width=path_width),
                    hoverinfo="skip", showlegend=True,
                ))

    if show_events:
        combat = df_in[~df_in["event"].isin(MOVE_EVENTS)]
        if not combat.empty:
            for evt, grp in combat.groupby("event", sort=False):
                fig.add_trace(go.Scattergl(
                    x=grp["pixel_x"], y=grp["pixel_y"],
                    mode="markers", name=evt,
                    marker=dict(
                        color=EVENT_COLORS.get(evt,"#fff"),
                        symbol=EVENT_SYMBOLS.get(evt,"circle"),
                        size=EVENT_SIZES.get(evt,8),
                        line=dict(color="#0a0c10",width=1),
                    ),
                    hovertemplate=(
                        f"<b>{evt}</b><br>"
                        "Player: %{customdata[0]}<br>"
                        "Match: %{customdata[1]}<extra></extra>"
                    ),
                    customdata=grp[["user_id_from_file","match_id_clean"]].values,
                    showlegend=True,
                ))

    _map_layout(fig)
    return fig


def build_heatmap_fig(df_in, htype, map_id):
    """
    Returns (fig, event_count) — event_count lets the UI show
    how many events contributed so the designer can judge reliability.
    """
    fig = go.Figure()
    b64 = get_minimap_b64(map_id)
    if b64:
        fig.add_layout_image(
            source=f"data:image/png;base64,{b64}",
            xref="x",yref="y",x=0,y=0,sizex=1024,sizey=1024,
            sizing="stretch",opacity=0.5,layer="below",
        )

    evts, cs = HEATMAP_EVTS.get(htype, ([], "Blues"))
    heat = df_in[df_in["event"].isin(evts)]
    event_count = len(heat)

    if not heat.empty:
        hx = np.clip(heat["pixel_x"].values, 0, 1023)
        hy = np.clip(heat["pixel_y"].values, 0, 1023)
        # FIX 5: adaptive bin count per map — finer for larger maps
        bins = HEATMAP_BINS.get(map_id, 36)
        H, xe, ye = np.histogram2d(hx, hy, bins=bins,
                                   range=[[0,1024],[0,1024]])
        fig.add_trace(go.Heatmap(
            x=(xe[:-1]+xe[1:])/2, y=(ye[:-1]+ye[1:])/2, z=H.T,
            colorscale=cs, opacity=0.7, showscale=True,
            # FIX 7: colorbar title so user knows what the scale means
            colorbar=dict(
                title=dict(text="Event Count", font=dict(color="#8b949e",size=11)),
                tickfont=dict(color="#c9d1d9"),
                bgcolor="#161b22", bordercolor="#21262d",
            ),
            hovertemplate="Event count: %{z}<extra></extra>",
        ))

    # FIX 2: heatmap-specific layout — no legend (colorbar handles it)
    fig.update_layout(
        xaxis=dict(range=[0,1024],showgrid=False,zeroline=False,showticklabels=False),
        yaxis=dict(range=[1024,0],showgrid=False,zeroline=False,showticklabels=False),
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        showlegend=False,   # heatmap uses colorbar, not legend
        margin=dict(l=0,r=0,t=0,b=0), height=680, dragmode="pan",
    )
    return fig, event_count

# ── Header ────────────────────────────────────────────────────────────────────
def render_header():
    st.markdown("""
    <div style="padding:14px 0 10px;border-bottom:1px solid #21262d;margin-bottom:18px;">
      <span style="font-family:'Rajdhani',sans-serif;font-size:1.9rem;font-weight:700;
                   color:#e6edf3;letter-spacing:0.08em;">🎯 LILA BLACK</span>
      <span style="font-family:'Share Tech Mono',monospace;font-size:0.68rem;
                   color:#58a6ff;letter-spacing:0.18em;margin-left:14px;">
        LEVEL INTELLIGENCE DASHBOARD
      </span>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — MAP VIEW
# ─────────────────────────────────────────────────────────────────────────────
def render_map_view(df):
    dates_list = get_dates_list(df)

    # ── CLEAR ALL ────────────────────────────────────────────────────────────
    if st.session_state.get("_mv_do_reset", False):
        # Map radio — None means nothing selected
        st.session_state["mv_map_radio"]    = None
        # Date checkboxes — all True = all dates
        for _d in get_dates_list(df):
            st.session_state[f"mv_date_{_d}"] = True
        st.session_state["mv_date_all"]     = True
        # Match
        st.session_state["mv_match_sel"]    = "All Matches"
        # Event checkboxes — all True = all events
        for _e in COMBAT_EVENTS:
            st.session_state[f"mv_evt_{_e}"] = True
        st.session_state["mv_evt_all"]      = True
        # Player type + display
        st.session_state["mv_humans_cb"]    = True
        st.session_state["mv_bots_cb"]      = True
        st.session_state["mv_paths_cb"]     = True
        st.session_state["mv_markers_cb"]   = True
        st.session_state["mv_show"]         = False
        st.session_state["mv_result"]       = None
        st.session_state["mv_filters_hash"] = None
        st.session_state["mv_fig"]          = None
        st.session_state["mv_fig_hash"]     = None
        st.session_state["_mv_do_reset"]    = False
        st.rerun()

    # ── FIX 15: consistent emoji + clear section header ───────────────────────
    st.markdown("""
    <div style="margin-bottom:14px;">
      <span style="font-family:'Rajdhani',sans-serif;font-size:1.15rem;font-weight:700;
                   color:#e6edf3;letter-spacing:0.06em;">🗺️ Map View</span>
      <span style="font-family:'Share Tech Mono',monospace;font-size:0.68rem;
                   color:#444d56;margin-left:10px;">Set filters · Show Map button stays at bottom of screen</span>
    </div>
    """, unsafe_allow_html=True)

    # ── GROUP 1 — Map (radio cards) ──────────────────────────────────────────
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Map (required)</div>', unsafe_allow_html=True)

    # Radio buttons styled as horizontal cards — one click, no dropdown
    mv_map = st.radio(
        "Map", MAPS,
        index=None,           # nothing pre-selected
        horizontal=True,
        key="mv_map_radio",
        label_visibility="collapsed",
    )
    if not mv_map:
        st.caption("← Select a map to begin")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── GROUP 2 — Date checkboxes ──────────────────────────────────────────────
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Date(s) — uncheck to exclude</div>',
                unsafe_allow_html=True)

    # Initialise date keys via setdefault — only on first load, never conflicts
    # with widget because we do NOT pass value= to the checkboxes below.
    st.session_state.setdefault("mv_date_all", True)
    for _d in dates_list:
        st.session_state.setdefault(f"mv_date_{_d}", True)

    def _on_date_all_change():
        """Propagate All toggle to every individual date checkbox."""
        new_val = st.session_state["mv_date_all"]
        for _d in dates_list:
            st.session_state[f"mv_date_{_d}"] = new_val

    def _on_date_individual_change():
        """If all individual dates checked → auto-check All."""
        all_on = all(st.session_state.get(f"mv_date_{_d}", True) for _d in dates_list)
        st.session_state["mv_date_all"] = all_on

    da_cols = st.columns([1] + [1]*len(dates_list))
    with da_cols[0]:
        all_dates_checked = st.checkbox(
            "All", key="mv_date_all",
            on_change=_on_date_all_change,
        )

    date_checks = {}
    for i, d in enumerate(dates_list):
        with da_cols[i+1]:
            date_checks[d] = st.checkbox(
                d, key=f"mv_date_{d}",
                disabled=all_dates_checked,
                on_change=_on_date_individual_change,
            )

    if all_dates_checked:
        mv_dates = None   # no filter = all dates
    else:
        selected_dates = [d for d,v in date_checks.items() if v]
        mv_dates = selected_dates if selected_dates else None

    st.markdown('</div>', unsafe_allow_html=True)

    # ── GROUP 3 — Match (keep as selectbox — too many options) ────────────────
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Match (optional)</div>',
                unsafe_allow_html=True)

    dates_tuple     = tuple(mv_dates) if mv_dates else None
    match_summaries = get_match_summaries(df, mv_map, dates_tuple) if mv_map else {}
    match_ids       = list(match_summaries.keys())
    match_opts      = ["All Matches"] + match_ids
    saved           = st.session_state.get("mv_match_sel", "All Matches")
    safe_idx        = match_opts.index(saved) if saved in match_opts else 0
    if not mv_map:
        st.caption("Select a map first to see available matches.")
        mv_match_sel = "All Matches"
        mv_match     = None
    else:
        mv_match_sel = st.selectbox(
            "Match", match_opts, index=safe_idx,
            format_func=lambda x: "All Matches" if x == "All Matches"
                                  else match_summaries.get(x, match_label(x)),
            key="mv_match_sel",
            help="Each entry shows: Match ID | Date | Players (P) | Bots (B)",
            label_visibility="collapsed",
        )
        mv_match = None if mv_match_sel == "All Matches" else mv_match_sel

    st.markdown('</div>', unsafe_allow_html=True)

    # ── GROUP 4 — Player type ─────────────────────────────────────────────────
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Player Type</div>', unsafe_allow_html=True)

    pt_cols = st.columns(2)
    with pt_cols[0]:
        mv_humans = st.checkbox("Show Humans", value=True, key="mv_humans_cb")
    with pt_cols[1]:
        mv_bots   = st.checkbox("Show Bots",   value=True, key="mv_bots_cb")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── GROUP 5 — Event type checkboxes ──────────────────────────────────────
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Event Types</div>',
                unsafe_allow_html=True)

    # Initialise event keys via setdefault — same pattern as dates
    st.session_state.setdefault("mv_evt_all", True)
    for _e in COMBAT_EVENTS:
        st.session_state.setdefault(f"mv_evt_{_e}", True)

    def _on_evt_all_change():
        """When All is toggled, set every individual event key to match it."""
        new_val = st.session_state["mv_evt_all"]
        for _e in COMBAT_EVENTS:
            st.session_state[f"mv_evt_{_e}"] = new_val

    def _on_evt_individual_change():
        """When any individual event is changed, update All to reflect reality.
        All = True only if every individual event is checked."""
        all_on = all(st.session_state.get(f"mv_evt_{_e}", True) for _e in COMBAT_EVENTS)
        st.session_state["mv_evt_all"] = all_on

    evt_master_col = st.columns([1] + [1]*len(COMBAT_EVENTS))
    with evt_master_col[0]:
        all_evts_checked = st.checkbox(
            "All", key="mv_evt_all",
            on_change=_on_evt_all_change,
        )

    evt_checks = {}
    for i, e in enumerate(COMBAT_EVENTS):
        with evt_master_col[i+1]:
            evt_checks[e] = st.checkbox(
                e,
                key=f"mv_evt_{e}",
                disabled=all_evts_checked,
                on_change=_on_evt_individual_change,
            )

    if all_evts_checked:
        mv_event_filter = None   # no filter = show all
    else:
        selected_evts = [e for e,v in evt_checks.items() if v]
        mv_event_filter = selected_evts if selected_evts else None

    st.markdown('</div>', unsafe_allow_html=True)

    # ── GROUP 6 — Display options ─────────────────────────────────────────────
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Display Options</div>', unsafe_allow_html=True)

    disp_cols = st.columns(2)
    with disp_cols[0]:
        mv_paths   = st.checkbox("Show Player Paths",  value=True, key="mv_paths_cb")
    with disp_cols[1]:
        mv_markers = st.checkbox("Show Event Markers", value=True, key="mv_markers_cb")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Stale detection ───────────────────────────────────────────────────────
    current_hash = str((
        mv_map,
        tuple(sorted(mv_dates)) if mv_dates else (),
        mv_match_sel,
        tuple(sorted(mv_event_filter)) if mv_event_filter else (),
        mv_humans, mv_bots, mv_paths, mv_markers,
    ))
    is_stale = (
        st.session_state["mv_show"]
        and st.session_state.get("mv_filters_hash") is not None
        and st.session_state["mv_filters_hash"] != current_hash
    )

    # Stale banner — shown in the filter area so user sees it without scrolling
    if is_stale:
        st.markdown(
            '<div class="stale-banner">'
            '⚠️  Filters changed — click <b>Show Map</b> at the bottom of the screen.'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── STICKY BUTTONS — rendered inline, CSS positions them as fixed bar ─────
    # Show Map: primary action, full weight
    # Clear all: secondary, muted — far right to prevent accidental clicks
    sb1, _, sb2 = st.columns([2, 6, 1])
    with sb1:
        show_clicked = st.button(
            "▶  Show Map", key="mv_show_btn", type="primary",
            use_container_width=True,
        )
    with sb2:
        clear_clicked = st.button(
            "✕ Clear all", key="mv_clear_btn",
            use_container_width=True,
            help="Reset all filters and clear the map",
        )

    if clear_clicked:
        st.session_state["_mv_do_reset"] = True
        st.rerun()

    # ── Validation + query ────────────────────────────────────────────────────
    if show_clicked:
        if not mv_map:
            st.error("⬆️  Please select a Map before loading.")
            return
        if not mv_humans and not mv_bots:
            st.error("⬆️  Please check at least one of Show Humans or Show Bots.")
            return

        with st.spinner("⏳ Querying data…"):
            result = run_map_query(
                df, mv_map, mv_dates, mv_match,
                mv_humans, mv_bots, mv_event_filter, mv_paths,
            )

        combined_df, marker_df, path_df = result
        st.session_state["mv_result"]       = (marker_df, path_df)
        # Flag that map needs to render — message shown during build below
        st.session_state["mv_building"]     = True
        st.session_state["mv_map_used"]     = mv_map
        st.session_state["mv_paths_used"]   = mv_paths
        st.session_state["mv_markers_used"] = mv_markers
        st.session_state["mv_event_filter"] = mv_event_filter
        st.session_state["mv_show"]         = True
        st.session_state["mv_filters_hash"] = current_hash
        st.rerun()

    # FIX 16: soft divider instead of hard hr
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── RENDER ────────────────────────────────────────────────────────────────
    if not st.session_state["mv_show"]:
        # FIX 17: rich empty state with guidance
        st.markdown("""
        <div class="empty-state">
          <div style="font-size:3rem;margin-bottom:12px;">🗺️</div>
          <div class="title">No map loaded yet</div>
          <div class="hint">1. Select a <b>Map</b> from the dropdown above</div>
          <div class="hint">2. Optionally filter by Date or Match</div>
          <div class="hint">3. Click <b>▶ Show Map</b> to visualise player behaviour</div>
          <div style="margin-top:20px;font-size:0.75rem;color:#30363d;">
            Tip: Show Map button is always visible at the bottom of the screen
          </div>
        </div>
        """, unsafe_allow_html=True)
        return

    stored = st.session_state.get("mv_result")
    if stored is None:
        st.info("Click Show Map to load the visualisation.")
        return

    marker_df, path_df = stored
    show_paths_flag = st.session_state["mv_paths_used"]
    if show_paths_flag and not path_df.empty:
        combined_df = pd.concat([path_df, marker_df], ignore_index=True)
    else:
        combined_df = marker_df.copy()

    map_used      = st.session_state["mv_map_used"]
    active_filter = st.session_state.get("mv_event_filter")

    if combined_df.empty and marker_df.empty:
        st.warning("No data found for these filters. Try broadening your selection.")
        return

    # ── Active filter summary — tells user exactly what map shows ────────────
    map_label    = st.session_state.get("mv_map_used", "")
    dates_used   = mv_dates if mv_dates else ["All dates"]
    match_used   = mv_match_sel if mv_match_sel != "All Matches" else "All matches"
    players_used = ("Humans & Bots" if st.session_state.get("mv_paths_used") and
                    not marker_df.empty else
                    "Humans" if not path_df[path_df["is_bot"]==False].empty
                    and path_df[path_df["is_bot"]==True].empty
                    else "Bots" if path_df[path_df["is_bot"]==True].empty is False
                    else "Humans & Bots")
    evts_used    = (", ".join(active_filter) if active_filter else "All event types")

    st.markdown(
        f'<div style="background:#0d1117;border:1px solid #21262d;border-radius:8px;'
        f'padding:10px 16px;margin-bottom:14px;font-family:Share Tech Mono,monospace;'
        f'font-size:0.75rem;color:#8b949e;">'
        f'<span style="color:#e6edf3;font-weight:600;">Currently showing:</span>'
        f' &nbsp; 🗺️ <span style="color:#58a6ff">{map_label}</span>'
        f' &nbsp;·&nbsp; 📅 <span style="color:#58a6ff">{", ".join(dates_used)}</span>'
        f' &nbsp;·&nbsp; 🎮 <span style="color:#58a6ff">{match_used}</span>'
        f' &nbsp;·&nbsp; ⚔️ <span style="color:#58a6ff">{evts_used}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Metrics ───────────────────────────────────────────────────────────────
    combat_rows   = len(marker_df)
    movement_rows = len(path_df)
    total_rows    = combat_rows + movement_rows
    kill_count    = int(len(marker_df[marker_df["event"].isin(["Kill","BotKill"])]))

    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    mc1.metric(
        "Game Events",
        f"{combat_rows:,}",
        help="Kills, deaths, loot pickups and storm deaths on this map."
    )
    mc2.metric(
        "Human Players",
        int(combined_df[~combined_df["is_bot"]]["user_id_from_file"].nunique()),
        help="Unique human players in this view."
    )
    mc3.metric(
        "Bots",
        int(combined_df[combined_df["is_bot"]]["user_id_from_file"].nunique()),
        help="Unique bot opponents in this view."
    )
    mc4.metric(
        "Matches",
        int(combined_df["match_id_clean"].nunique()),
        help="Number of matches included in this view."
    )
    mc5.metric("Kills", kill_count,
               help="Player kills (human-on-human and human-on-bot).")

    # FIX 13: plain English breakdown bar
    st.markdown(
        f'<div class="info-bar">'
        f'🚶 Player movement recorded: <span style="color:#58a6ff">{movement_rows:,}</span> positions'
        f' &nbsp;·&nbsp; '
        f'⚔️ Game events: <span style="color:#58a6ff">{combat_rows:,}</span>'
        f' &nbsp;·&nbsp; '
        f'📊 Total data points: <span style="color:#58a6ff">{total_rows:,}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # FIX 5: repeat stale hint near the map so it's visible when scrolled down
    if is_stale:
        st.markdown(
            '<div class="stale-map-hint">'
            '⚠️  This map reflects your previous filters. '
            'Scroll up and click Show Map to update.'
            '</div>',
            unsafe_allow_html=True,
        )

    # Build figure only when needed — identified by filters_hash.
    # If hash matches what is already stored, reuse the cached figure.
    # This prevents "Generating map..." from showing on every rerun.
    current_fig_hash = st.session_state.get("mv_filters_hash")
    cached_fig_hash  = st.session_state.get("mv_fig_hash")

    if current_fig_hash != cached_fig_hash or st.session_state.get("mv_fig") is None:
        # New filters — build the figure with progress feedback
        with st.status("🗺️ Generating map — please wait…", expanded=True) as status:
            st.write(f"Processing {len(combined_df):,} data points…")
            fig = build_map_fig(
                combined_df, map_used,
                show_paths    = st.session_state["mv_paths_used"],
                show_events   = st.session_state["mv_markers_used"],
                active_events = active_filter,
            )
            st.session_state["mv_fig"]      = fig
            st.session_state["mv_fig_hash"] = current_fig_hash
            st.session_state["mv_building"] = False
            status.update(label="✅ Map ready", state="complete", expanded=False)
    else:
        # Same filters — use cached figure, no rebuild, no spinner
        fig = st.session_state["mv_fig"]

    # FIX 7: zoom/pan instructions above the map
    st.markdown(
        '<div style="font-size:0.72rem;color:#444d56;margin-bottom:4px;'
        'font-family:Share Tech Mono,monospace;">'
        '🖱 Scroll to zoom · Click and drag to pan · Double-click to reset view'
        '</div>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(fig, use_container_width=True,
                    config={"scrollZoom":True,"displayModeBar":True,
                            "modeBarButtonsToRemove":["select2d","lasso2d"]})

    # FIX 14: single legend below map — Plotly legend disabled in _map_layout
    st.markdown(
        '<div style="font-size:0.78rem;color:#8b949e;margin:8px 0 6px;">',
        unsafe_allow_html=True,
    )
    st.markdown("**What's on the map:**")
    st.markdown('</div>', unsafe_allow_html=True)

    if active_filter:
        legend_events = {e: EVENT_COLORS[e] for e in active_filter if e in EVENT_COLORS}
    else:
        legend_events = {e: EVENT_COLORS[e] for e in COMBAT_EVENTS}

    if st.session_state["mv_paths_used"] and not path_df.empty:
        has_humans = not path_df[path_df["is_bot"] == False].empty
        has_bots   = not path_df[path_df["is_bot"] == True].empty
        if has_humans:
            legend_events["Human Paths"] = "rgba(88,166,255,0.8)"
        if has_bots:
            legend_events["Bot Paths"]   = "rgba(139,148,158,0.8)"

    lcols = st.columns(max(len(legend_events), 1))
    for i,(evt,color) in enumerate(legend_events.items()):
        lcols[i].markdown(
            f'<div class="event-pill" style="background:{color}22;'
            f'border:1px solid {color};color:{color};">{evt}</div>',
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — HEATMAPS
# ─────────────────────────────────────────────────────────────────────────────
def render_heatmap(df):
    dates_list = get_dates_list(df)

    st.markdown("""
    <div style="margin-bottom:14px;">
      <span style="font-family:'Rajdhani',sans-serif;font-size:1.15rem;font-weight:700;
                   color:#e6edf3;letter-spacing:0.06em;">🔥 Heatmap</span>
      <span style="font-family:'Share Tech Mono',monospace;font-size:0.68rem;
                   color:#444d56;margin-left:10px;">Select filters, then click Show Heatmap</span>
    </div>
    """, unsafe_allow_html=True)

    # ── GROUP 1: Map ──────────────────────────────────────────────────────────
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Map (required)</div>', unsafe_allow_html=True)
    hm_map = st.radio(
        "Map", MAPS, index=None, horizontal=True,
        key="hm_map_radio", label_visibility="collapsed",
    )
    if not hm_map:
        st.caption("← Select a map to begin")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── GROUP 2: Date checkboxes ───────────────────
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Date(s) — uncheck to exclude</div>',
                unsafe_allow_html=True)

    st.session_state.setdefault("hm_date_all", True)
    for _d in dates_list:
        st.session_state.setdefault(f"hm_date_{_d}", True)

    def _on_hm_date_all_change():
        new_val = st.session_state["hm_date_all"]
        for _d in dates_list:
            st.session_state[f"hm_date_{_d}"] = new_val

    def _on_hm_date_individual_change():
        all_on = all(st.session_state.get(f"hm_date_{_d}", True) for _d in dates_list)
        st.session_state["hm_date_all"] = all_on

    hm_da_cols = st.columns([1] + [1]*len(dates_list))
    with hm_da_cols[0]:
        hm_all_dates = st.checkbox(
            "All", key="hm_date_all",
            on_change=_on_hm_date_all_change,
        )
    hm_date_checks = {}
    for i, d in enumerate(dates_list):
        with hm_da_cols[i+1]:
            hm_date_checks[d] = st.checkbox(
                d, key=f"hm_date_{d}",
                disabled=hm_all_dates,
                on_change=_on_hm_date_individual_change,
            )

    if hm_all_dates:
        hm_dates = None
    else:
        sel = [d for d,v in hm_date_checks.items() if v]
        hm_dates = sel if sel else None

    # Data sufficiency notice when only one date selected
    if hm_dates and len(hm_dates) == 1:
        st.markdown(
            '<div style="font-size:0.72rem;color:#f0a500;margin-top:4px;">'
            '⚠️ Heatmaps are more reliable with more data. '
            'Single-day results may appear noisy.'
            '</div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── GROUP 3: Match ────────────────────────────────────────────────────────
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Match (optional)</div>', unsafe_allow_html=True)
    if not hm_map:
        st.caption("Select a map first to see available matches.")
        hm_match_sel = "All Matches"
        hm_match     = None
    else:
        hm_dates_tuple = tuple(hm_dates) if hm_dates else None
        hm_matches     = get_map_matches(df, hm_map, hm_dates_tuple)
        hm_match_opts  = ["All Matches"] + list(hm_matches)
        hm_saved       = st.session_state.get("hm_match_sel", "All Matches")
        hm_safe_idx    = hm_match_opts.index(hm_saved) if hm_saved in hm_match_opts else 0
        hm_match_sel   = st.selectbox(
            "Match", hm_match_opts, index=hm_safe_idx,
            format_func=lambda x: "All Matches" if x=="All Matches" else match_label(x),
            key="hm_match_sel",
            help="Each entry shows: Match ID | Date | Players (P) | Bots (B)",
            label_visibility="collapsed",
        )
        hm_match = None if hm_match_sel=="All Matches" else hm_match_sel
    st.markdown('</div>', unsafe_allow_html=True)

    # ── GROUP 4: Overlay type ─────────────────────────────────────────────────
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Overlay Type</div>', unsafe_allow_html=True)
    hm_type = st.radio(
        "Overlay", list(OVERLAY_INFO.keys()),
        horizontal=True, key="hm_type_sel", label_visibility="collapsed",
    )
    if hm_type:
        icon, summary, detail = OVERLAY_INFO[hm_type]
        st.markdown(
            f'<div style="background:#0d1117;border:1px solid #21262d;border-radius:6px;'
            f'padding:8px 14px;margin-top:8px;font-size:0.78rem;">'
            f'<span style="color:#e6edf3;font-weight:600;">{icon} {summary}</span>'
            f'<span style="color:#444d56;font-size:0.72rem;margin-left:10px;">{detail}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # Stale detection — includes overlay type so banner shows when ANY filter changes
    # Even though overlay doesn't re-query data, the user expects feedback
    hm_hash = str((hm_data_hash(hm_map, hm_dates, hm_match_sel), hm_type))
    hm_is_stale = (
        st.session_state["hm_show"]
        and st.session_state.get("hm_filters_hash") is not None
        and st.session_state.get("hm_filters_hash") != hm_hash
    )
    if hm_is_stale:
        st.markdown(
            '<div class="stale-banner">'
            '⚠️  Filters changed — click <b>Show Heatmap</b> to refresh.'
            '</div>',
            unsafe_allow_html=True,
        )

    sb1, _, sb2 = st.columns([2, 6, 1])
    with sb1:
        show_clicked = st.button("▶  Show Heatmap", key="hm_show_btn",
                                 type="primary", use_container_width=True)
    with sb2:
        st.write("")  # spacer
    if show_clicked:
        if not hm_map:
            st.error("⬆️  Please select a Map first.")
        else:
            with st.spinner("Querying data…"):
                # FIX 8: apply all filters first, then copy once
                mask = df["map_id"] == hm_map
                if hm_dates:
                    mask &= df["date_str"].isin(hm_dates)
                if hm_match:
                    mask &= df["match_id_clean"] == hm_match
                data = df[mask].copy()
            st.session_state["hm_result"]       = data
            st.session_state["hm_map_used"]     = hm_map
            st.session_state["hm_type_used"]    = hm_type
            st.session_state["hm_dates_used"]   = hm_dates
            st.session_state["hm_match_used"]   = hm_match_sel
            st.session_state["hm_show"]         = True
            st.session_state["hm_filters_hash"] = hm_hash
            # FIX 9: invalidate cached figure when data changes
            st.session_state["hm_fig"]          = None
            st.session_state["hm_fig_hash"]     = None
            st.rerun()  # commit all session state before rendering

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    if not st.session_state["hm_show"]:
        st.markdown("""
        <div class="empty-state">
          <div style="font-size:3rem;margin-bottom:12px;">🔥</div>
          <div class="title">No heatmap loaded yet</div>
          <div class="hint">1. Select a <b>Map</b> above</div>
          <div class="hint">2. Optionally filter by <b>Date</b> or <b>Match</b></div>
          <div class="hint">3. Choose an <b>Overlay Type</b></div>
          <div class="hint">4. Click <b>▶ Show Heatmap</b> — the button is just below</div>
          <div style="margin-top:20px;font-size:0.75rem;color:#30363d;">
            Tip: The heatmap is interactive — scroll to zoom, drag to pan
          </div>
        </div>
        """, unsafe_allow_html=True)
        return

    data    = st.session_state["hm_result"]
    map_u   = st.session_state["hm_map_used"]
    # Read overlay from current widget — not stored — so changing overlay
    # immediately updates the figure without re-clicking Show Heatmap
    htype   = st.session_state.get("hm_type_sel", st.session_state["hm_type_used"])
    dates_u = st.session_state.get("hm_dates_used")
    match_u = st.session_state.get("hm_match_used","All Matches")

    if data is None or data.empty:
        st.warning("No data found. Try broadening your filters.")
        return

    # ── Metric cards ─────────────────────────────────────────────────────────
    hm1, hm2, hm3, hm4 = st.columns(4)
    hm1.metric("Total Records", f"{len(data):,}",
               help="All events in this map/date/match selection.")
    hm2.metric("Human Players",
               int(data[~data["is_bot"]]["user_id_from_file"].nunique()),
               help="Unique human players in this heatmap.")
    hm3.metric("Bots",
               int(data[data["is_bot"]]["user_id_from_file"].nunique()),
               help="Unique bots in this heatmap.")
    hm4.metric("Matches",
               int(data["match_id_clean"].nunique()),
               help="Number of matches contributing to this heatmap.")
    st.markdown("<br>", unsafe_allow_html=True)

    # Active filter summary
    dates_label = ", ".join(dates_u) if dates_u else "All dates"
    st.markdown(
        f'<div style="background:#0d1117;border:1px solid #21262d;border-radius:8px;'
        f'padding:10px 16px;margin-bottom:14px;font-family:Share Tech Mono,monospace;'
        f'font-size:0.75rem;color:#8b949e;">'
        f'<span style="color:#e6edf3;font-weight:600;">Currently showing:</span>'
        f' &nbsp; 🗺️ <span style="color:#58a6ff">{map_u}</span>'
        f' &nbsp;·&nbsp; 📅 <span style="color:#58a6ff">{dates_label}</span>'
        f' &nbsp;·&nbsp; 🔥 <span style="color:#58a6ff">{htype}</span>'
        f' &nbsp;·&nbsp; 🎮 <span style="color:#58a6ff">{"All matches" if match_u == "All Matches" else match_u[:12]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # FIX 1 & 9: Cache heatmap figure by (data hash + overlay type)
    # Only rebuild when overlay type changes — data stays the same
    # Deterministic cache key — id(data) changes every rerun, use hash instead
    # Use locally computed hm_hash (not session state) so the key is always
    # based on current filter values, not potentially stale session state
    hm_fig_key = str((hm_hash, htype))
    if (st.session_state.get("hm_fig") is None or
            st.session_state.get("hm_fig_hash") != hm_fig_key):
        # FIX 11: st.status for build feedback
        with st.status("🔥 Building heatmap — please wait…", expanded=True) as hm_status:
            st.write(f"Analysing {len(data):,} data points…")
            fig, event_count = build_heatmap_fig(data, htype, map_u)
            st.session_state["hm_fig"]      = fig
            st.session_state["hm_fig_hash"] = hm_fig_key
            st.session_state["hm_evt_count"]= event_count
            hm_status.update(label="✅ Heatmap ready", state="complete", expanded=False)
    else:
        fig         = st.session_state["hm_fig"]
        event_count = st.session_state.get("hm_evt_count", 0)

    # Show event count so designer can assess reliability
    evt_label = HEATMAP_EVT_LABELS.get(htype, "events")
    reliability = ("✅ Good sample size" if event_count >= 500
                   else "⚠️ Small sample — interpret with caution" if event_count >= 50
                   else "🔴 Very few events — results may not be meaningful")
    n_matches = int(data["match_id_clean"].nunique())
    if n_matches == 1 and event_count < 500:
        reliability += " (single match)"
    st.markdown(
        f'<div class="info-bar">'
        f'📊 {event_count:,} {evt_label} contributing to this heatmap &nbsp;·&nbsp; '
        f'{reliability}'
        f'</div>',
        unsafe_allow_html=True,
    )

    if hm_is_stale:
        st.markdown(
            '<div class="stale-map-hint">'
            '⚠️  This heatmap reflects previous filters. '
            'Scroll up and click Show Heatmap to update.'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="font-size:0.72rem;color:#444d56;margin-bottom:4px;'
        'font-family:Share Tech Mono,monospace;">'
        '🖱 Scroll to zoom · Click and drag to pan · Double-click to reset view'
        '</div>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(fig, use_container_width=True,
                    config={"scrollZoom":True,"displayModeBar":True,
                            "modeBarButtonsToRemove":["select2d","lasso2d"]})

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — TIMELINE
# ─────────────────────────────────────────────────────────────────────────────
def render_timeline(df):
    dates_list = get_dates_list(df)

    # FIX 11: styled header consistent with other tabs
    st.markdown("""
    <div style="margin-bottom:14px;">
      <span style="font-family:'Rajdhani',sans-serif;font-size:1.15rem;font-weight:700;
                   color:#e6edf3;letter-spacing:0.06em;">⏱️ Timeline</span>
      <span style="font-family:'Share Tech Mono',monospace;font-size:0.68rem;
                   color:#444d56;margin-left:10px;">Select a match to replay it second by second</span>
    </div>
    """, unsafe_allow_html=True)

    # FIX 1: Map — radio buttons consistent with other tabs
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Map (required)</div>', unsafe_allow_html=True)
    tl_map = st.radio(
        "Map", MAPS, index=None, horizontal=True,
        key="tl_map_radio", label_visibility="collapsed",
    )
    if not tl_map:
        st.caption("← Select a map to begin")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── GROUP 2: Date checkboxes — narrows match dropdown ────────────────────
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Date(s) — filter matches by day</div>',
                unsafe_allow_html=True)

    st.session_state.setdefault("tl_date_all", True)
    for _d in dates_list:
        st.session_state.setdefault(f"tl_date_{_d}", True)

    def _on_tl_date_all_change():
        new_val = st.session_state["tl_date_all"]
        for _d in dates_list:
            st.session_state[f"tl_date_{_d}"] = new_val

    def _on_tl_date_individual_change():
        all_on = all(st.session_state.get(f"tl_date_{_d}", True) for _d in dates_list)
        st.session_state["tl_date_all"] = all_on

    tl_da_cols = st.columns([1] + [1]*len(dates_list))
    with tl_da_cols[0]:
        tl_all_dates = st.checkbox(
            "All", key="tl_date_all",
            on_change=_on_tl_date_all_change,
        )
    tl_date_checks = {}
    for i, d in enumerate(dates_list):
        with tl_da_cols[i+1]:
            tl_date_checks[d] = st.checkbox(
                d, key=f"tl_date_{d}",
                disabled=tl_all_dates,
                on_change=_on_tl_date_individual_change,
            )

    if tl_all_dates:
        tl_dates = None
    else:
        sel = [d for d,v in tl_date_checks.items() if v]
        tl_dates = sel if sel else None

    st.markdown('</div>', unsafe_allow_html=True)

    # ── GROUP 3: Match dropdown — filtered by map + dates ────────────────────
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Match (required)</div>', unsafe_allow_html=True)
    if not tl_map:
        st.caption("Select a map first to see available matches.")
        tl_match     = None
        tl_match_sel = None
    else:
        tl_dates_tuple = tuple(tl_dates) if tl_dates else None
        tl_summaries   = get_match_summaries(df, tl_map, tl_dates_tuple)
        tl_match_ids   = list(tl_summaries.keys())
        n_matches      = len(tl_match_ids)
        tl_saved       = st.session_state.get("tl_match_sel")
        tl_safe_idx    = tl_match_ids.index(tl_saved) if tl_saved in tl_match_ids else None
        tl_match_sel   = st.selectbox(
            "Match", tl_match_ids, index=tl_safe_idx,
            placeholder=f"Choose from {n_matches} matches…" if tl_match_ids else "No matches for these filters",
            format_func=lambda x: tl_summaries.get(x, match_label(x)),
            key="tl_match_sel",
            help="Each entry shows: Match ID | Date | Players (P) | Bots (B)",
            label_visibility="collapsed",
        )
        tl_match = tl_match_sel
        # Show how many matches are visible after date filter
        if tl_dates:
            st.caption(f"Showing {n_matches} matches for {', '.join(tl_dates)}")
    st.markdown('</div>', unsafe_allow_html=True)

    # FIX 17: "All Players" label instead of "All"
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Player Type</div>', unsafe_allow_html=True)
    tl_players = st.radio(
        "Players", ["All Players","Humans Only","Bots Only"],
        horizontal=True, key="tl_players_sel", label_visibility="collapsed",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # FIX 10: Stale detection
    tl_hash = str((tl_map, tuple(tl_dates) if tl_dates else (), tl_match_sel, tl_players))
    tl_is_stale = (
        st.session_state["tl_show"]
        and st.session_state.get("tl_filters_hash") is not None
        and st.session_state.get("tl_filters_hash") != tl_hash
    )
    if tl_is_stale:
        st.markdown(
            '<div class="stale-banner">'
            '⚠️  Filters changed — click <b>Load Match</b> to refresh.'
            '</div>',
            unsafe_allow_html=True,
        )

    # FIX 16: sticky Load Match button layout
    sb1, _, sb2 = st.columns([2, 6, 1])
    with sb1:
        show_clicked = st.button("▶  Load Match", key="tl_show_btn",
                                 type="primary", use_container_width=True)
    with sb2:
        st.write("")

    if show_clicked:
        if not tl_map:
            st.error("⬆️  Please select a Map.")
        elif not tl_match:
            st.error("⬆️  Please select a Match.")
        else:
            with st.spinner("Loading match data…"):
                # FIX 3: run_match_query already returns .copy() — no double copy
                mdf = run_match_query(df, tl_match)
                if tl_players == "Humans Only":
                    mdf = mdf[~mdf["is_bot"]].copy()
                elif tl_players == "Bots Only":
                    mdf = mdf[mdf["is_bot"]].copy()
                if not mdf.empty:
                    # Per-player normalization — each player's ts starts at 0
                    # This handles late-joiners whose ts=0 doesn't align with match start
                    # elapsed_s = seconds into the match for each event per player
                    mdf["elapsed_s"] = (
                        mdf.groupby("user_id_from_file")["ts"]
                        .transform(lambda x: x.astype(float) - float(x.min()))
                    )
                    total_s = max(float(mdf["elapsed_s"].max()), 1.0)
                    combat = mdf[~mdf["event"].isin(MOVE_EVENTS)].copy()
                    if not combat.empty:
                        human_uids = sorted(mdf[~mdf["is_bot"]]["user_id_from_file"].unique())
                        bot_uids   = sorted(mdf[mdf["is_bot"]]["user_id_from_file"].unique())
                        human_ids  = {uid: f"👤 P{i+1}" for i,uid in enumerate(human_uids)}
                        bot_ids    = {uid: f"🤖 B{i+1}" for i,uid in enumerate(bot_uids)}
                        id_map     = {**human_ids, **bot_ids}
                        combat["player_label"] = combat["user_id_from_file"].map(id_map)
                        # Pre-build Gantt base figure — only vline added per render
                        gantt_traces = []
                        gantt_base   = go.Figure()
                        for evt, grp in combat.groupby("event"):
                            gantt_traces.append(dict(
                                x=grp["elapsed_s"].tolist(),
                                y=grp["player_label"].tolist(),
                                name=evt,
                                color=EVENT_COLORS.get(evt,"#fff"),
                                symbol=EVENT_SYMBOLS.get(evt,"circle"),
                            ))
                            gantt_base.add_trace(go.Scatter(
                                x=grp["elapsed_s"].tolist(),
                                y=grp["player_label"].tolist(),
                                mode="markers", name=evt,
                                marker=dict(color=EVENT_COLORS.get(evt,"#fff"),
                                            symbol=EVENT_SYMBOLS.get(evt,"circle"),
                                            size=10,
                                            line=dict(color="#0a0c10",width=1)),
                                hovertemplate=f"<b>{evt}</b><br>T+%{{x:.1f}}s<br>%{{y}}<extra></extra>",
                            ))
                        n_rows = combat["player_label"].nunique()
                        gantt_base.update_layout(
                            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                            font=dict(color="#c9d1d9", size=11),
                            legend=dict(bgcolor="#161b22", bordercolor="#21262d",
                                        borderwidth=1, orientation="h",
                                        yanchor="bottom", y=1.02, x=0),
                            xaxis=dict(title="Elapsed (seconds)", gridcolor="#21262d",
                                       range=[0, total_s], zeroline=False,
                                       tickfont=dict(color="#8b949e")),
                            yaxis=dict(gridcolor="#21262d", autorange="reversed",
                                       zeroline=False,
                                       tickfont=dict(color="#c9d1d9", size=10)),
                            height=max(320, n_rows*30+100),
                            margin=dict(l=10, r=20, t=50, b=50),
                        )
                        # Pre-build histogram base — bins fixed, only vline changes
                        hfig_base = px.histogram(
                            combat, x="elapsed_s", color="event",
                            nbins=max(20, int(total_s//15)),
                            color_discrete_map=EVENT_COLORS,
                            barmode="stack", height=250,
                            labels={"elapsed_s":"Elapsed (seconds)", "count":"Events"},
                        )
                        hfig_base.update_layout(
                            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                            font=dict(color="#c9d1d9"),
                            legend=dict(bgcolor="#161b22", bordercolor="#21262d",
                                        borderwidth=1, orientation="h",
                                        yanchor="bottom", y=1.02),
                            xaxis=dict(gridcolor="#21262d", range=[0,total_s],
                                       zeroline=False),
                            yaxis=dict(gridcolor="#21262d", title="Event count",
                                       zeroline=False),
                            margin=dict(l=10, r=10, t=40, b=40),
                        )
                    else:
                        gantt_traces = []
                        gantt_base   = None
                        hfig_base    = None
                        n_rows       = 0
                        id_map       = {}
                else:
                    total_s      = 1.0
                    combat       = pd.DataFrame()
                    gantt_traces = []
                    gantt_base   = None
                    hfig_base    = None
                    n_rows       = 0
                    id_map       = {}
                n_h = int(mdf[~mdf["is_bot"]]["user_id_from_file"].nunique()) if not mdf.empty else 0
                n_b = int(mdf[mdf["is_bot"]]["user_id_from_file"].nunique()) if not mdf.empty else 0

            st.session_state[f"tl_slider_{tl_match}"] = 0.0
            st.session_state["tl_data"]         = mdf
            st.session_state["tl_combat"]        = combat
            st.session_state["tl_gantt_traces"]  = gantt_traces
            st.session_state["tl_gantt_base"]    = gantt_base
            st.session_state["tl_hfig_base"]     = hfig_base
            st.session_state["tl_n_rows"]        = n_rows
            st.session_state["tl_id_map"]        = id_map
            st.session_state["tl_map_used"]      = tl_map
            st.session_state["tl_match_used"]    = tl_match
            st.session_state["tl_total_s"]       = total_s
            st.session_state["tl_players_used"]  = tl_players
            st.session_state["tl_n_h"]           = n_h
            st.session_state["tl_n_b"]           = n_b
            st.session_state["tl_show"]          = True
            st.session_state["tl_filters_hash"]  = tl_hash
            st.rerun()

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # FIX 12: rich empty state
    if not st.session_state["tl_show"]:
        st.markdown("""
        <div class="empty-state">
          <div style="font-size:3rem;margin-bottom:12px;">⏱️</div>
          <div class="title">No match loaded yet</div>
          <div class="hint">1. Select a <b>Map</b> above</div>
          <div class="hint">2. Optionally filter by <b>Date</b> to narrow the match list</div>
          <div class="hint">3. Pick a <b>Match</b> — each entry shows date and player count</div>
          <div class="hint">4. Choose a <b>Player Type</b> filter</div>
          <div class="hint">5. Click <b>▶ Load Match</b> to start the replay</div>
          <div style="margin-top:20px;font-size:0.75rem;color:#30363d;">
            Tip: Use the scrub slider or jump buttons to move through the match
          </div>
        </div>
        """, unsafe_allow_html=True)
        return

    mdf          = st.session_state["tl_data"]
    map_u        = st.session_state["tl_map_used"]
    match_u      = st.session_state["tl_match_used"]
    total_s      = st.session_state["tl_total_s"]
    combat       = st.session_state["tl_combat"]
    gantt_traces = st.session_state["tl_gantt_traces"]
    gantt_base   = st.session_state.get("tl_gantt_base")
    hfig_base    = st.session_state.get("tl_hfig_base")
    n_rows       = st.session_state["tl_n_rows"]
    id_map       = st.session_state["tl_id_map"]

    if mdf is None or mdf.empty:
        st.warning("No data for this match / player filter.")
        return

    # Active filter summary bar — read stored value not current widget
    players_label = st.session_state.get("tl_players_used", tl_players)
    st.markdown(
        f'<div style="background:#0d1117;border:1px solid #21262d;border-radius:8px;'
        f'padding:10px 16px;margin-bottom:14px;font-family:Share Tech Mono,monospace;'
        f'font-size:0.75rem;color:#8b949e;">'
        f'<span style="color:#e6edf3;font-weight:600;">Currently showing:</span>'
        f' &nbsp; 🗺️ <span style="color:#58a6ff">{map_u}</span>'
        f' &nbsp;·&nbsp; 🎮 <span style="color:#58a6ff">{match_label(match_u)}</span>'
        f' &nbsp;·&nbsp; 👥 <span style="color:#58a6ff">{players_label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Stale hint near chart
    if tl_is_stale:
        st.markdown(
            '<div class="stale-map-hint">'
            '⚠️  This data reflects previous filters. '
            'Scroll up and click Load Match to update.'
            '</div>',
            unsafe_allow_html=True,
        )

    n_h = st.session_state.get("tl_n_h", 0)
    n_b = st.session_state.get("tl_n_b", 0)
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Duration",      f"{total_s:.0f}s",
               help="Total match duration in seconds.")
    mc2.metric("Human Players", n_h,
               help="Unique human players in this match.")
    mc3.metric("Bots",          n_b,
               help="Unique bots in this match.")
    mc4.metric("Events",        f"{len(mdf):,}",
               help="Total events recorded in this match.")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # Initialise slider position in session state if not already set
    slider_key = f"tl_slider_{match_u}"
    st.session_state.setdefault(slider_key, 0.0)

    # ── Jump buttons ──────────────────────────────────────────────────────────
    def _make_jump(seconds, key, max_s):
        """Return on_click callback that advances slider by `seconds`."""
        def _jump():
            cur = float(st.session_state.get(key, 0.0))
            st.session_state[key] = min(cur + seconds, max_s)
        return _jump

    def _make_back(seconds, key):
        """Return on_click callback that rewinds slider by `seconds`."""
        def _back():
            cur = float(st.session_state.get(key, 0.0))
            st.session_state[key] = max(cur - seconds, 0.0)
        return _back

    def _reset(key):
        st.session_state[key] = 0.0

    # Read current slider position BEFORE rendering buttons
    # so disabled state is correctly computed on every rerun
    cur_pos = float(st.session_state.get(slider_key, 0.0))

    st.markdown(
        '<div style="font-size:0.72rem;color:#444d56;margin-bottom:4px;'
        'font-family:Share Tech Mono,monospace;">'
        '⏱ Jump controls — click to advance or rewind the timeline'
        '</div>',
        unsafe_allow_html=True,
    )
    btn_cols = st.columns([1, 1, 1, 0.3, 1, 1, 1, 1, 1])
    with btn_cols[0]:
        # Reset disabled when already at start
        st.button("⏮ Reset", key="tl_reset_btn",
                  on_click=lambda: _reset(slider_key),
                  use_container_width=True,
                  disabled=cur_pos <= 0.0)
    with btn_cols[1]:
        st.button("−30s", key="tl_back30",
                  on_click=_make_back(30, slider_key),
                  use_container_width=True,
                  disabled=cur_pos <= 0.0)
    with btn_cols[2]:
        st.button("−10s", key="tl_back10",
                  on_click=_make_back(10, slider_key),
                  use_container_width=True,
                  disabled=cur_pos <= 0.0)
    # spacer col [3]
    with btn_cols[4]:
        st.button("+1s",  key="tl_fwd1",
                  on_click=_make_jump(1,  slider_key, total_s),
                  use_container_width=True, type="primary",
                  disabled=cur_pos >= total_s)
    with btn_cols[5]:
        st.button("+5s",  key="tl_fwd5",
                  on_click=_make_jump(5,  slider_key, total_s),
                  use_container_width=True, type="primary",
                  disabled=cur_pos >= total_s)
    with btn_cols[6]:
        st.button("+10s", key="tl_fwd10",
                  on_click=_make_jump(10, slider_key, total_s),
                  use_container_width=True, type="primary",
                  disabled=cur_pos >= total_s)
    with btn_cols[7]:
        st.button("+30s", key="tl_fwd30",
                  on_click=_make_jump(30, slider_key, total_s),
                  use_container_width=True, type="primary",
                  disabled=cur_pos >= total_s)
    with btn_cols[8]:
        st.button("+60s", key="tl_fwd60",
                  on_click=_make_jump(60, slider_key, total_s),
                  use_container_width=True, type="primary",
                  disabled=cur_pos >= total_s)

    step_s = max(1.0, round(total_s / 120, 1))
    playback_s = st.slider(
        "Scrub through match (seconds)",
        min_value=0.0, max_value=total_s,
        step=step_s,
        key=slider_key,
        help="Drag the slider or use the jump buttons above.",
    )

    # FIX 5: Map figure — only rebuild when slider moves (use st.empty placeholder)
    st.markdown(
        '<div style="font-size:0.72rem;color:#444d56;margin-bottom:4px;'
        'font-family:Share Tech Mono,monospace;">'
        '🖱 Scroll to zoom · Click and drag to pan · Double-click to reset view'
        '</div>',
        unsafe_allow_html=True,
    )
    up_to = mdf[mdf["elapsed_s"] <= playback_s]
    # Map must rebuild on every slider move (data slice changes) but we keep it fast
    # by using the pre-sorted mdf and a simple boolean filter — no heavy groupby
    st.plotly_chart(
        build_map_fig(up_to, map_u, show_paths=True, show_events=True,
                      path_width=2.5,
                      path_opacity_human=0.85,
                      path_opacity_bot=0.65),
        use_container_width=True,
        key=f"tl_map_{match_u}_{playback_s}",
        config={"scrollZoom":True,"displayModeBar":True,
                "modeBarButtonsToRemove":["select2d","lasso2d"]},
    )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    st.markdown(
        '<div style="font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:700;'
        'color:#e6edf3;margin:8px 0 4px;">👥 Player Activity</div>',
        unsafe_allow_html=True,
    )
    if gantt_traces:
        kill_times = [x for t in gantt_traces if t["name"] in ("Kill","BotKill")
                      for x in t["x"]]
        if kill_times:
            st.markdown(
                f'<div style="font-size:0.78rem;color:#8b949e;margin-bottom:8px;">'
                f'💡 First kill at <span style="color:#ff4444">T={min(kill_times):.0f}s</span>'
                f' · Last kill at <span style="color:#ff4444">T={max(kill_times):.0f}s</span>'
                f' · {len(kill_times)} total kills'
                f'</div>',
                unsafe_allow_html=True,
            )
    if not gantt_traces or gantt_base is None:
        st.info("No combat or loot events in this match.")
    else:
        import copy
        # Only add vline to pre-built base — no trace rebuild on slider move
        gantt = copy.deepcopy(gantt_base)
        gantt.add_vline(
            x=playback_s, line_width=2, line_dash="dash", line_color="#ff4444",
            annotation_text=f"▶ {playback_s:.0f}s",
            annotation_font_color="#ff4444", annotation_font_size=11,
            annotation_position="top right",
        )
        st.plotly_chart(gantt, use_container_width=True,
                        key=f"tl_gantt_{match_u}_{playback_s}")

        # FIX 8: Player label lookup table
        if id_map:
            with st.expander("🔎 Player Label Lookup — who is P1, P2, B1…"):
                rows = [{"Label": lbl, "Short ID": uid[:8]+"…"+uid[-4:],
                         "Full User ID": uid}
                        for uid, lbl in id_map.items()]
                st.dataframe(pd.DataFrame(rows), use_container_width=True,
                             hide_index=True)
                st.caption("Copy a Full User ID to search in the Raw Data Explorer in Stats tab.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # FIX 7: Histogram — rebuild from cached combat, only vline changes
    st.markdown(
        '<div style="font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:700;'
        'color:#e6edf3;margin:8px 0 6px;">📊 Event Density</div>',
        unsafe_allow_html=True,
    )
    if not combat.empty and hfig_base is not None:
        # Only add vline — histogram bins fixed, no rebuild needed
        hfig = copy.deepcopy(hfig_base)
        hfig.add_vline(
            x=playback_s, line_width=2, line_dash="dash", line_color="#ff4444",
            annotation_text=f"T={playback_s:.0f}s",
            annotation_font_color="#ff4444", annotation_font_size=10,
        )
        st.plotly_chart(hfig, use_container_width=True,
                        key=f"tl_hist_{match_u}_{playback_s}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — STATS
# ─────────────────────────────────────────────────────────────────────────────
def render_stats(df):
    dates_list = get_dates_list(df)

    # FIX 14: styled header consistent with other tabs
    st.markdown("""
    <div style="margin-bottom:14px;">
      <span style="font-family:'Rajdhani',sans-serif;font-size:1.15rem;font-weight:700;
                   color:#e6edf3;letter-spacing:0.06em;">📊 Stats</span>
      <span style="font-family:'Share Tech Mono',monospace;font-size:0.68rem;
                   color:#444d56;margin-left:10px;">Select filters, then click Show Stats</span>
    </div>
    """, unsafe_allow_html=True)

    # FIX 2: Map — radio buttons consistent with Map View and Heatmap
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Map</div>', unsafe_allow_html=True)
    st_map = st.radio(
        "Map", ["All Maps"] + MAPS, index=0,
        horizontal=True, key="st_map_radio",
        label_visibility="collapsed",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # FIX 3: Date — checkboxes with All master toggle consistent with other tabs
    st.markdown('<div class="filter-group">', unsafe_allow_html=True)
    st.markdown('<div class="filter-group-label">Date(s) — uncheck to exclude</div>',
                unsafe_allow_html=True)

    st.session_state.setdefault("st_date_all", True)
    for _d in dates_list:
        st.session_state.setdefault(f"st_date_{_d}", True)

    def _on_st_date_all_change():
        new_val = st.session_state["st_date_all"]
        for _d in dates_list:
            st.session_state[f"st_date_{_d}"] = new_val

    def _on_st_date_individual_change():
        all_on = all(st.session_state.get(f"st_date_{_d}", True) for _d in dates_list)
        st.session_state["st_date_all"] = all_on

    st_da_cols = st.columns([1] + [1]*len(dates_list))
    with st_da_cols[0]:
        st_all_dates = st.checkbox(
            "All", key="st_date_all",
            on_change=_on_st_date_all_change,
        )
    st_date_checks = {}
    for i, d in enumerate(dates_list):
        with st_da_cols[i+1]:
            st_date_checks[d] = st.checkbox(
                d, key=f"st_date_{d}",
                disabled=st_all_dates,
                on_change=_on_st_date_individual_change,
            )

    if st_all_dates:
        st_dates = None
    else:
        sel = [d for d,v in st_date_checks.items() if v]
        st_dates = sel if sel else None

    st.markdown('</div>', unsafe_allow_html=True)

    # FIX 4: Stale detection
    st_hash = str((st_map, tuple(st_dates) if st_dates else ()))
    st_is_stale = (
        st.session_state["st_show"]
        and st.session_state.get("st_filters_hash") is not None
        and st.session_state.get("st_filters_hash") != st_hash
    )
    if st_is_stale:
        st.markdown(
            '<div class="stale-banner">'
            '⚠️  Filters changed — click <b>Show Stats</b> to refresh.'
            '</div>',
            unsafe_allow_html=True,
        )

    sb1, _, sb2 = st.columns([2, 6, 1])
    with sb1:
        show_clicked = st.button("▶  Show Stats", key="st_show_btn",
                                 type="primary", use_container_width=True)
    with sb2:
        st.write("")
    if show_clicked:
        with st.spinner("Computing stats…"):
            # FIX 1: mask first, copy once
            mask = pd.Series([True]*len(df), index=df.index)
            if st_map != "All Maps":
                mask &= df["map_id"] == st_map
            if st_dates:
                mask &= df["date_str"].isin(st_dates)
            data = df[mask].copy()
        st.session_state["st_data"]         = data
        st.session_state["st_show"]         = True
        st.session_state["st_filters_hash"] = st_hash
        # FIX 9 & 17: invalidate chart cache on new data
        st.session_state["st_charts"]       = None
        st.session_state["st_insight"]      = None
        st.session_state["st_dates_used"]   = st_dates
        st.session_state["st_dates_label"]  = ", ".join(st_dates) if st_dates else "All dates"
        st.session_state["st_map_used"]     = st_map
        st.rerun()

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # FIX 15: rich empty state
    if not st.session_state["st_show"]:
        st.markdown("""
        <div class="empty-state">
          <div style="font-size:3rem;margin-bottom:12px;">📊</div>
          <div class="title">No stats loaded yet</div>
          <div class="hint">1. Select a <b>Map</b> — or leave on All Maps for full dataset</div>
          <div class="hint">2. Optionally filter by <b>Date</b></div>
          <div class="hint">3. Click <b>▶ Show Stats</b></div>
        </div>
        """, unsafe_allow_html=True)
        return

    data = st.session_state["st_data"]
    if data is None or data.empty:
        st.warning("No data found. Try broadening your filters.")
        return

    # Active filter summary bar — reads values already stored before rerun
    st.markdown(
        f'<div style="background:#0d1117;border:1px solid #21262d;border-radius:8px;'
        f'padding:10px 16px;margin-bottom:14px;font-family:Share Tech Mono,monospace;'
        f'font-size:0.75rem;color:#8b949e;">'
        f'<span style="color:#e6edf3;font-weight:600;">Currently showing:</span>'
        f' &nbsp; 🗺️ <span style="color:#58a6ff">{st.session_state.get("st_map_used","All Maps")}</span>'
        f' &nbsp;·&nbsp; 📅 <span style="color:#58a6ff">{st.session_state.get("st_dates_label","All dates")}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # FIX 7 & 8: 5 metric cards, game events separate from total
    game_events = data[~data["event"].isin(MOVE_EVENTS)]
    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("Game Events",   f"{len(game_events):,}",
              help="Combat + loot events only. Excludes movement GPS pings.")
    m2.metric("Human Players", int(data[~data["is_bot"]]["user_id_from_file"].nunique()),
              help="Unique human players in this selection.")
    m3.metric("Bots",          int(data[data["is_bot"]]["user_id_from_file"].nunique()),
              help="Unique bot opponents in this selection.")
    m4.metric("Matches",       int(data["match_id_clean"].nunique()),
              help="Unique matches in this selection.")
    m5.metric("Kills",         int(len(data[data["event"].isin(["Kill","BotKill"])])),
              help="Player kills (human + bot kills).")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # FIX 9: Cache all charts together under one key
    charts_key = st.session_state.get("st_filters_hash","")
    if st.session_state.get("st_charts") is None or        st.session_state.get("st_charts_hash") != charts_key:

        with st.status("📊 Building charts — please wait…", expanded=True) as st_status:
            st.write(f"Processing {len(data):,} records…")

            # Chart 1 — Game Event Distribution (FIX 6: excludes Position/BotPosition)
            game_only = data[~data["event"].isin(MOVE_EVENTS)]
            ec = game_only["event"].value_counts().reset_index()
            ec.columns = ["event","count"]
            f1 = px.bar(ec, x="count", y="event", orientation="h", color="event",
                       color_discrete_map=EVENT_COLORS,
                       title="Game Event Distribution", height=320)
            f1.update_layout(
                plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                font=dict(color="#c9d1d9"), showlegend=False,
                xaxis=dict(gridcolor="#21262d", title="Count"),
                yaxis=dict(gridcolor="#21262d", title=""),
                title_font=dict(color="#e6edf3"),
                margin=dict(l=10,r=10,t=40,b=10),
            )

            # Chart 2 — Events per Day with partial day annotation
            dc = data.groupby("date_str")["event"].count().reset_index()
            dc.columns = ["date","events"]
            f2 = px.bar(dc, x="date", y="events",
                       title="Events per Day",
                       color_discrete_sequence=["#58a6ff"], height=320)
            # FIX 11: annotate Feb 14 as partial day
            partial_date = "Feb 14"
            if partial_date in dc["date"].values:
                f2.add_annotation(
                    x=partial_date, y=dc[dc["date"]==partial_date]["events"].values[0],
                    text="Partial day", showarrow=True, arrowhead=2,
                    font=dict(color="#f0a500", size=11),
                    arrowcolor="#f0a500", ax=0, ay=-30,
                )
            f2.update_layout(
                plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                font=dict(color="#c9d1d9"),
                xaxis=dict(gridcolor="#21262d", title=""),
                yaxis=dict(gridcolor="#21262d", title="Event Count"),
                title_font=dict(color="#e6edf3"),
                margin=dict(l=10,r=10,t=40,b=10),
            )

            # Chart 3 — Human vs Bot Events (FIX 6: use assign not copy)
            hbc = (data.assign(type=data["is_bot"].map({True:"Bot",False:"Human"}))
                   .groupby(["type","event"])["event"].count().reset_index(name="count"))
            f3 = px.bar(hbc, x="event", y="count", color="type", barmode="group",
                       color_discrete_map={"Human":"#58a6ff","Bot":"#8b949e"},
                       title="Human vs Bot Events", height=320)
            f3.update_layout(
                plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                font=dict(color="#c9d1d9"),
                xaxis=dict(gridcolor="#21262d", tickangle=30, title=""),
                yaxis=dict(gridcolor="#21262d", title="Count"),
                title_font=dict(color="#e6edf3"),
                legend=dict(bgcolor="#161b22", bordercolor="#21262d", borderwidth=1),
                margin=dict(l=10,r=10,t=40,b=60),
            )

            # Chart 4 — Top 10 Killers
            kdf = data[data["event"].isin(["Kill","BotKill"]) & ~data["is_bot"]]
            top = (kdf.groupby("user_id_from_file")["event"]
                   .count().reset_index(name="kills")
                   .sort_values("kills", ascending=False).head(10)
                   .reset_index(drop=True))
            top["label"]    = ["Player " + str(i+1) for i in range(len(top))]
            top["short_id"] = top["user_id_from_file"].str[:8] + "…" + top["user_id_from_file"].str[-4:]
            f4 = px.bar(top, x="kills", y="label", orientation="h", color="kills",
                       color_continuous_scale="Reds",
                       title="Top 10 Human Killers", height=320,
                       custom_data=["user_id_from_file","short_id"])
            # Hover shows full UUID so designer can cross-reference with Timeline tab
            f4.update_traces(
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Kills: %{x}<br>"
                    "User ID: %{customdata[1]}<br>"
                    "<span style='font-size:10px;color:#8b949e'>Full ID: %{customdata[0]}</span>"
                    "<extra></extra>"
                )
            )
            f4.update_layout(
                plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                font=dict(color="#c9d1d9"),
                xaxis=dict(gridcolor="#21262d", title="Kill Count"),
                yaxis=dict(gridcolor="#21262d", title="", autorange="reversed"),
                title_font=dict(color="#e6edf3"),
                coloraxis_showscale=False,
                margin=dict(l=10,r=10,t=40,b=10),
            )

            st.session_state["st_charts"]      = (f1, f2, f3, f4, top)
            st.session_state["st_charts_hash"] = charts_key
            st_status.update(label="✅ Charts ready", state="complete", expanded=False)
    else:
        f1, f2, f3, f4, top = st.session_state["st_charts"]

    # FIX 1,2,3,4,5: Compute insights once, cache in session state
    if st.session_state.get("st_insight") is None:
        game_df      = data[~data["event"].isin(MOVE_EVENTS)]
        total_kills  = int(len(data[data["event"].isin(["Kill","BotKill"])]))
        total_deaths = int(len(data[data["event"].isin(["Killed","BotKilled","KilledByStorm"])]))
        storm_deaths = int(len(data[data["event"] == "KilledByStorm"]))
        n_humans     = int(data[~data["is_bot"]]["user_id_from_file"].nunique())
        n_bots       = int(data[data["is_bot"]]["user_id_from_file"].nunique())
        n_matches    = int(data["match_id_clean"].nunique())
        top_event    = game_df["event"].value_counts().idxmax() if not game_df.empty else "N/A"
        event_verb   = {"Kill":"killing","Killed":"dying","BotKill":"killing bots",
                        "BotKilled":"being killed by bots","KilledByStorm":"storm deaths",
                        "Loot":"looting"}.get(top_event, top_event)
        kd_ratio     = round(total_kills / total_deaths, 2) if total_deaths > 0 else 0
        storm_pct    = round(storm_deaths / total_deaths * 100) if total_deaths > 0 else 0
        bot_ratio    = round(n_bots / n_humans, 1) if n_humans > 0 else 0
        human_kills  = int(len(data[data["event"]=="Kill"]))
        bot_kills    = int(len(data[data["event"]=="BotKill"]))
        balance      = ("balanced"
                        if abs(human_kills-bot_kills) < 0.3*max(human_kills,bot_kills,1)
                        else ("humans dominate" if human_kills > bot_kills else "bots dominate"))
        top3_str     = " · ".join([f"{e} ({c:,})"
                                   for e,c in game_df["event"].value_counts().head(3).items()])
        dc_vals      = data.groupby("date_str")["event"].count()
        st.session_state["st_insight"] = dict(
            total_kills=total_kills, n_humans=n_humans, n_bots=n_bots,
            n_matches=n_matches, event_verb=event_verb, kd_ratio=kd_ratio,
            storm_pct=storm_pct, bot_ratio=bot_ratio, human_kills=human_kills,
            bot_kills=bot_kills, balance=balance, top3_str=top3_str,
            max_day=dc_vals.idxmax(), min_day=dc_vals.idxmin(),
            has_feb14="Feb 14" in dc_vals.index,
        )

    ins = st.session_state["st_insight"]

    # ── Top-level summary callout ─────────────────────────────────────────────
    st.markdown(
        f'<div style="background:#0d1f2d;border:1px solid #1f6feb;border-radius:8px;'
        f'padding:14px 18px;margin-bottom:16px;font-size:0.82rem;color:#c9d1d9;">'
        f'<span style="font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:700;'
        f'color:#58a6ff;">📋 Quick Read</span><br>'
        f'Across <b>{ins["n_matches"]}</b> matches, <b>{ins["n_humans"]}</b> human players '
        f'faced <b>{ins["n_bots"]}</b> bots ({ins["bot_ratio"]}x bot ratio). '
        f'Players were most frequently <b>{ins["event_verb"]}</b>. '
        f'Kill/Death ratio is <b>{ins["kd_ratio"]}</b> and '
        f'<b>{ins["storm_pct"]}%</b> of all deaths were caused by the storm.'
        f'</div>',
        unsafe_allow_html=True,
    )

    if st_is_stale:
        st.markdown(
            '<div class="stale-map-hint">'
            '⚠️  These charts reflect previous filters. '
            'Scroll up and click Show Stats to update.'
            '</div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        '<div style="font-size:0.72rem;color:#444d56;margin-bottom:12px;'
        'font-family:Share Tech Mono,monospace;">'
        '🖱 All charts are interactive — hover for details, click legend to filter'
        '</div>',
        unsafe_allow_html=True,
    )

    r1, r2 = st.columns(2)
    with r1:
        # FIX 11: each chart has its own header inside its column
        st.markdown(
            '<div style="font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:700;'
            'color:#e6edf3;margin:8px 0 4px;">What game events are happening?</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:0.78rem;color:#8b949e;margin-bottom:8px;">'
            f'💡 Top 3: <span style="color:#58a6ff">{ins["top3_str"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(f1, use_container_width=True)

    with r2:
        st.markdown(
            '<div style="font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:700;'
            'color:#e6edf3;margin:8px 0 4px;">Is engagement consistent across days?</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:0.78rem;color:#8b949e;margin-bottom:8px;">'
            f'💡 Most active: <span style="color:#58a6ff">{ins["max_day"]}</span> · '
            f'Least active: <span style="color:#58a6ff">{ins["min_day"]}</span>'
            f'{"  · ⚠️ Feb 14 is a partial day" if ins["has_feb14"] else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(f2, use_container_width=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    r3, r4 = st.columns(2)
    with r3:
        st.markdown(
            '<div style="font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:700;'
            'color:#e6edf3;margin:8px 0 4px;">Are bots and humans balanced?</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:0.78rem;color:#8b949e;margin-bottom:8px;">'
            f'💡 Human kills: <span style="color:#58a6ff">{ins["human_kills"]:,}</span> · '
            f'Bot kills: <span style="color:#58a6ff">{ins["bot_kills"]:,}</span> · '
            f'Combat appears <span style="color:#58a6ff">{ins["balance"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(f3, use_container_width=True)

    with r4:
        st.markdown(
            '<div style="font-family:Rajdhani,sans-serif;font-size:1rem;font-weight:700;'
            'color:#e6edf3;margin:8px 0 4px;">Who are the most lethal players?</div>',
            unsafe_allow_html=True,
        )
        if not top.empty:
            top_kills = int(top["kills"].iloc[0])
            avg_kills = round(top["kills"].mean(), 1)
            st.markdown(
                f'<div style="font-size:0.78rem;color:#8b949e;margin-bottom:8px;">'
                f'💡 Top killer: <span style="color:#ff4444">{top_kills} kills</span> · '
                f'Average top 10: <span style="color:#58a6ff">{avg_kills} kills</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.plotly_chart(f4, use_container_width=True)

        # Player ID lookup table — so designer can find the UUID for each player
        if not top.empty:
            with st.expander("🔎 Player ID Lookup — click to see who Player 1, 2… are"):
                lookup = top[["label","short_id","user_id_from_file","kills"]].copy()
                lookup.columns = ["Label","Short ID","Full User ID","Kills"]
                st.dataframe(
                    lookup,
                    use_container_width=True,
                    hide_index=True,
                    height=min(38*len(lookup)+38, 420),
                )
                st.caption(
                    "Copy a Full User ID and paste it into the Timeline tab "
                    "Match dropdown to investigate that player's journey."
                )

    # ── Raw Data Explorer ─────────────────────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    with st.expander(f"🔍 Raw Data Explorer — {len(data):,} total rows"):
        col_opts = list(data.columns)
        selected_cols = st.multiselect(
            "Columns to show", col_opts,
            default=["match_id_clean","date_str","map_id","user_id_from_file",
                     "is_bot","event","pixel_x","pixel_y"],
            key="st_explorer_cols",
        )
        n_rows = st.slider("Rows to display", 50, min(2000, len(data)), 200,
                           step=50, key="st_explorer_rows")
        st.caption(f"Showing {n_rows:,} of {len(data):,} rows · Use column headers to sort")
        st.dataframe(
            data[selected_cols].head(n_rows),
            use_container_width=True, height=320,
        )

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    init_state()
    df = load_data()
    render_header()
    tab1,tab2,tab3,tab4 = st.tabs([
        "🗺️  MAP VIEW","🔥  HEATMAPS","⏱️  TIMELINE","📊  STATS",
    ])
    with tab1: render_map_view(df)
    with tab2: render_heatmap(df)
    with tab3: render_timeline(df)
    with tab4: render_stats(df)

if __name__ == "__main__":
    main()