# generate_insights.py
# One-time analysis script used to extract player behaviour statistics
# from data/all_events.parquet for the INSIGHTS.md report.
# Run with: python generate_insights.py
# Output: printed to terminal — numbers were manually transferred to INSIGHTS.md
import pandas as pd
import numpy as np

df = pd.read_parquet("data/all_events.parquet")
df["ts"] = pd.to_numeric(df["ts"], errors="coerce")
df["date"] = pd.to_datetime(df["date"])
df["date_str"] = df["date"].dt.strftime("%b %d")

MOVE_EVENTS = ["Position", "BotPosition"]
game = df[~df["event"].isin(MOVE_EVENTS)]

print("=" * 60)
print("LILA BLACK — DATA INSIGHTS REPORT")
print("=" * 60)

print(f"\nTotal records:    {len(df):,}")
print(f"Game events:      {len(game):,}")
print(f"Unique matches:   {df['match_id_clean'].nunique()}")
print(f"Human players:    {df[~df['is_bot']]['user_id_from_file'].nunique()}")
print(f"Bots:             {df[df['is_bot']]['user_id_from_file'].nunique()}")

print("\n--- EVENT DISTRIBUTION (all maps) ---")
print(game["event"].value_counts().to_string())

print("\n--- PER MAP STATS ---")
for map_id in df["map_id"].unique():
    m = game[game["map_id"] == map_id]
    kills       = len(m[m["event"].isin(["Kill","BotKill"])])
    deaths      = len(m[m["event"].isin(["Killed","BotKilled","KilledByStorm"])])
    storm       = len(m[m["event"] == "KilledByStorm"])
    loot        = len(m[m["event"] == "Loot"])
    h_kills     = len(m[m["event"] == "Kill"])
    b_kills     = len(m[m["event"] == "BotKill"])
    matches     = m["match_id_clean"].nunique()
    storm_pct   = round(storm/deaths*100, 1) if deaths else 0
    kd          = round(kills/deaths, 2) if deaths else 0
    print(f"\n  {map_id}")
    print(f"    Matches:      {matches}")
    print(f"    KD Ratio:     {kd}")
    print(f"    Storm Deaths: {storm_pct}% of all deaths")
    print(f"    Human Kills:  {h_kills:,} | Bot Kills: {b_kills:,}")
    print(f"    Loot Pickups: {loot:,}")

print("\n--- KILL HEATMAP HOTSPOT (top 5% pixel zones) ---")
for map_id in df["map_id"].unique():
    kills = df[(df["map_id"]==map_id) & (df["event"].isin(["Kill","BotKill"]))]
    if kills.empty: continue
    kills = kills.copy()
    kills["zone_x"] = (kills["pixel_x"] // 200).astype(int)
    kills["zone_y"] = (kills["pixel_y"] // 200).astype(int)
    top = kills.groupby(["zone_x","zone_y"]).size().sort_values(ascending=False).head(3)
    total = len(kills)
    print(f"\n  {map_id} — top kill zones (out of {total} kills):")
    for (zx,zy), count in top.items():
        pct = round(count/total*100,1)
        print(f"    Zone ({zx*200}-{zx*200+200}px, {zy*200}-{zy*200+200}px): {count} kills ({pct}%)")

print("\n--- MATCH DURATION (per map) ---")
for map_id in df["map_id"].unique():
    m = df[df["map_id"]==map_id]
    durations = (m.groupby(["match_id_clean","user_id_from_file"])["ts"]
                  .agg(lambda x: float(x.max()) - float(x.min()))
                  .groupby(level=0).max())
    print(f"\n  {map_id}")
    print(f"    Median duration: {durations.median():.0f}s")
    print(f"    Min duration:    {durations.min():.0f}s")
    print(f"    Max duration:    {durations.max():.0f}s")

print("\n--- EVENTS PER DAY ---")
print(game.groupby("date_str")["event"].count().to_string())

print("\n--- BOT RATIO PER MAP ---")
for map_id in df["map_id"].unique():
    m = df[df["map_id"]==map_id]
    humans = m[~m["is_bot"]]["user_id_from_file"].nunique()
    bots   = m[m["is_bot"]]["user_id_from_file"].nunique()
    print(f"  {map_id}: {humans} humans, {bots} bots ({round(bots/humans,1)}x ratio)")

print("\n--- TOP 5 HUMAN KILLERS (all maps) ---")
kdf = game[(game["event"].isin(["Kill","BotKill"])) & (~game["is_bot"])]
top = kdf.groupby("user_id_from_file")["event"].count().sort_values(ascending=False).head(5)
for uid, count in top.items():
    print(f"  {uid[:12]}... : {count} kills")

print("\nDone. Copy these numbers into INSIGHTS.md")