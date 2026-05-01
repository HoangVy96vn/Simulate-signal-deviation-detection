import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random
from datetime import datetime
import time

st.set_page_config(page_title="Furnace Demo Deviation Detection", layout="wide")

MY_LIMITS = {
    "temperature_zone_1": [800.0, 870.0],
    "temperature_zone_2": [230.0, 270.0],
    "main_gas_flow": [21.0, 27.0],
    "main_gas_pressure": [60.0, 100.0],
    "carbon_potential": [0.7, 1.0],
    "oxygen_mV": [1100.0, 1200.0],
    "CO_percentage": [15.0, 25.0]
}


# --- FUNCTIONS ---

def prepare_data_with_status(df, signal_name):
    status_df = df[df['signal_name'] == "furnace_empty"][['timestamp', 'value']]
    status_df['status_text'] = status_df['value'].map({0.0: "RUN", 1.0: "NO RUN"})
    sig_df = df[df['signal_name'] == signal_name].copy()
    return pd.merge(sig_df, status_df[['timestamp', 'status_text']], on='timestamp', how='left')


def create_dual_y_chart(df, title, sig1, sig2, unit1, unit2, limits):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    # Signal 1
    d1 = prepare_data_with_status(df, sig1)
    fig.add_trace(go.Scatter(x=d1['timestamp'], y=d1['value'], name=sig1, customdata=d1['status_text'],
                             hovertemplate="Value: %{y} " + unit1 + "<br>Status: %{customdata}<extra></extra>"),
                  secondary_y=False)
    # Signal 2
    d2 = prepare_data_with_status(df, sig2)
    fig.add_trace(go.Scatter(x=d2['timestamp'], y=d2['value'], name=sig2, customdata=d2['status_text'],
                             hovertemplate="Value: %{y} " + unit2 + "<br>Status: %{customdata}<extra></extra>"),
                  secondary_y=True)

    # Add Limit Lines
    for sig, is_sec in [(sig1, False), (sig2, True)]:
        if sig in limits:
            y_ref = "y2" if is_sec else "y"
            fig.add_shape(type="line", x0=0, x1=1, xref="paper", y0=limits[sig][1], y1=limits[sig][1], yref=y_ref,
                          line=dict(color="red", width=1, dash="dot"))

    fig.update_layout(title_text=title, height=350, margin=dict(l=10, r=10, t=40, b=10), hovermode="x unified")
    return fig


def style_alert_cells(df):
    style_df = pd.DataFrame('', index=df.index, columns=df.columns)
    for column, limits in MY_LIMITS.items():
        if column in df.columns:
            is_error = (df[column] < limits[0]) | (df[column] > limits[1])
            style_df.loc[is_error, column] = 'background-color: #ff4b4b; color: white'
    return style_df


if 'database' not in st.session_state:
    st.session_state.database = pd.DataFrame(columns=['timestamp', 'signal_name', 'value'])
    st.session_state.alerts = []


