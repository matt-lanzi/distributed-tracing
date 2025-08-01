import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import numpy as np

# Connect to DB
DB_PATH = "db/event_history.db"
conn = sqlite3.connect(DB_PATH)

# Load spans
spans = pd.read_sql_query("SELECT * FROM spans", conn)
spans["start_time"] = pd.to_datetime(spans["start_time"])
spans["end_time"] = pd.to_datetime(spans["end_time"])

# Sidebar filters
st.sidebar.title("Span Filters")
selected_status = st.sidebar.multiselect(
    "Select Status:", spans["status"].unique(), default=spans["status"].unique()
)
selected_systems = st.sidebar.multiselect(
    "Select Systems:", spans["system_id"].unique(), default=spans["system_id"].unique()
)

# Apply filters
filtered_spans = spans[
    spans["status"].isin(selected_status) &
    spans["system_id"].isin(selected_systems)
].copy()

# Calculate duration for sort order
filtered_spans["duration"] = (filtered_spans["end_time"] - filtered_spans["start_time"]).dt.total_seconds()

# Adjust draw order: sort by duration descending
filtered_spans = filtered_spans.sort_values(by=["correlation_id", "start_time", "duration"], ascending=[True, True, False])

# Custom color map for improved contrast between reporting and order
color_discrete_map = {
    "inventory": "#1f77b4",
    "payments": "#ff7f0e",
    "orders": "#2ca02c",        # green
    "reporting": "#d62728"     # red
}

# Title and Overview
st.title("System Spans Overview")
st.markdown("Use the filters on the left to explore system span activity. Each row represents a full trace timeline across systems.")
st.markdown(f"**Total Spans:** {len(filtered_spans)}")

# Gantt chart with y-axis as correlation ID only (1 row per trace)
fig = px.timeline(
    filtered_spans,
    x_start="start_time",
    x_end="end_time",
    y="correlation_id",
    color="system_id",
    color_discrete_map=color_discrete_map,
    hover_data=["system_id", "status", "duration_sec"],
    title="Spans by Correlation ID"
)
fig.update_yaxes(autorange="reversed", tickfont=dict(size=10), title="Correlation ID")
fig.update_traces(opacity=0.5)
fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))

st.plotly_chart(fig, use_container_width=True)

# Expandable raw table
with st.expander("Show Span Table"):
    st.dataframe(filtered_spans.sort_values(by=["correlation_id", "start_time"]))

conn.close()
