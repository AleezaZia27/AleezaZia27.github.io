# ===============================
# 🌍 Chakwal Climate Dashboard (Optimized, POWER data integrated)
# ===============================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="Chakwal Climate Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# Load & Prepare Data (Optimized)
# -------------------------------
@st.cache_data
def load_data():
    file_path = os.path.join(
        "projects",
        "Chakwal_Climate_Solar_Trends",
        "POWER_Point_Daily_20000101_20241231_032d93N_072d86E_LST.csv"
    )

    df = pd.read_csv(file_path, skiprows=32)

    for col in ["YEAR", "MO", "DY"]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' is missing from the dataset!")

    df["YEAR"] = df["YEAR"].astype(int)
    df["MO"] = df["MO"].fillna(1).astype(int)
    df["DY"] = df["DY"].fillna(1).astype(int)

    df["DATE"] = pd.to_datetime(dict(year=df["YEAR"], month=df["MO"], day=df["DY"]), errors="coerce")
    df["year"] = df["DATE"].dt.year
    df["month"] = df["DATE"].dt.month
    df["month_name"] = df["DATE"].dt.strftime("%b")

    df = df.rename(columns={
        "T2M": "Mean_Temp_C",
        "T2M_MAX": "Max_Temp_C",
        "PRECTOTCORR": "Total_Rain_mm",
        "ALLSKY_SFC_SW_DWN": "Solar_Irradiance_kWh_per_m²_per_day"
    })

    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    # Precompute aggregates to avoid recalculating in tabs
    aggregates = {}

    aggregates["yearly_temp"] = df.groupby("year")["Mean_Temp_C"].mean().reset_index()
    aggregates["yearly_max_temp"] = df.groupby("year")["Max_Temp_C"].max().reset_index()
    aggregates["annual_rain"] = df.groupby("year")["Total_Rain_mm"].sum().reset_index()
    aggregates["annual_solar"] = df.groupby("year")["Solar_Irradiance_kWh_per_m²_per_day"].mean().reset_index()
    aggregates["annual_solar"]["Clipped"] = aggregates["annual_solar"]["Solar_Irradiance_kWh_per_m²_per_day"].clip(
        lower=aggregates["annual_solar"]["Solar_Irradiance_kWh_per_m²_per_day"].mean()-2*aggregates["annual_solar"]["Solar_Irradiance_kWh_per_m²_per_day"].std(),
        upper=aggregates["annual_solar"]["Solar_Irradiance_kWh_per_m²_per_day"].mean()+2*aggregates["annual_solar"]["Solar_Irradiance_kWh_per_m²_per_day"].std()
    )
    aggregates["annual_solar"]["Trend"] = aggregates["annual_solar"]["Clipped"].rolling(3, center=True).mean()

    aggregates["monthly"] = df.groupby(["year","month"]).agg({
        "Mean_Temp_C":"mean",
        "Total_Rain_mm":"sum"
    }).reset_index()
    aggregates["monthly_solar"] = df.groupby(["year","month"])["Solar_Irradiance_kWh_per_m²_per_day"].mean().reset_index()
    aggregates["monthly_solar"]["Trend"] = aggregates["monthly_solar"].rolling(3, on="year", center=True).mean()

    # Heatmaps
    pivot_temp = aggregates["monthly"].pivot(index="month", columns="year", values="Mean_Temp_C").sort_index()
    pivot_temp.index = [month_order[int(m)-1] for m in pivot_temp.index]
    aggregates["heatmap_temp"] = pivot_temp

    pivot_rain = aggregates["monthly"].pivot(index="month", columns="year", values="Total_Rain_mm").sort_index()
    pivot_rain.index = [month_order[int(m)-1] for m in pivot_rain.index]
    aggregates["heatmap_rain"] = pivot_rain

    # Seasonal
    seasonal_avg = df.groupby("month").agg({
        "Mean_Temp_C":"mean",
        "Total_Rain_mm":"mean"
    }).reset_index()
    seasonal_avg["month_name"] = seasonal_avg["month"].apply(lambda x: month_order[x-1])
    aggregates["seasonal_avg"] = seasonal_avg

    # Correlation
    aggregates["corr_matrix"] = df[["Mean_Temp_C","Max_Temp_C","Total_Rain_mm","Solar_Irradiance_kWh_per_m²_per_day"]].corr()

    # Highlights
    aggregates["hottest_year"] = int(df.groupby("year")["Max_Temp_C"].mean().idxmax())
    aggregates["hottest_val"] = float(df.groupby("year")["Max_Temp_C"].mean().max())
    aggregates["coolest_year"] = int(df.groupby("year")["Mean_Temp_C"].mean().idxmin())
    aggregates["coolest_val"] = float(df.groupby("year")["Mean_Temp_C"].mean().min())
    aggregates["wettest_year"] = int(df.groupby("year")["Total_Rain_mm"].sum().idxmax())
    aggregates["wettest_val"] = float(df.groupby("year")["Total_Rain_mm"].sum().max())
    aggregates["driest_year"] = int(df.groupby("year")["Total_Rain_mm"].sum().idxmin())
    aggregates["driest_val"] = float(df.groupby("year")["Total_Rain_mm"].sum().min())
    aggregates["solar_year"] = int(df.groupby("year")["Solar_Irradiance_kWh_per_m²_per_day"].mean().idxmax())
    aggregates["solar_val"] = float(df.groupby("year")["Solar_Irradiance_kWh_per_m²_per_day"].mean().max())
    aggregates["rainiest_month"] = df.groupby("month_name")["Total_Rain_mm"].sum().idxmax()
    aggregates["longest_dry"] = int((df["Total_Rain_mm"]==0).astype(int).groupby(df["year"]).sum().max())

    return df, aggregates

