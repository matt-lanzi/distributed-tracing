import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# Connect to DB
DB_PATH = "db/event_history.db"
conn = sqlite3.connect(DB_PATH)

# Load events
events = pd.read_sql_query("SELECT * FROM events", conn)
events["timestamp"] = pd.to_datetime(events["timestamp"])

# Sidebar filters
st.sidebar.title("Event Filters")
selected_status = st.sidebar.multiselect(
    "Select Status:", events["status"].unique(), default=events["status"].unique()
)
selected_systems = st.sidebar.multiselect(
    "Select Systems:", events["system_id"].unique(), default=events["system_id"].unique()
)

# Apply filters
filtered_events = events[
    events["status"].isin(selected_status) &
    events["system_id"].isin(selected_systems)
].copy()

# System ordering to reduce overlap
system_order = {
    "fedebom": 1,
    "cmf": 2,
    "bcis": 3,
    "reporting": 4
}
filtered_events["system_order"] = filtered_events["system_id"].map(system_order).fillna(99).astype(int)

# Compose y-axis label: correlation_id + system
filtered_events["correlation_system"] = filtered_events["correlation_id"] + " - " + filtered_events["system_id"]

# Sort for display: correlation_id and then system order
filtered_events = filtered_events.sort_values(by=["correlation_id", "system_order", "timestamp"])

# Create color map: SUCCESS -> green, FAILURE -> red
status_color_map = {
    "SUCCESS": "green",
    "FAILURE": "red"
}
filtered_events["status_color"] = filtered_events["status"].map(status_color_map)

# Title and Overview
st.title("System Events Overview")
st.markdown("Each row shows the sequence of all events for a single correlation ID grouped by system.")
st.markdown(f"**Total Events:** {len(filtered_events)}")

# Use scatter plot: color by status, shape by system
fig = px.scatter(
    filtered_events,
    x="timestamp",
    y="correlation_system",
    color="status",
    color_discrete_map=status_color_map,
    symbol="system_id",
    hover_data=["system_id", "checkpoint_id", "failure_reason"],
    title="Events by Correlation ID and System"
)
fig.update_yaxes(categoryorder="array", categoryarray=filtered_events["correlation_system"].unique()[::-1], tickfont=dict(size=9), title="Correlation ID + System")
fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))

st.plotly_chart(fig, use_container_width=True)

# Expandable raw table
with st.expander("Show Event Table"):
    st.dataframe(filtered_events)

conn.close()