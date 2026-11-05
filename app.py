
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="6G Smart Factory Dashboard",
    page_icon="🏭",
    layout="wide"
)

st.title("6G Network Performance & Manufacturing Efficiency")
st.write("Smart Factory Network Analytics Dashboard")

file_path = r"C:\Users\Nishant\OneDrive\Documents\IndusSync\Data\Thales_Group_Manufacturing.csv"

@st.cache_data
def load_data():
    data = pd.read_csv(file_path)
    return data

df = load_data()

if "Timestamp" in df.columns:
    df["Timestamp"] = pd.to_datetime(
        df["Timestamp"], errors="coerce"
    )
elif "Date" in df.columns:
    df["Timestamp"] = pd.to_datetime(
        df["Date"],
        format="%d-%m-%Y",
        errors="coerce"
    )

df["Date_Filter"] = df["Timestamp"].dt.date

latency_normalized = (
    (df["Network_Latency_ms"] - df["Network_Latency_ms"].min()) /
    (df["Network_Latency_ms"].max() - df["Network_Latency_ms"].min())
)

packet_normalized = (
    (df["Packet_Loss_%"] - df["Packet_Loss_%"].min()) /
    (df["Packet_Loss_%"].max() - df["Packet_Loss_%"].min())
)

df["Network_Degradation_Score"] = (
    latency_normalized + packet_normalized
) / 2

df["Network_Quality"] = pd.qcut(
    df["Network_Degradation_Score"],
    q=3,
    labels=["High", "Medium", "Low"]
)

st.sidebar.header("Dashboard Filters")

network_filter = st.sidebar.selectbox(
    "Network Quality",
    ["All", "High", "Medium", "Low"]
)

efficiency_filter = st.sidebar.selectbox(
    "Efficiency Status",
    ["All"] + sorted(df["Efficiency_Status"].dropna().unique().tolist())
)

operation_filter = st.sidebar.selectbox(
    "Operation Mode",
    ["All"] + sorted(df["Operation_Mode"].dropna().unique().tolist())
)

if df["Date_Filter"].notna().any():

    min_date = df["Date_Filter"].min()
    max_date = df["Date_Filter"].max()

    date_range = st.sidebar.date_input(
        "Time Window",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = min_date
        end_date = max_date

    filtered_df = df[
        (df["Date_Filter"] >= start_date) &
        (df["Date_Filter"] <= end_date)
    ].copy()

else:
    filtered_df = df.copy()

if network_filter != "All":
    filtered_df = filtered_df[
        filtered_df["Network_Quality"] == network_filter
    ]

if efficiency_filter != "All":
    filtered_df = filtered_df[
        filtered_df["Efficiency_Status"] == efficiency_filter
    ]

if operation_filter != "All":
    filtered_df = filtered_df[
        filtered_df["Operation_Mode"] == operation_filter
    ]

if filtered_df.empty:
    st.warning("No records found for the selected filters.")
    st.stop()

st.write("Records available:", len(filtered_df))

network_stability = (
    1 - df["Network_Degradation_Score"].mean()
) * 100

latency_sensitivity = (
    df["Network_Latency_ms"].cov(
        df["Production_Speed_units_per_hr"]
    ) / df["Network_Latency_ms"].var()
)

df["Packet_Loss_Level"] = pd.qcut(
    df["Packet_Loss_%"],
    q=3,
    labels=["Low", "Medium", "High"]
)

packet_speed = df.groupby(
    "Packet_Loss_Level",
    observed=True
)["Production_Speed_units_per_hr"].mean()

packet_impact = (
    (packet_speed["Low"] - packet_speed["High"]) /
    packet_speed["Low"]
) * 100

network_correlation = df[
    "Network_Degradation_Score"
].corr(df["Production_Speed_units_per_hr"])

st.subheader("Network Performance KPIs")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Network Stability Index",
    f"{network_stability:.2f}%"
)

col2.metric(
    "Latency Sensitivity",
    f"{latency_sensitivity:.4f}"
)

col3.metric(
    "Packet Loss Impact",
    f"{packet_impact:.2f}%"
)

col4.metric(
    "Network-Efficiency Correlation",
    f"{network_correlation:.4f}"
)