df, agg = load_data()
month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# -------------------------------
# Sidebar Navigation
# -------------------------------
st.sidebar.title("🌍 Chakwal Climate Dashboard")
tab = st.sidebar.radio(
    "Navigate",
    ["Overview", "Temperature", "Rainfall & Solar", "Monthly Trends & Heatmaps", "Correlation & Insights", "Seasonal Analysis", "Highlights & Location"]
)

# -------------------------------
# Overview
# -------------------------------
if tab == "Overview":
    st.markdown("<h2 style='color:#000000;'>🌄 Climate Overview (2000–2024)</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Temperature (°C)", f"{df['Mean_Temp_C'].mean():.1f}",
                delta=f"{df['Mean_Temp_C'].max()-df['Mean_Temp_C'].min():.1f}")
    col2.metric("Total Rainfall (mm)", f"{df['Total_Rain_mm'].sum():.1f}",
                delta=f"{df['Total_Rain_mm'].max()-df['Total_Rain_mm'].min():.1f}")
    col3.metric("Avg Solar Irradiance", f"{df['Solar_Irradiance_kWh_per_m²_per_day'].mean():.2f} kWh/m²/day",
                delta=f"{df['Solar_Irradiance_kWh_per_m²_per_day'].max()-df['Solar_Irradiance_kWh_per_m²_per_day'].min():.2f}")

    roll_window = st.selectbox("Select Rolling Trend Window (years)", [3,5,10], index=0)
    yearly_temp = agg["yearly_temp"].copy()
    yearly_temp["Trend"] = yearly_temp["Mean_Temp_C"].rolling(roll_window, center=True).mean()

    fig = px.line(
        yearly_temp, x="year", y="Mean_Temp_C",
        title="Average Annual Temperature with Rolling Trend",
        markers=True, template="plotly_white"
    )
    fig.add_trace(go.Scatter(
        x=yearly_temp["year"], y=yearly_temp["Trend"],
        mode="lines", name=f"{roll_window}-Year Trend",
        line=dict(color="red", dash="dash")
    ))
    fig.add_trace(go.Scatter(
        x=yearly_temp["year"], y=yearly_temp["Trend"] + yearly_temp["Mean_Temp_C"].std(),
        fill=None, mode='lines', line_color='lightpink', showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=yearly_temp["year"], y=yearly_temp["Trend"] - yearly_temp["Mean_Temp_C"].std(),
        fill='tonexty', mode='lines', line_color='lightpink', name="Trend ±1 Std Dev"
    ))
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# Temperature
# -------------------------------
elif tab == "Temperature":
    st.markdown("<h2 style='color:#000000;'>🌡 Temperature Analysis</h2>", unsafe_allow_html=True)

    yearly_max = agg["yearly_max_temp"].copy()
    mean_temp = yearly_max["Max_Temp_C"].mean()
    std_temp = yearly_max["Max_Temp_C"].std()
    yearly_max["Anomaly"] = yearly_max["Max_Temp_C"] > (mean_temp + std_temp)

    fig = px.scatter(
        yearly_max, x="year", y="Max_Temp_C", color="Anomaly",
        color_discrete_map={True: "green", False: "red"},
        title="Max Temperature with Anomalies", template="plotly_white"
    )
    fig.add_trace(go.Scatter(
        x=yearly_max["year"], y=yearly_max["Max_Temp_C"].rolling(3).mean(),
        mode="lines", name="3-Year Avg",
        line=dict(color="orange", dash="dash")
    ))
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# Rainfall & Solar
# -------------------------------
elif tab == "Rainfall & Solar":
    st.markdown("<h2 style='color:#000000;'>🌧 Rainfall & ☀ Solar</h2>", unsafe_allow_html=True)

    fig_rain = px.bar(
        agg["annual_rain"], x="year", y="Total_Rain_mm",
        title="Annual Total Rainfall (mm)", template="plotly_white",
        color_discrete_sequence=["#1f77b4"]
    )
    st.plotly_chart(fig_rain, use_container_width=True)

    fig_solar = px.line(
        agg["annual_solar"], x="year", y="Clipped",
        title="Annual Solar Irradiance (Clipped ±2σ) with 3-Year Trend",
        markers=True, template="plotly_white"
    )
    fig_solar.update_traces(line=dict(color="gold"), marker=dict(color="gold"))
    fig_solar.add_trace(go.Scatter(
        x=agg["annual_solar"]["year"], y=agg["annual_solar"]["Trend"],
        mode="lines",
        name="3-Year Trend",
        line=dict(color="orange", dash="dash")
    ))
    st.plotly_chart(fig_solar, use_container_width=True)