def generate_and_check_data():      # function to generate data for simulation
    new_data = []
    ts = datetime.now()
    status = 1.0 if (ts.second // 15) % 2 == 0 else 0.0

    signals = {
        "temperature_zone_1": (850.0, 10.0), "temperature_zone_2": (250.0, 5.0),
        "main_gas_flow": (24.0, 3.0), "main_gas_pressure": (80.0, 10.0),
        "carbon_potential": (0.9, 0.05), "oxygen_mV": (1150.0, 50.0),
        "addition_gas_flow": (350.0, 50.0), "addition_gas_pressure": (45.0, 5.0),
        "CO_percentage": (20.0, 3.0), "furnace_empty": (status, 0)
    }

    for sig, (base, noise) in signals.items():
        val = round(base + random.uniform(-noise, noise), 2)
        if random.random() < 0.05 and sig != "furnace_empty":
            val = round(val * 1.3, 2)

        new_data.append({'timestamp': ts, 'signal_name': sig, 'value': val})

        if sig in MY_LIMITS:
            if val < MY_LIMITS[sig][0] or val > MY_LIMITS[sig][1]:
                st.session_state.alerts.append({"timestamp": ts.strftime('%H:%M:%S'), "message": f"⚠️ {sig}: {val}"})

    new_df = pd.DataFrame(new_data)
    st.session_state.database = pd.concat([st.session_state.database, new_df]).tail(3000)


# --- DASHBOARD INTERFACE ---

st.title("🔥 Real-time Furnace Monitoring")
st.caption("Industrial Dashboard Demo")

# Generate data
generate_and_check_data()
df_full = st.session_state.database
df_plot = df_full.tail(500)

if not df_plot.empty:
    # Metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    latest = df_plot.groupby('signal_name').last()['value']
    m1.metric("Temp Z1", f"{latest.get('temperature_zone_1')} °C")
    m2.metric("Temp Z2", f"{latest.get('temperature_zone_2')} °C")
    m3.metric("Gas Flow", f"{latest.get('main_gas_flow')} m3/h")
    m4.metric("Gas Pressure", f"{latest.get('main_gas_pressure')} mbar")
    m5.metric("Cp", f"{latest.get('carbon_potential')} %")

    m6, m7, m8, m9, m10 = st.columns(5)
    m6.metric("oxygen mV", f"{latest.get('oxygen_mV')} mV")
    m7.metric("CO percentage", f"{latest.get('CO_percentage')} %")
    m8.metric("addition_gas_flow", f"{latest.get('addition_gas_flow')} Nl/h")
    m9.metric("addition_gas_pressure", f"{latest.get('addition_gas_pressure')} mbar")
    m10.metric("Status", "NO RUN" if latest.get('furnace_empty') == 1 else "RUN")


    # Charts
    c1, c2 = st.columns(2)
    with c1:
        # 1/ Temperature Chart (Z1 & Z2 with Hover Status & Multi-Limits)
        fig_temp = go.Figure()
        for s, color in [("temperature_zone_1", "#1f77b4"), ("temperature_zone_2", "#2ca02c")]:
            d = prepare_data_with_status(df_plot, s)
            fig_temp.add_trace(go.Scatter(
                x=d['timestamp'], y=d['value'], name=s,
                customdata=d['status_text'],
                hovertemplate="Value: %{y} °C<br>Status: %{customdata}<extra></extra>",
                line=dict(color=color)
            ))
            # Add limits for each zone
            if s in MY_LIMITS:
                low, up = MY_LIMITS[s]
                fig_temp.add_hline(y=up, line_dash="dot", line_color="red", annotation_text=f"Max {s}")
                fig_temp.add_hline(y=low, line_dash="dot", line_color="orange")

        fig_temp.update_layout(title="Temperature Monitoring (°C)", height=380, hovermode="x unified")
        st.plotly_chart(fig_temp, use_container_width=True)

        st.plotly_chart(
            create_dual_y_chart(df_plot, "Gas Analysis", "main_gas_flow", "main_gas_pressure", "m3/h", "mbar",
                                MY_LIMITS), use_container_width=True)

    with c2:
        st.plotly_chart(
            create_dual_y_chart(df_plot, "Atmosphere (CP/O2)", "carbon_potential", "oxygen_mV", "%", "mV", MY_LIMITS),
            use_container_width=True)
        st.plotly_chart(
            create_dual_y_chart(df_plot, "Addition Gas", "addition_gas_flow", "addition_gas_pressure", "Nl/h", "mbar",
                                MY_LIMITS), use_container_width=True)
    # 2/ CO Percentage Chart (with Limit & Hover Status)
    st.divider()
    st.subheader("CO Percentage Trend")
    d_co = prepare_data_with_status(df_plot, "CO_percentage")
    fig_co = go.Figure()
    fig_co.add_trace(go.Scatter(
        x=d_co['timestamp'], y=d_co['value'], name="CO%",
        customdata=d_co['status_text'],
        hovertemplate="Value: %{y} %<br>Status: %{customdata}<extra></extra>"
    ))
    if "CO_percentage" in MY_LIMITS:
        fig_co.add_hline(y=MY_LIMITS["CO_percentage"][1], line_dash="dash", line_color="red",
                         annotation_text="Max CO%")
        fig_co.add_hline(y=MY_LIMITS["CO_percentage"][0], line_dash="dash", line_color="orange")
    fig_co.update_layout(height=300, hovermode="x unified")
    st.plotly_chart(fig_co, use_container_width=True)


    # 5. TABLES
    st.divider()
    st.subheader("📊 Raw Signals & 🚨 Alert History")

    t_left, t_right = st.columns([2, 1])

    with t_left:
        st.write("Current Data")
        df_p = df_plot.pivot_table(index='timestamp', columns='signal_name', values='value').reset_index()


        def check_alert(row):
            for c, l in MY_LIMITS.items():
                if c in row and (row[c] < l[0] or row[c] > l[1]):
                    return "⚠️ YES"
            return "OK"


        df_p['Is_Alert'] = df_p.apply(check_alert, axis=1)
        df_p = df_p.sort_values('timestamp', ascending=False)
        df_p['timestamp'] = df_p['timestamp'].dt.strftime('%H:%M:%S')
        cols = ['timestamp', 'Is_Alert'] + [c for c in df_p.columns if c not in ['timestamp', 'Is_Alert']]
        df_p = df_p[cols]
        st.dataframe(df_p.style.apply(style_alert_cells, axis=None), use_container_width=True, height=300)

    with t_right:
        st.write("Alert History")
        if st.session_state.alerts:
            df_a = pd.DataFrame(st.session_state.alerts).tail(10).iloc[::-1]
            st.dataframe(df_a, use_container_width=True, height=250)
            if st.button("Clear"):
                st.session_state.alerts = []
                st.rerun()
        else:
            st.success("System Normal")

# Sidebar
st.sidebar.subheader("Quick Watch")
if st.session_state.alerts:
    for a in st.session_state.alerts[-5:]:
        st.sidebar.error(a['message'])

time.sleep(2)
st.rerun()
