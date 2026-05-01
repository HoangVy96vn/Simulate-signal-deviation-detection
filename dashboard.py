import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import time

st.set_page_config(page_title="Furnace Monitoring System", layout="wide")

st.title("🔥 Furnace Monitoring System - Advanced Realtime")

# --- CONFIGURATION ---
machine_id = "FURNACE-001"
file_path = f"data/{machine_id}.csv"
alert_file = "data/alerts_log.csv"

MY_LIMITS = {
    "temperature_zone_1": [800.0, 870.0],
    "temperature_zone_2": [230.0, 270.0],
    "main_gas_pressure": [60.0, 100.0],
    "carbon_potential": [0.7, 0.9],
    "oxygen_mV": [1100.0, 1200.0],
    "CO_percentage": [15.0, 25.0]
}


# --- HELPER FUNCTIONS ---

def prepare_data_with_status(df, signal_name):
    """Add furnace_empty (condition) into to show when Hover into datapoints on dashboard"""
    status_df = df[df['signal_name'] == "furnace_empty"][['timestamp', 'value']]
    status_df['status_text'] = status_df['value'].map({0.0: "RUN", 1.0: "NO RUN"})

    sig_df = df[df['signal_name'] == signal_name].copy()
    merged = pd.merge(sig_df, status_df[['timestamp', 'status_text']], on='timestamp', how='left')
    return merged


def create_dual_y_chart(df, title, sig1, sig2, unit1, unit2, limits):
    """Function to draw chart dual y-axis plus Hover Status và Limit Shapes"""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1st signal (Left)
    d1 = prepare_data_with_status(df, sig1)
    fig.add_trace(go.Scatter(
        x=d1['timestamp'], y=d1['value'], name=sig1,
        customdata=d1['status_text'],
        hovertemplate="<b>%{x}</b><br>Value: %{y} " + unit1 + "<br>Status: %{customdata}<extra></extra>",
        line=dict(color='#1f77b4')
    ), secondary_y=False)

    # 2nd signal (Right)
    d2 = prepare_data_with_status(df, sig2)
    fig.add_trace(go.Scatter(
        x=d2['timestamp'], y=d2['value'], name=sig2,
        customdata=d2['status_text'],
        hovertemplate="<b>%{x}</b><br>Value: %{y} " + unit2 + "<br>Status: %{customdata}<extra></extra>",
        line=dict(color='#ff7f0e')
    ), secondary_y=True)

    # Add Shapes for Limits
    for sig, is_secondary in [(sig1, False), (sig2, True)]:
        if sig in limits:
            low, up = limits[sig]
            y_ref = "y2" if is_secondary else "y"
            dash_style = "dash" if is_secondary else "dot"
            fig.add_shape(type="line", x0=0, x1=1, xref="paper", y0=up, y1=up, yref=y_ref,
                          line=dict(color="red", width=1, dash=dash_style))
            fig.add_shape(type="line", x0=0, x1=1, xref="paper", y0=low, y1=low, yref=y_ref,
                          line=dict(color="red", width=1, dash=dash_style))

    fig.update_layout(title_text=title, height=380, hovermode="x unified", margin=dict(l=20, r=20, t=50, b=20))
    fig.update_yaxes(title_text=unit1, secondary_y=False)
    fig.update_yaxes(title_text=unit2, secondary_y=True)
    return fig


def highlight_alerts(row):
    """Style alert table rows"""
    if "[L2-SPIKE]" in str(row.message):
        return ['background-color: #ff4b4b; color: white'] * len(row)
    return ['background-color: #ffa500; color: black'] * len(row)


# --- MAIN DASHBOARD LOOP ---

placeholder = st.empty()