# -------------------------------
# Monthly Trends & Heatmaps
# -------------------------------
elif tab == "Monthly Trends & Heatmaps":
    st.markdown("<h2 style='color:#000000;'>🔥 Monthly Trends & Heatmaps</h2>", unsafe_allow_html=True)

    selected_month = st.selectbox("Select Month for Trends", month_order, index=0)
    selected_month_num = month_order.index(selected_month) + 1

    month_df = agg["monthly"][agg["monthly"]["month"]==selected_month_num].sort_values("year")
    fig_temp = px.line(
        month_df, x="year", y="Mean_Temp_C",
        title=f"📈 {selected_month} Mean Temperature Across Years",
        markers=True, template="plotly_white"
    )
    fig_temp.update_traces(line=dict(color="orange"), marker=dict(color="orange"))
    st.plotly_chart(fig_temp, use_container_width=True)

    fig_rain = px.bar(
        month_df, x="year", y="Total_Rain_mm",
        title=f"🌧 {selected_month} Rainfall Across Years",
        template="plotly_white", color_discrete_sequence=["#1f77b4"]
    )
    st.plotly_chart(fig_rain, use_container_width=True)

    monthly_solar = agg["monthly_solar"][agg["monthly_solar"]["month"]==selected_month_num].sort_values("year")
    fig_solar_month = go.Figure()
    fig_solar_month.add_trace(go.Scatter(
        x=monthly_solar["year"],
        y=monthly_solar["Solar_Irradiance_kWh_per_m²_per_day"],
        mode="lines+markers",
        name="Solar Irradiance",
        line=dict(color="gold"),
        marker=dict(color="gold", size=6)
    ))
    fig_solar_month.add_trace(go.Scatter(
        x=monthly_solar["year"],
        y=monthly_solar["Trend"],
        mode="lines",
        name="3-Year Trend",
        line=dict(color="orange", dash="dash")
    ))
    fig_solar_month.update_layout(
        title=f"Solar Irradiance in {selected_month} (kWh/m²/day) with 3-Year Trend",
        xaxis_title="Year",
        yaxis_title="Solar Irradiance",
        template="plotly_white"
    )
    st.plotly_chart(fig_solar_month, use_container_width=True)

    # Heatmaps
    fig_heat_temp = px.imshow(
        agg["heatmap_temp"],
        labels=dict(x="Year", y="Month", color="Temp °C"),
        color_continuous_scale="Oranges",
        title="Monthly Mean Temperature Heatmap",
        aspect="auto"
    )
    st.plotly_chart(fig_heat_temp, use_container_width=True)

    fig_heat_rain = px.imshow(
        agg["heatmap_rain"],
        labels=dict(x="Year", y="Month", color="Rain (mm)"),
        color_continuous_scale=px.colors.sequential.Blues,
        title="Monthly Rainfall Heatmap",
        aspect="auto"
    )
    st.plotly_chart(fig_heat_rain, use_container_width=True)

