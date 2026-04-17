import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OLA Ride Analytics",
    page_icon="🚖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0a0e1a; color: #e8eaf0; }

section[data-testid="stSidebar"] {
    background: #0f1526 !important;
    border-right: 1px solid #1e2a45;
}
h1, h2, h3 { font-family: 'Syne', sans-serif !important; color: #ffffff !important; }

[data-testid="metric-container"] {
    background: #111827;
    border: 1px solid #1e2a45;
    border-radius: 12px;
    padding: 1rem 1.2rem;
}
[data-testid="metric-container"] label {
    color: #8892a4 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-family: 'Syne', sans-serif;
    font-size: 1.75rem !important;
    font-weight: 700 !important;
}
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #00d4aa;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
    border-left: 3px solid #00d4aa;
    padding-left: 0.6rem;
}
div.stTabs [data-baseweb="tab-list"] { background: #111827; border-radius: 10px; padding: 4px; }
div.stTabs [data-baseweb="tab"] {
    color: #8892a4;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    border-radius: 8px;
    padding: 0.4rem 1.1rem;
}
div.stTabs [aria-selected="true"] {
    background: #00d4aa !important;
    color: #0a0e1a !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & HELPERS
# ─────────────────────────────────────────────────────────────────────────────
TEAL   = "#00d4aa"
COLORS = ["#00d4aa", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#10b981"]

AXIS   = dict(gridcolor="#1e2a45", linecolor="#1e2a45")
BASE   = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#c9d1e0"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#c9d1e0")),
    title_font=dict(family="Syne", size=16, color="#fff"),
)

def theme(fig, cat_y=False, cat_x=False, **kwargs):
    """Apply dark theme. Use cat_y/cat_x to sort categorical axes."""
    yaxis = {**AXIS, **({"categoryorder": "total ascending"} if cat_y else {})}
    xaxis = {**AXIS, **({"categoryorder": "total ascending"} if cat_x else {})}
    fig.update_layout(**BASE, xaxis=xaxis, yaxis=yaxis, **kwargs)
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADER
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(src) -> pd.DataFrame:
    df = pd.read_csv(src, parse_dates=["ride_datetime"])
    df["date"]           = df["ride_datetime"].dt.date
    df["month"]          = df["ride_datetime"].dt.to_period("M").astype(str)
    df["week"]           = df["ride_datetime"].dt.to_period("W").astype(str)
    df["Booking_Value"]  = pd.to_numeric(df["Booking_Value"],  errors="coerce").fillna(0)
    df["Ride_Distance"]  = pd.to_numeric(df["Ride_Distance"],  errors="coerce").fillna(0)
    df["Driver_Ratings"] = pd.to_numeric(df["Driver_Ratings"], errors="coerce")
    df["Customer_Rating"]= pd.to_numeric(df["Customer_Rating"],errors="coerce")
    return df

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚖 OLA Analytics")
    st.markdown("---")
    uploaded = st.file_uploader("Upload Dataset (CSV)", type=["csv"])
    if uploaded:
        df = load_data(uploaded)
        st.success(f"✅ {len(df):,} rows loaded")
    else:
        try:
            df = load_data("cleaned_ola_data.csv")
            st.info(f"📂 Default dataset · {len(df):,} rows")
        except FileNotFoundError:
            st.error("Place `cleaned_ola_data.csv` in the same folder, or upload above.")
            st.stop()

    st.markdown("### 🔽 Filters")
    d_min = df["ride_datetime"].min().date()
    d_max = df["ride_datetime"].max().date()
    date_range = st.date_input("Date Range", (d_min, d_max), min_value=d_min, max_value=d_max)

    veh_opts = ["All"] + sorted(df["Vehicle_Type"].dropna().unique())
    veh_sel  = st.selectbox("Vehicle Type", veh_opts)

    sta_opts = ["All"] + sorted(df["Booking_Status"].dropna().unique())
    sta_sel  = st.selectbox("Booking Status", sta_opts)

    st.markdown("---")
    st.caption("OLA Ride Project · Streamlit + Plotly")

# ─────────────────────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────────────────────
s, e = (date_range[0], date_range[1]) if len(date_range) == 2 else (d_min, d_max)
fdf = df[(df["ride_datetime"].dt.date >= s) & (df["ride_datetime"].dt.date <= e)].copy()
if veh_sel != "All": fdf = fdf[fdf["Vehicle_Type"] == veh_sel]
if sta_sel != "All": fdf = fdf[fdf["Booking_Status"] == sta_sel]

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='font-size:2rem; margin-bottom:0;'>🚖 OLA Ride Analytics Dashboard</h1>",
            unsafe_allow_html=True)
st.markdown(
    f"<p style='color:#8892a4; margin-top:0;'>Showing "
    f"<b style='color:#00d4aa'>{len(fdf):,}</b> rides &nbsp;·&nbsp; {s} → {e}</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────────────────────────────────────
success = fdf[fdf["Booking_Status"] == "Success"]
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Rides",          f"{len(fdf):,}")
k2.metric("Successful Rides",     f"{len(success):,}")
k3.metric("Total Revenue",        f"₹{success['Booking_Value'].sum():,.0f}")
k4.metric("Avg Customer Rating",  f"{fdf['Customer_Rating'].mean():.2f} ⭐")
k5.metric("Avg Driver Rating",    f"{fdf['Driver_Ratings'].mean():.2f} ⭐")
st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
t1, t2, t3, t4, t5, t6 = st.tabs([
    "📈 Ride Trends",
    "📊 Booking Status",
    "🚗 Vehicle Analysis",
    "❌ Cancellations",
    "💰 Revenue & Distance",
    "👤 Customers & Ratings",
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 · RIDE VOLUME OVER TIME
# ═══════════════════════════════════════════════════════════════════════════
with t1:
    st.markdown("<div class='section-title'>1 · Ride Volume Over Time</div>", unsafe_allow_html=True)

    gran = st.radio("Granularity", ["Daily", "Weekly", "Monthly"], horizontal=True)
    if gran == "Daily":
        rv = fdf.groupby("date").size().reset_index(name="Rides")
        rv["date"] = pd.to_datetime(rv["date"])
        xcol = "date"
    elif gran == "Weekly":
        rv = fdf.groupby("week").size().reset_index(name="Rides")
        xcol = "week"
    else:
        rv = fdf.groupby("month").size().reset_index(name="Rides")
        xcol = "month"

    fig = px.area(rv, x=xcol, y="Rides", color_discrete_sequence=[TEAL],
                  title="Ride Volume Over Time")
    fig.update_traces(line_width=2, fillcolor="rgba(0,212,170,0.12)")
    theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-title'>Rides by Hour of Day</div>", unsafe_allow_html=True)
    hv = fdf.groupby("hour").size().reset_index(name="Rides")
    fig2 = px.bar(hv, x="hour", y="Rides", color="Rides",
                  color_continuous_scale=["#1e2a45", TEAL],
                  title="Hourly Ride Distribution",
                  labels={"hour": "Hour of Day"})
    theme(fig2, coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 · BOOKING STATUS BREAKDOWN
# ═══════════════════════════════════════════════════════════════════════════
with t2:
    st.markdown("<div class='section-title'>2 · Booking Status Breakdown</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    sc = fdf["Booking_Status"].value_counts().reset_index()
    sc.columns = ["Status", "Count"]

    c1, c2 = st.columns(2)
    with c1:
        fig = px.pie(sc, names="Status", values="Count",
                     color_discrete_sequence=COLORS, hole=0.55,
                     title="Booking Status Share")
        fig.update_traces(textinfo="percent+label")
        theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig2 = px.bar(sc, x="Status", y="Count", color="Status",
                      color_discrete_sequence=COLORS, text="Count",
                      title="Booking Status Count")
        fig2.update_traces(textposition="outside", texttemplate="%{text:,}")
        theme(fig2, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<div class='section-title'>Status × Vehicle Type Heatmap</div>", unsafe_allow_html=True)
    pivot = fdf.groupby(["Vehicle_Type", "Booking_Status"]).size().unstack(fill_value=0)
    fig3 = px.imshow(pivot, text_auto=True,
                     color_continuous_scale=["#0a0e1a", TEAL],
                     title="Ride Count: Vehicle × Status", aspect="auto")
    theme(fig3)
    st.plotly_chart(fig3, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 · VEHICLE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
with t3:
    st.markdown("<div class='section-title'>3 · Top 5 Vehicle Types by Ride Distance</div>",
                unsafe_allow_html=True)

    top5d = (fdf.groupby("Vehicle_Type")["Ride_Distance"].sum().reset_index()
             .sort_values("Ride_Distance", ascending=False).head(5))
    fig = px.bar(top5d, x="Ride_Distance", y="Vehicle_Type", orientation="h",
                 color="Ride_Distance", color_continuous_scale=["#1e2a45", TEAL],
                 text="Ride_Distance", title="Top 5 Vehicle Types by Total Distance (km)")
    fig.update_traces(texttemplate="%{text:,.0f} km", textposition="outside")
    theme(fig, cat_y=True, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-title'>Avg Ride Distance per Vehicle Type</div>",
                unsafe_allow_html=True)
    avg_d = fdf.groupby("Vehicle_Type")["Ride_Distance"].mean().reset_index()
    avg_d.columns = ["Vehicle_Type", "Avg_km"]
    fig2 = px.bar(avg_d.sort_values("Avg_km", ascending=False),
                  x="Vehicle_Type", y="Avg_km",
                  color_discrete_sequence=[COLORS[1]],
                  text="Avg_km", title="Avg Ride Distance by Vehicle (km)")
    fig2.update_traces(texttemplate="%{text:.1f} km", textposition="outside")
    theme(fig2)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<div class='section-title'>4 · Avg Customer Rating by Vehicle Type</div>",
                unsafe_allow_html=True)
    avg_r = fdf.groupby("Vehicle_Type")["Customer_Rating"].mean().reset_index()
    avg_r.columns = ["Vehicle_Type", "Avg_Rating"]
    fig3 = px.bar(avg_r.sort_values("Avg_Rating", ascending=False),
                  x="Vehicle_Type", y="Avg_Rating",
                  color="Avg_Rating", color_continuous_scale=["#1e2a45", "#f59e0b"],
                  text="Avg_Rating", title="Avg Customer Rating by Vehicle Type",
                  range_y=[3.5, 5])
    fig3.update_traces(texttemplate="%{text:.2f} ⭐", textposition="outside")
    theme(fig3, coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 · CANCELLATIONS
# ═══════════════════════════════════════════════════════════════════════════
with t4:
    st.markdown("<div class='section-title'>5 · Canceled Rides Reasons</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### 🙋 Canceled by Customer")
        cc = fdf["Canceled_Rides_by_Customer"].dropna().value_counts().reset_index()
        cc.columns = ["Reason", "Count"]
        if cc.empty:
            st.info("No customer cancellation data for current filter.")
        else:
            fig = px.bar(cc, x="Count", y="Reason", orientation="h",
                         color_discrete_sequence=[COLORS[4]], text="Count",
                         title="Customer Cancellation Reasons")
            fig.update_traces(textposition="outside")
            theme(fig, cat_y=True, height=330)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("##### 🚗 Canceled by Driver")
        dc = fdf["Canceled_Rides_by_Driver"].dropna().value_counts().reset_index()
        dc.columns = ["Reason", "Count"]
        if dc.empty:
            st.info("No driver cancellation data for current filter.")
        else:
            fig2 = px.bar(dc, x="Count", y="Reason", orientation="h",
                          color_discrete_sequence=[COLORS[3]], text="Count",
                          title="Driver Cancellation Reasons")
            fig2.update_traces(textposition="outside")
            theme(fig2, cat_y=True, height=330)
            st.plotly_chart(fig2, use_container_width=True)

    # Combined grouped bar
    all_r = pd.concat([
        fdf["Canceled_Rides_by_Customer"].dropna().rename("Reason")
           .to_frame().assign(By="Customer"),
        fdf["Canceled_Rides_by_Driver"].dropna().rename("Reason")
           .to_frame().assign(By="Driver"),
    ])
    if not all_r.empty:
        st.markdown("<div class='section-title'>All Cancellation Reasons Combined</div>",
                    unsafe_allow_html=True)
        rc = all_r.groupby(["Reason", "By"]).size().reset_index(name="Count")
        fig3 = px.bar(rc, x="Count", y="Reason", color="By", orientation="h",
                      color_discrete_sequence=[COLORS[4], COLORS[3]],
                      barmode="group", title="All Cancellation Reasons by Type")
        theme(fig3, cat_y=True)
        st.plotly_chart(fig3, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 · REVENUE & DISTANCE
# ═══════════════════════════════════════════════════════════════════════════
with t5:
    st.markdown("<div class='section-title'>6 · Revenue by Payment Method</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    rev = fdf[fdf["Booking_Status"] == "Success"].copy()
    pay = (rev.groupby("Payment_Method")["Booking_Value"].sum().reset_index()
           .rename(columns={"Booking_Value": "Revenue"})
           .query("Payment_Method != 'Unknown'")
           .sort_values("Revenue", ascending=False))

    c1, c2 = st.columns(2)
    with c1:
        fig = px.pie(pay, names="Payment_Method", values="Revenue",
                     color_discrete_sequence=COLORS, hole=0.5,
                     title="Revenue Share by Payment Method")
        fig.update_traces(textinfo="percent+label")
        theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig2 = px.bar(pay, x="Payment_Method", y="Revenue", color="Payment_Method",
                      color_discrete_sequence=COLORS, text="Revenue",
                      title="Total Revenue by Payment Method (₹)")
        fig2.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
        theme(fig2, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<div class='section-title'>8 · Ride Distance Distribution Per Day</div>",
                unsafe_allow_html=True)
    dd = (fdf[fdf["Ride_Distance"] > 0]
          .groupby("date")["Ride_Distance"].mean().reset_index()
          .rename(columns={"Ride_Distance": "Avg_km"}))
    dd["date"] = pd.to_datetime(dd["date"])
    fig3 = px.line(dd, x="date", y="Avg_km", color_discrete_sequence=[COLORS[2]],
                   title="Average Ride Distance Per Day (km)", markers=True)
    fig3.update_traces(line_width=2)
    theme(fig3)
    st.plotly_chart(fig3, use_container_width=True)

    fig4 = px.histogram(fdf[fdf["Ride_Distance"] > 0], x="Ride_Distance", nbins=40,
                        color_discrete_sequence=[TEAL],
                        title="Ride Distance Frequency Distribution",
                        labels={"Ride_Distance": "Distance (km)"})
    theme(fig4)
    st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 6 · CUSTOMERS & RATINGS
# ═══════════════════════════════════════════════════════════════════════════
with t6:
    st.markdown("<div class='section-title'>7 · Top 5 Customers by Total Booking Value</div>",
                unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    top5c = (fdf[fdf["Booking_Status"] == "Success"]
             .groupby("Customer_ID")["Booking_Value"].sum().reset_index()
             .sort_values("Booking_Value", ascending=False).head(5))
    fig = px.bar(top5c, x="Booking_Value", y="Customer_ID", orientation="h",
                 color="Booking_Value", color_continuous_scale=["#1e2a45", TEAL],
                 text="Booking_Value", title="Top 5 Customers by Total Booking Value (₹)")
    fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
    theme(fig, cat_y=True, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("<div class='section-title'>9 · Driver Ratings Distribution</div>",
                    unsafe_allow_html=True)
        fig2 = px.histogram(fdf["Driver_Ratings"].dropna(), nbins=30,
                            color_discrete_sequence=[COLORS[1]],
                            title="Driver Ratings Distribution",
                            labels={"value": "Rating", "count": "Frequency"})
        theme(fig2, xaxis_title="Driver Rating", yaxis_title="Count")
        st.plotly_chart(fig2, use_container_width=True)

    with c2:
        st.markdown("<div class='section-title'>10 · Customer vs Driver Ratings</div>",
                    unsafe_allow_html=True)
        rdf = fdf[["Customer_Rating", "Driver_Ratings", "Vehicle_Type"]].dropna()
        fig3 = px.scatter(
            rdf.sample(min(3000, len(rdf))),
            x="Driver_Ratings", y="Customer_Rating",
            color="Vehicle_Type", color_discrete_sequence=COLORS,
            opacity=0.5, title="Customer vs Driver Ratings",
            labels={"Driver_Ratings": "Driver Rating",
                    "Customer_Rating": "Customer Rating"},
        )
        # Reference diagonal line — uses rgba() string, fully compatible with Plotly
        fig3.add_shape(
            type="line", x0=3.5, y0=3.5, x1=5, y1=5,
            line=dict(color="rgba(255,255,255,0.2)", dash="dash", width=1),
        )
        theme(fig3)
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("<div class='section-title'>Ratings Comparison — Box Plot</div>",
                unsafe_allow_html=True)
    rm = (fdf[["Customer_Rating", "Driver_Ratings"]]
          .melt(var_name="Type", value_name="Rating").dropna())
    fig4 = px.box(rm, x="Type", y="Rating", color="Type",
                  color_discrete_sequence=[COLORS[2], COLORS[1]],
                  title="Customer vs Driver Rating Distribution", notched=True)
    theme(fig4, showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#3a4a6b; font-size:0.78rem;'>"
    "OLA Ride Analytics · Streamlit + Plotly</p>",
    unsafe_allow_html=True,
)