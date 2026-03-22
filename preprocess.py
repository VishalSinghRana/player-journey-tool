"""
preprocess.py  (v2 — fixed human filename parsing)
Run this ONCE before starting the Streamlit app.

Usage:
    python preprocess.py
"""

import os
import re
import pandas as pd
import pyarrow.parquet as pq
import numpy as np

BASE_DIR    = "player_data"
OUTPUT_DIR  = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "all_events.parquet")

DAY_FOLDERS = [
    ("February_10", "2026-02-10", False),
    ("February_11", "2026-02-11", False),
    ("February_12", "2026-02-12", False),
    ("February_13", "2026-02-13", False),
    ("February_14", "2026-02-14", True),
]

MAP_CONFIG = {
    "AmbroseValley": {"scale": 900,  "origin_x": -370, "origin_z": -473},
    "GrandRift":     {"scale": 581,  "origin_x": -290, "origin_z": -290},
    "Lockdown":      {"scale": 1000, "origin_x": -500, "origin_z": -500},
}

UUID_RE = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def world_to_pixel(x, z, map_id):
    cfg = MAP_CONFIG.get(map_id)
    if cfg is None:
        return np.full_like(x, np.nan, dtype=float), np.full_like(z, np.nan, dtype=float)
    u = (x - cfg["origin_x"]) / cfg["scale"]
    v = (z - cfg["origin_z"]) / cfg["scale"]
    return (u * 1024).astype("float32"), ((1 - v) * 1024).astype("float32")


def parse_filename(filename):
    """
    HUMAN:  {uuid}_{uuid}.nakama-0   -> (uuid1, uuid2, False)
    BOT:    {number}_{uuid}.nakama-0 -> (number, uuid, True)
    Returns (user_id, match_id, is_bot) or (None, None, None)
    """
    name = filename.replace(".nakama-0", "")
    uuids = re.findall(UUID_RE, name)

    if len(uuids) == 2:
        return uuids[0], uuids[1], False

    if len(uuids) == 1:
        match_id = uuids[0]
        split_pos = name.find("_" + match_id)
        if split_pos == -1:
            return None, None, None
        user_id = name[:split_pos]
        if re.match(r"^\d+$", user_id):
            return user_id, match_id, True
        return None, None, None

    return None, None, None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_frames = []
    total_files = human_files = bot_files = skipped = 0

    for folder_name, date_str, is_partial in DAY_FOLDERS:
        folder_path = os.path.join(BASE_DIR, folder_name)
        if not os.path.exists(folder_path):
            print(f"  WARNING: Folder not found: {folder_path}")
            continue

        files = os.listdir(folder_path)
        print(f"\n{folder_name} ({date_str}{'  <- partial' if is_partial else ''}) — {len(files)} files")

        for filename in files:
            filepath = os.path.join(folder_path, filename)
            if os.path.isdir(filepath):
                continue

            user_id, match_id, is_bot = parse_filename(filename)
            if user_id is None:
                print(f"  Could not parse: {filename}")
                skipped += 1
                continue

            try:
                df = pq.read_table(filepath).to_pandas()
            except Exception as e:
                print(f"  Could not read {filename}: {e}")
                skipped += 1
                continue

            if df.empty:
                skipped += 1
                continue

            # Decode event bytes
            df["event"] = df["event"].apply(
                lambda x: x.decode("utf-8") if isinstance(x, bytes) else str(x)
            )

            # Add metadata
            df["user_id_from_file"] = user_id
            df["match_id_clean"]    = match_id
            df["is_bot"]            = is_bot
            df["date"]              = date_str
            df["is_partial_day"]    = is_partial

            # Coordinate transform
            map_id = df["map_id"].iloc[0] if "map_id" in df.columns else ""
            df["pixel_x"], df["pixel_y"] = world_to_pixel(
                df["x"].values, df["z"].values, map_id
            )

            all_frames.append(df)
            total_files += 1
            if is_bot:
                bot_files += 1
            else:
                human_files += 1

            if total_files % 100 == 0:
                print(f"  Processed {total_files} files... (humans={human_files}, bots={bot_files})")

    print(f"\nCombining {total_files} files...")
    combined = pd.concat(all_frames, ignore_index=True)

    # Strip .nakama-0 from match_id in data column
    if "match_id" in combined.columns:
        combined["match_id"] = combined["match_id"].str.replace(r"\.nakama-0$", "", regex=True)

    combined["x"]       = combined["x"].astype("float32")
    combined["z"]       = combined["z"].astype("float32")
    combined["pixel_x"] = combined["pixel_x"].astype("float32")
    combined["pixel_y"] = combined["pixel_y"].astype("float32")
    combined["date"]    = pd.to_datetime(combined["date"])

    print(f"\nFinal dataset shape: {combined.shape}")
    print(f"   Rows        : {len(combined):,}")
    print(f"   Maps        : {list(combined['map_id'].unique())}")
    print(f"   Event types : {list(combined['event'].unique())}")
    print(f"   Humans      : {combined[~combined['is_bot']]['user_id_from_file'].nunique()} unique players")
    print(f"   Bots        : {combined[combined['is_bot']]['user_id_from_file'].nunique()} unique bots")
    print(f"   Matches     : {combined['match_id_clean'].nunique()} unique matches")
    print(f"   Files read  : {total_files}  (human={human_files}, bot={bot_files})")
    print(f"   Skipped     : {skipped} files")

    combined.to_parquet(OUTPUT_FILE, index=False)
    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"\nSaved to {OUTPUT_FILE}  ({size_mb:.1f} MB)")
    print("You can now run:  streamlit run app.py")


if __name__ == "__main__":
    main()