tab1, tab2, tab3, tab4 = st.tabs([
    "Network Overview",
    "Network vs Efficiency",
    "Quality & Error Impact",
    "6G Optimization Insights"
])

with tab1:

    st.subheader("Network Performance Overview")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.histogram(
            filtered_df,
            x="Network_Latency_ms",
            nbins=30,
            title="Network Latency Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.histogram(
            filtered_df,
            x="Packet_Loss_%",
            nbins=30,
            title="Packet Loss Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Network Performance Trends")

    daily_network = filtered_df.groupby(
        "Date_Filter"
    )[
        ["Network_Latency_ms", "Packet_Loss_%"]
    ].mean().reset_index()

    fig = px.line(
        daily_network,
        x="Date_Filter",
        y=["Network_Latency_ms", "Packet_Loss_%"],
        title="Daily Network Performance Trends"
    )

    st.plotly_chart(fig, use_container_width=True)

with tab2:

    st.subheader("Network Quality vs Efficiency")

    efficiency_count = filtered_df[
        "Efficiency_Status"
    ].value_counts().reset_index()

    efficiency_count.columns = [
        "Efficiency_Status", "Records"
    ]

    fig = px.bar(
        efficiency_count,
        x="Efficiency_Status",
        y="Records",
        color="Efficiency_Status",
        title="Efficiency Status Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

    fig = px.box(
        filtered_df,
        x="Network_Quality",
        y="Production_Speed_units_per_hr",
        color="Network_Quality",
        title="Production Speed by Network Quality"
    )

    st.plotly_chart(fig, use_container_width=True)

    fig = px.scatter(
        filtered_df,
        x="Network_Latency_ms",
        y="Production_Speed_units_per_hr",
        color="Network_Quality",
        title="Latency vs Production Speed"
    )

    st.plotly_chart(fig, use_container_width=True)

with tab3:

    st.subheader("Quality and Error Impact")

    col1, col2 = st.columns(2)

    with col1:

        fig = px.scatter(
            filtered_df,
            x="Packet_Loss_%",
            y="Error_Rate_%",
            color="Network_Quality",
            title="Packet Loss vs Error Rate"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:

        fig = px.box(
            filtered_df,
            x="Network_Quality",
            y="Quality_Control_Defect_Rate_%",
            color="Network_Quality",
            title="Defect Rate by Network Quality"
        )

        st.plotly_chart(fig, use_container_width=True)

    quality_table = filtered_df.groupby(
        "Network_Quality",
        observed=True
    )[[
        "Error_Rate_%",
        "Quality_Control_Defect_Rate_%"
    ]].mean().round(2)

    st.write("Quality and Error Summary")
    st.dataframe(quality_table)

with tab4:

    st.subheader("6G Network Optimization Insights")

    latency_limit = df["Network_Latency_ms"].quantile(0.75)

    packet_limit = df["Packet_Loss_%"].quantile(0.75)

    st.write(
        "75th Percentile Latency Benchmark:",
        round(latency_limit, 2), "ms"
    )

    st.write(
        "75th Percentile Packet Loss Benchmark:",
        round(packet_limit, 2), "%"
    )

    st.subheader("Network Risk Zones")

    risk_data = filtered_df.copy()

    risk_data["Network_Risk"] = "Normal"

    risk_data.loc[
        (risk_data["Network_Latency_ms"] > latency_limit) |
        (risk_data["Packet_Loss_%"] > packet_limit),
        "Network_Risk"
    ] = "High Risk"

    risk_summary = risk_data["Network_Risk"].value_counts()

    fig = px.pie(
        values=risk_summary.values,
        names=risk_summary.index,
        title="Network Risk Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Optimization Recommendations")

    st.write("""
    1. Monitor latency variations continuously.

    2. Monitor packet loss to identify communication
       reliability problems.

    3. Investigate machines operating above the
       75th percentile network thresholds.

    4. Compare network conditions with production
       performance before making network investments.

    5. Reassess network performance using real
       operational data and validated thresholds.
    """)

st.divider()

st.caption(
    "6G Network Performance and Manufacturing Efficiency | "
    "Smart Factory Analytics Project"
)
