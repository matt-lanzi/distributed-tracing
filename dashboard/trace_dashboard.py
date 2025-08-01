import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# Connect to the SQLite DB
DB_PATH = "db/event_history.db"
conn = sqlite3.connect(DB_PATH)

# Load trace summary
trace_summary = pd.read_sql_query("SELECT * FROM trace_summary ORDER BY trace_start DESC", conn)

# Sidebar - Choose correlation ID
st.sidebar.title("Trace Navigator")
selected_trace = st.sidebar.selectbox(
    "Select Correlation ID:", trace_summary["correlation_id"].unique()
)

# Load spans for selected trace
spans = pd.read_sql_query(
    f"""
    SELECT * FROM spans
    WHERE correlation_id = ?
    ORDER BY 
      CASE system_id
        WHEN 'inventory' THEN 1
        WHEN 'payments' THEN 2
        WHEN 'orders' THEN 3
        WHEN 'reporting' THEN 4
        ELSE 5
      END
    """,
    conn,
    params=(selected_trace,)
)

# Display trace summary
st.title("Trace Dashboard")
st.subheader(f"Trace: {selected_trace}")

selected_summary = trace_summary[trace_summary["correlation_id"] == selected_trace].iloc[0]
st.markdown(f"**Trace Status:** {selected_summary['trace_status']}")
st.markdown(f"**Start:** {selected_summary['trace_start']}")
st.markdown(f"**End:** {selected_summary['trace_end']}")
st.markdown(f"**Duration:** {selected_summary['trace_duration_sec']} seconds")

# Plot Gantt chart
spans["start_time"] = pd.to_datetime(spans["start_time"])
spans["end_time"] = pd.to_datetime(spans["end_time"])

fig = px.timeline(
    spans,
    x_start="start_time",
    x_end="end_time",
    y="system_id",
    color="status",
    hover_data=["duration_sec"]
)
fig.update_yaxes(autorange="reversed")
fig.update_layout(title="System Span Timeline", xaxis_title="Time", yaxis_title="System")

st.plotly_chart(fig, use_container_width=True)

# Show raw span data
with st.expander("Show raw spans"):
    st.dataframe(spans)

# Show trace summary table (optional)
with st.expander("Show trace summary"):
    st.dataframe(trace_summary)

conn.close()