while True:
    with placeholder.container():
        if os.path.exists(file_path):
            try:
                df_full = pd.read_csv(file_path)
                df_full['timestamp'] = pd.to_datetime(df_full['timestamp'])
                df_plot = df_full.tail(500)

                # --- 1. METRICS ---
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                latest = df_full.groupby('signal_name').last()['value']
                m_col1.metric("Temp Z1", f"{latest.get('temperature_zone_1', 0)} °C")
                m_col2.metric("Gas Pressure", f"{latest.get('main_gas_pressure', 0)} Bar")
                m_col3.metric("Carbon Potential", f"{latest.get('carbon_potential', 0)} %")
                m_col4.metric("Furnace Status", "NO RUN" if latest.get('furnace_empty', 0) == 1 else "RUN")

                st.divider()

                # --- 2. CHARTS ---
                col_left, col_right = st.columns(2)

                with col_left:
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

                    # Main Gas
                    st.plotly_chart(
                        create_dual_y_chart(df_plot, "Main Gas Analysis", "main_gas_flow", "main_gas_pressure", "m3/h",
                                            "Bar", MY_LIMITS), use_container_width=True)

                with col_right:
                    # Atmosphere
                    st.plotly_chart(
                        create_dual_y_chart(df_plot, "Atmosphere Control (CP/O2)", "carbon_potential", "oxygen_mV", "%",
                                            "mV", MY_LIMITS), use_container_width=True)

                    # Addition Gas
                    st.plotly_chart(create_dual_y_chart(df_plot, "Addition Gas Analysis", "addition_gas_flow",
                                                        "addition_gas_pressure", "Nl/h", "Bar", MY_LIMITS),
                                    use_container_width=True)

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

                # --- 3. RAW SIGNALS DATA TABLE (500 ROWS + ALERT COLUMN) ---
                st.divider()
                st.subheader("📊 Raw Signals Data Table (Last 500 Points)")

                df_pivot = df_plot.pivot_table(index='timestamp', columns='signal_name', values='value').reset_index()


                # 1. Table raw data visualize which data points is out, which time has alert
                def check_row_alert(row):
                    for col, limits in MY_LIMITS.items():
                        if col in row:
                            val = row[col]
                            if val < limits[0] or val > limits[1]:
                                return "⚠️ YES"
                    return "OK"


                df_pivot['Is_Alert'] = df_pivot.apply(check_row_alert, axis=1)


                # 2. Highlight in red for alert values
                def style_alert_cells(df):
                    # Create empty dataframe same shape with df for CSS format
                    style_df = pd.DataFrame('', index=df.index, columns=df.columns)

                    for col, limits in MY_LIMITS.items():
                        if col in df.columns:
                            # Condition: value out threshold
                            is_error = (df[col] < limits[0]) | (df[col] > limits[1])
                            # Style
                            style_df.loc[is_error, col] = 'background-color: #ff4b4b; color: white; font-weight: bold'

                    return style_df

                # Show the newest information
                df_pivot = df_pivot.sort_values(by='timestamp', ascending=False)

                # Format time to string
                df_display = df_pivot.copy()
                df_display['timestamp'] = df_display['timestamp'].dt.strftime('%H:%M:%S %d-%m-%Y')

                # Show Alert at the first column
                cols = ['timestamp', 'Is_Alert'] + [c for c in df_pivot.columns if c not in ['timestamp', 'Is_Alert']]
                df_display = df_display[cols]

                # Style
                st.dataframe(
                    df_display.style.apply(style_alert_cells, axis=None),
                    use_container_width=True,
                    height=400
                )

            except Exception as e:
                st.error(f"Error processing data: {e}")

        # --- 4. ALERT HISTORY ---
        st.divider()
        st.subheader("🚨 ALERT LOGS (Backend Detected)")
        if os.path.exists(alert_file):
            try:
                df_alerts = pd.read_csv(alert_file)
                if not df_alerts.empty:
                    st.dataframe(df_alerts.tail(15).iloc[::-1].style.apply(highlight_alerts, axis=1),
                                 use_container_width=True)
                    if st.button("🗑️ Clear Alert Logs"):
                        os.remove(alert_file)
                        st.rerun()
                else:
                    st.info("No alert recorded.")
            except:
                pass
        else:
            st.success("✅ Furnace running well.")

    time.sleep(2)