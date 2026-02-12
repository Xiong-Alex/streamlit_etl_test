from pathlib import Path
import csv
import requests
import pandas as pd
import streamlit as st
from datetime import datetime


st.title("NOAA Station Downloader")

# -------------------------
# Configuration
# -------------------------
BASE_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily"
OUT_DIR = Path("/data/landing/stations")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------
# Directory Viewer
# -------------------------
def render_directory_view(title: str, directory: Path):

    st.markdown(f"## {title}")

    if not directory.exists():
        st.warning(f"Directory does not exist: {directory}")
        return

    files = list(directory.glob("*"))

    if not files:
        st.info("No files found.")
        return

    file_data = []

    for f in files:
        stat = f.stat()
        file_data.append({
            "File Name": f.name,
            "Size (KB)": round(stat.st_size / 1024, 2),
            "Last Modified": datetime.fromtimestamp(stat.st_mtime),
        })

    df = pd.DataFrame(file_data).sort_values("Last Modified", ascending=False)

    col1, col2 = st.columns(2)
    col1.metric("File Count", len(df))
    col2.metric("Total Size (MB)", round(df["Size (KB)"].sum() / 1024, 2))

    st.dataframe(df, use_container_width=True)

    if st.button(f"Refresh {title}"):
        st.rerun()


# -------------------------
# Download + Parse Function
# -------------------------
def download_station_to_csv() -> Path:
    txt_path = OUT_DIR / "ghcnd-stations.txt"
    csv_path = OUT_DIR / "ghcnd-stations.csv"

    # Download
    if not txt_path.exists():
        with st.spinner("Downloading station file..."):
            r = requests.get(f"{BASE_URL}/ghcnd-stations.txt", timeout=60)
            r.raise_for_status()
            txt_path.write_bytes(r.content)
        st.success("Downloaded ghcnd-stations.txt")
    else:
        st.info("Station file already exists. Skipping download.")

    # Parse → CSV
    with st.spinner("Parsing file into CSV..."):
        with open(txt_path, "r", encoding="utf-8") as fin, open(
            csv_path, "w", newline="", encoding="utf-8"
        ) as fout:
            writer = csv.writer(fout)

            writer.writerow([
                "station_id",
                "latitude",
                "longitude",
                "elevation",
                "state",
                "name",
                "gsn",
                "hcn",
                "wmo",
            ])

            for line in fin:
                station_id = line[0:11].strip()
                if not station_id:
                    continue

                def val(s):
                    s = s.strip()
                    return s if s else None

                writer.writerow([
                    station_id,
                    val(line[12:20]),
                    val(line[21:30]),
                    val(line[31:37]),
                    val(line[38:40]),
                    val(line[41:71]),
                    val(line[72:75]),
                    val(line[76:79]),
                    val(line[80:85]),
                ])

    txt_path.unlink()
    st.success("CSV created successfully!")

    return csv_path


# -------------------------
# Landing Directory View
# -------------------------
render_directory_view("Landing Directory", OUT_DIR)

st.divider()

# -------------------------
# UI
# -------------------------
if st.button("Download & Process Station File", use_container_width=True):

    csv_file = download_station_to_csv()

    df = pd.read_csv(csv_file)

    st.subheader("Preview")
    st.dataframe(df.head(), use_container_width=True)

    st.success(f"Saved to: {csv_file}")

    st.rerun()