# -------------------------------
# Correlation & Insights
# -------------------------------
elif tab == "Correlation & Insights":
    st.markdown("<h2 style='color:#000000;'>📊 Correlation & Insights</h2>", unsafe_allow_html=True)

    fig_corr = px.imshow(
        agg["corr_matrix"],
        text_auto=True,
        color_continuous_scale="RdBu_r",
        title="Correlation Between Climate Variables",
        aspect="auto"
    )
    st.plotly_chart(fig_corr, use_container_width=True)

# -------------------------------
# Seasonal Analysis
# -------------------------------
elif tab == "Seasonal Analysis":
    st.markdown("<h2 style='color:#000000;'>📈 Seasonal Trends</h2>", unsafe_allow_html=True)

    fig_temp = px.line(
        agg["seasonal_avg"], x="month_name", y="Mean_Temp_C",
        title="Average Monthly Temperature Across Years",
        markers=True, template="plotly_white"
    )
    st.plotly_chart(fig_temp, use_container_width=True)

    fig_rain = px.bar(
        agg["seasonal_avg"], x="month_name", y="Total_Rain_mm",
        title="Average Monthly Rainfall Across Years",
        template="plotly_white", color_discrete_sequence=["#1f77b4"]
    )
    st.plotly_chart(fig_rain, use_container_width=True)

# -------------------------------
# Highlights & Location
# -------------------------------
elif tab == "Highlights & Location":
    st.markdown("<h2 style='color:#000000;'>📊 Climate Highlights & Chakwal Location</h2>", unsafe_allow_html=True)

    st.markdown(f"""
    - 🌡 **Hottest Year:** {agg['hottest_year']} (Avg Max Temp {agg['hottest_val']:.1f}°C)  
    - ❄ **Coolest Year:** {agg['coolest_year']} (Avg Mean Temp {agg['coolest_val']:.1f}°C)  
    - 🌧 **Wettest Year:** {agg['wettest_year']} ({agg['wettest_val']:.0f} mm rainfall)  
    - 🌵 **Driest Year:** {agg['driest_year']} ({agg['driest_val']:.0f} mm rainfall)  
    - ☀ **Highest Solar Irradiance:** {agg['solar_year']} ({agg['solar_val']:.2f} kWh/m²/day)  
    - ⛈ **Rainiest Month (overall):** {agg['rainiest_month']}  
    - 🔎 **Longest Dry Spell (approx. yearly zeros):** ~{agg['longest_dry']} days
    """)

    st.markdown("### 🗺 Chakwal Location")
    st.map(pd.DataFrame({"lat":[32.9336], "lon":[72.8530]}), zoom=9)

# -------------------------------
# Footer
# -------------------------------
st.markdown(
    "<hr><p style='text-align:center; color:gray;'>© 2025 Aleeza Zia | Chakwal Climate Dashboard</p>",
    unsafe_allow_html=True
)
