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
        "st_show":False, "st_data":None,
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
        date     = grp["date_str"].iloc[0]
        summaries[mid] = f"{mid[:8]}… | {date} | {n_humans}P {n_bots}B"
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

def build_map_fig(df_in, map_id, show_paths=True, show_events=True, active_events=None):
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
            for is_bot_flag, label, color in [
                (False, "Human Paths", "rgba(88,166,255,0.3)"),
                (True,  "Bot Paths",   "rgba(139,148,158,0.2)"),
            ]:
                subset = pos[pos["is_bot"] == is_bot_flag]
                if subset.empty:
                    continue
                xs, ys = [], []
                for _, grp in subset.groupby(
                    ["user_id_from_file","match_id_clean"], sort=False
                ):
                    xs.extend(grp["pixel_x"].tolist() + [None])
                    ys.extend(grp["pixel_y"].tolist() + [None])
                fig.add_trace(go.Scattergl(
                    x=xs, y=ys, mode="lines", name=label,
                    line=dict(color=color, width=1),
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
    st.markdown("#### ⏱️ Timeline Filters")
    c1,c2,c3 = st.columns([1,2,1])
    with c1:
        tl_map = st.selectbox("Map (required)", MAPS, index=None,
                              placeholder="Select a map…", key="tl_map_sel")
    with c2:
        matches = get_map_matches(df, tl_map) if tl_map else []
        tl_match = st.selectbox(
            "Match (required)", matches, index=None,
            placeholder="Choose a match…" if matches else "Select map first",
            format_func=match_label,
            key="tl_match_sel", disabled=not tl_map,
        )
    with c3:
        tl_players = st.radio("Players", ["All","Humans","Bots"], key="tl_players_sel")

    show_clicked = st.button("▶  Load Match", key="tl_show_btn", type="primary")
    if show_clicked:
        if not tl_map:
            st.error("⬆️  Please select a Map.")
        elif not tl_match:
            st.error("⬆️  Please select a Match.")
        else:
            with st.spinner("Loading match data…"):
                mdf = run_match_query(df, tl_match).copy()
                if tl_players == "Humans":
                    mdf = mdf[~mdf["is_bot"]]
                elif tl_players == "Bots":
                    mdf = mdf[mdf["is_bot"]]
                if not mdf.empty:
                    mdf["ts"]        = pd.to_datetime(mdf["ts"])
                    t_min            = mdf["ts"].min()
                    t_max            = mdf["ts"].max()
                    mdf["elapsed_s"] = (mdf["ts"] - t_min).dt.total_seconds()
                    total_s          = max(float((t_max-t_min).total_seconds()), 1.0)
                else:
                    total_s = 1.0
            st.session_state["tl_data"]       = mdf
            st.session_state["tl_map_used"]   = tl_map
            st.session_state["tl_match_used"] = tl_match
            st.session_state["tl_total_s"]    = total_s
            st.session_state["tl_show"]       = True

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    if not st.session_state["tl_show"]:
        st.markdown("""
        <div class="empty-state">
          <div style="font-size:3rem;margin-bottom:12px;">⏱️</div>
          <div class="title">No match loaded yet</div>
          <div class="hint">Select a map and a specific match, then click Load Match</div>
          <div class="hint">You can then scrub through the match second by second</div>
        </div>
        """, unsafe_allow_html=True)
        return

    mdf     = st.session_state["tl_data"]
    map_u   = st.session_state["tl_map_used"]
    match_u = st.session_state["tl_match_used"]
    total_s = st.session_state["tl_total_s"]

    if mdf is None or mdf.empty:
        st.warning("No data for this match / player filter.")
        return

    n_h = int(mdf[~mdf["is_bot"]]["user_id_from_file"].nunique())
    n_b = int(mdf[mdf["is_bot"]]["user_id_from_file"].nunique())
    st.markdown(
        f'<div class="info-bar">'
        f'⏱ Duration: <span style="color:#58a6ff">{total_s:.0f}s</span>'
        f' &nbsp;·&nbsp; 👤 <span style="color:#58a6ff">{n_h}</span> humans'
        f' &nbsp;·&nbsp; 🤖 <span style="color:#58a6ff">{n_b}</span> bots'
        f' &nbsp;·&nbsp; 📋 <span style="color:#58a6ff">{len(mdf):,}</span> events'
        f'</div>',
        unsafe_allow_html=True,
    )

    playback_s = st.slider(
        "Scrub through match (seconds)",
        min_value=0.0, max_value=total_s, value=0.0,
        step=max(1.0, round(total_s/120,1)),
        key=f"tl_slider_{match_u}",
        help="Drag to replay the match. The map below updates to show events up to this point.",
    )

    up_to = mdf[mdf["elapsed_s"] <= playback_s]
    st.markdown(
        f'<div style="font-size:0.72rem;color:#444d56;margin-bottom:4px;'
        f'font-family:Share Tech Mono,monospace;">'
        f'🖱 Scroll to zoom · Click and drag to pan</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        build_map_fig(up_to, map_u, show_paths=True, show_events=True),
        use_container_width=True,
        config={"scrollZoom":True,"displayModeBar":True,
                "modeBarButtonsToRemove":["select2d","lasso2d"]},
    )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    combat = mdf[~mdf["event"].isin(MOVE_EVENTS)].copy()
    st.markdown("**👥 Player Activity**")
    if combat.empty:
        st.info("No combat or loot events in this match.")
    else:
        combat["player_label"] = (
            combat["is_bot"].map({True:"🤖 ",False:"👤 "})
            + combat["user_id_from_file"].str[:8]
        )
        gantt = go.Figure()
        for evt, grp in combat.groupby("event"):
            gantt.add_trace(go.Scatter(
                x=grp["elapsed_s"], y=grp["player_label"],
                mode="markers", name=evt,
                marker=dict(color=EVENT_COLORS.get(evt,"#fff"),
                            symbol=EVENT_SYMBOLS.get(evt,"circle"),
                            size=10,line=dict(color="#0a0c10",width=1)),
                hovertemplate=f"<b>{evt}</b><br>T+%{{x:.1f}}s<br>%{{y}}<extra></extra>",
            ))
        gantt.add_vline(x=playback_s, line_width=2, line_dash="dash",
                        line_color="#ff4444",
                        annotation_text=f"▶ {playback_s:.0f}s",
                        annotation_font_color="#ff4444",annotation_font_size=11,
                        annotation_position="top right")
        n_rows = combat["player_label"].nunique()
        gantt.update_layout(
            plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9",size=11),
            legend=dict(bgcolor="#161b22",bordercolor="#21262d",borderwidth=1,
                        orientation="h",yanchor="bottom",y=1.02,x=0),
            xaxis=dict(title="Elapsed (seconds)",gridcolor="#21262d",
                       range=[0,total_s],zeroline=False,tickfont=dict(color="#8b949e")),
            yaxis=dict(gridcolor="#21262d",autorange="reversed",
                       zeroline=False,tickfont=dict(color="#c9d1d9",size=10)),
            height=max(320, n_rows*30+100),
            margin=dict(l=10,r=20,t=50,b=50),
        )
        st.plotly_chart(gantt, use_container_width=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("**📊 Event Density**")
    if not combat.empty:
        hfig = px.histogram(
            combat, x="elapsed_s", color="event",
            nbins=max(20,int(total_s//15)),
            color_discrete_map=EVENT_COLORS, barmode="stack", height=250,
            labels={"elapsed_s":"Elapsed (seconds)","count":"Events"},
        )
        hfig.add_vline(x=playback_s,line_width=2,line_dash="dash",
                       line_color="#ff4444",
                       annotation_text=f"T={playback_s:.0f}s",
                       annotation_font_color="#ff4444",annotation_font_size=10)
        hfig.update_layout(
            plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",font=dict(color="#c9d1d9"),
            legend=dict(bgcolor="#161b22",bordercolor="#21262d",borderwidth=1,
                        orientation="h",yanchor="bottom",y=1.02),
            xaxis=dict(gridcolor="#21262d",range=[0,total_s],zeroline=False),
            yaxis=dict(gridcolor="#21262d",title="Event count",zeroline=False),
            margin=dict(l=10,r=10,t=40,b=40),
        )
        st.plotly_chart(hfig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — STATS
# ─────────────────────────────────────────────────────────────────────────────
def render_stats(df):
    st.markdown("#### 📊 Stats Filters")
    c1,c2 = st.columns(2)
    with c1:
        st_map = st.selectbox("Map", ["All Maps"]+MAPS, key="st_map_sel")
    with c2:
        dates_list = get_dates_list(df)
        st_dates_sel = st.multiselect(
            "Date(s)", dates_list,
            placeholder="All dates shown — pick to filter",
            key="st_dates_sel",
        )
        st_dates = st_dates_sel if st_dates_sel else None

    show_clicked = st.button("▶  Show Stats", key="st_show_btn", type="primary")
    if show_clicked:
        with st.spinner("Computing stats…"):
            data = df.copy()
            if st_map != "All Maps":
                data = data[data["map_id"]==st_map]
            if st_dates:
                data = data[data["date_str"].isin(st_dates)]
        st.session_state["st_data"] = data
        st.session_state["st_show"] = True

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    if not st.session_state["st_show"]:
        st.markdown("""
        <div class="empty-state">
          <div style="font-size:3rem;margin-bottom:12px;">📊</div>
          <div class="title">No stats loaded yet</div>
          <div class="hint">Select filters above and click Show Stats</div>
        </div>
        """, unsafe_allow_html=True)
        return

    data = st.session_state["st_data"]
    if data is None or data.empty:
        st.warning("No data.")
        return

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Total Events",  f"{len(data):,}")
    m2.metric("Human Players", int(data[~data["is_bot"]]["user_id_from_file"].nunique()))
    m3.metric("Matches",       int(data["match_id_clean"].nunique()))
    m4.metric("Kills",         int(len(data[data["event"].isin(["Kill","BotKill"])])))
    st.markdown("<br>",unsafe_allow_html=True)

    r1,r2 = st.columns(2)
    with r1:
        ec = data["event"].value_counts().reset_index()
        ec.columns = ["event","count"]
        f = px.bar(ec,x="count",y="event",orientation="h",color="event",
                   color_discrete_map=EVENT_COLORS,title="Event Distribution",height=320)
        f.update_layout(plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",
                        font=dict(color="#c9d1d9"),showlegend=False,
                        xaxis=dict(gridcolor="#21262d"),yaxis=dict(gridcolor="#21262d"),
                        title_font=dict(color="#e6edf3"))
        st.plotly_chart(f,use_container_width=True)
    with r2:
        dc = data.groupby("date_str")["event"].count().reset_index()
        dc.columns = ["date","events"]
        f2 = px.bar(dc,x="date",y="events",title="Events per Day",
                    color_discrete_sequence=["#58a6ff"],height=320)
        f2.update_layout(plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",
                         font=dict(color="#c9d1d9"),
                         xaxis=dict(gridcolor="#21262d"),yaxis=dict(gridcolor="#21262d"),
                         title_font=dict(color="#e6edf3"))
        st.plotly_chart(f2,use_container_width=True)

    r3,r4 = st.columns(2)
    with r3:
        hb = data.copy()
        hb["type"] = hb["is_bot"].map({True:"Bot",False:"Human"})
        hbc = hb.groupby(["type","event"])["event"].count().reset_index(name="count")
        f3 = px.bar(hbc,x="event",y="count",color="type",barmode="group",
                    color_discrete_map={"Human":"#58a6ff","Bot":"#8b949e"},
                    title="Human vs Bot Events",height=320)
        f3.update_layout(plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",
                         font=dict(color="#c9d1d9"),
                         xaxis=dict(gridcolor="#21262d",tickangle=30),
                         yaxis=dict(gridcolor="#21262d"),
                         title_font=dict(color="#e6edf3"),
                         legend=dict(bgcolor="#161b22"))
        st.plotly_chart(f3,use_container_width=True)
    with r4:
        kdf = data[data["event"].isin(["Kill","BotKill"]) & ~data["is_bot"]]
        top = (kdf.groupby("user_id_from_file")["event"]
               .count().reset_index(name="kills")
               .sort_values("kills",ascending=False).head(10))
        top["id"] = top["user_id_from_file"].str[:8]+"…"
        f4 = px.bar(top,x="kills",y="id",orientation="h",color="kills",
                    color_continuous_scale="Reds",title="Top 10 Killers",height=320)
        f4.update_layout(plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",
                         font=dict(color="#c9d1d9"),
                         xaxis=dict(gridcolor="#21262d"),yaxis=dict(gridcolor="#21262d"),
                         title_font=dict(color="#e6edf3"),coloraxis_showscale=False)
        st.plotly_chart(f4,use_container_width=True)

    with st.expander("🔍 Raw Data Explorer"):
        st.dataframe(data.head(500),use_container_width=True,height=300)

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