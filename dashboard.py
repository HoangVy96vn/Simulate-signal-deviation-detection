import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import time

st.set_page_config(page_title="Furnace Monitoring System", layout="wide")

st.title("🔥 Hệ thống Giám sát Lò nung - Dashboard Nâng cao")

# Cấu hình đường dẫn dữ liệu
machine_id = "FURNACE-001"
file_path = f"data/{machine_id}.csv"


def create_dual_y_chart(df, title, sig1, sig2, unit1, unit2):
    """Hàm hỗ trợ vẽ biểu đồ 2 trục Y"""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Dữ liệu tín hiệu 1
    d1 = df[df['signal_name'] == sig1]
    fig.add_trace(
        go.Scatter(x=d1['timestamp'], y=d1['value'], name=sig1, mode='lines'),
        secondary_y=False,
    )

    # Dữ liệu tín hiệu 2
    d2 = df[df['signal_name'] == sig2]
    fig.add_trace(
        go.Scatter(x=d2['timestamp'], y=d2['value'], name=sig2, mode='lines'),
        secondary_y=True,
    )

    fig.update_layout(title_text=title, hovermode="x unified", height=400)
    fig.update_yaxes(title_text=f"<b>{sig1}</b> ({unit1})", secondary_y=False)
    fig.update_yaxes(title_text=f"<b>{sig2}</b> ({unit2})", secondary_y=True)

    return fig


# Vòng lặp cập nhật Dashboard
placeholder = st.empty()

while True:
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # Chỉ lấy 100 điểm gần nhất để đảm bảo hiệu suất biểu đồ
            df = df.tail(1000)
        except:
            continue

        with placeholder.container():
            # --- KHU VỰC CHỈ SỐ NHANH (METRICS) ---
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            latest = df.groupby('signal_name').last()['value']

            m_col1.metric("Nhiệt độ Z1", f"{latest.get('temperature_zone_1', 0)} °C")
            m_col2.metric("Áp suất Gas", f"{latest.get('main_gas_pressure', 0)} Pa")
            m_col3.metric("Carbon Potential", f"{latest.get('carbon_potential', 0)} %")
            m_col4.metric("Trạng thái lò", "TRỐNG" if latest.get('furnace_empty', 0) == 1 else "CHẠY")

            st.divider()

            # --- KHU VỰC BIỂU ĐỒ ---
            col_left, col_right = st.columns(2)

            with col_left:
                # 1. Biểu đồ Nhiệt độ (2 vùng)
                fig_temp = go.Figure()
                for s in ["temperature_zone_1", "temperature_zone_2"]:
                    d = df[df['signal_name'] == s]
                    fig_temp.add_trace(go.Scatter(x=d['timestamp'], y=d['value'], name=s))
                fig_temp.update_layout(title="Temperature Monitoring", yaxis_title="°C")
                st.plotly_chart(fig_temp, use_container_width=True)

                # 2. Biểu đồ Main Gas (Flow & Pressure) - 2 Trục Y
                fig_gas = create_dual_y_chart(df, "Main Gas Analysis",
                                              "main_gas_flow", "main_gas_pressure",
                                              "m3/h", "Pa")
                st.plotly_chart(fig_gas, use_container_width=True)

            with col_right:
                # 3. Biểu đồ Carbon & Oxygen - 2 Trục Y
                fig_cp = create_dual_y_chart(df, "Atmosphere Control",
                                             "carbon_potential", "oxygen_mV",
                                             "%", "mV")
                st.plotly_chart(fig_cp, use_container_width=True)

                # 4. Biểu đồ Addition Gas - 2 Trục Y
                fig_add_gas = create_dual_y_chart(df, "Addition Gas Analysis",
                                                  "addition_gas_flow", "addition_gas_pressure",
                                                  "m3/h", "Pa")
                st.plotly_chart(fig_add_gas, use_container_width=True)

            # 5. Biểu đồ CO Percentage (Biểu đồ đơn)
            st.divider()
            co_data = df[df['signal_name'] == "CO_percentage"]
            st.subheader("CO Percentage Trend")
            st.line_chart(co_data.set_index('timestamp')['value'])
    # Thêm vào cuối file dashboard.py, sau phần vẽ biểu đồ

    st.divider()
    st.subheader("🚨 Nhật ký cảnh báo hệ thống (Real-time Alerts)")

    alert_file = "data/alerts_log.csv"

    if os.path.exists(alert_file):
        try:
            # Đọc log cảnh báo
            df_alerts = pd.read_csv(alert_file)

            # Đảo ngược bảng để cảnh báo mới nhất hiện lên đầu
            df_alerts = df_alerts.iloc[::-1]


            # Định nghĩa hàm để tô màu dòng dựa trên loại cảnh báo
            def highlight_alerts(row):
                if "[L2-SPIKE]" in row.message:
                    return ['background-color: #ff4b4b; color: white'] * len(row)  # Đỏ đậm cho Spike
                return ['background-color: #ffa500; color: black'] * len(row)  # Cam cho Range


            # Hiển thị bảng với style
            st.dataframe(
                df_alerts.head(20).style.apply(highlight_alerts, axis=1),
                use_container_width=True,
                height=400
            )

            # Nút bấm để xóa nhật ký cảnh báo nếu quá nhiều
            if st.button("Clear Alert Logs"):
                os.remove(alert_file)
                st.rerun()

        except Exception as e:
            st.write("Đang chờ dữ liệu cảnh báo mới...")
    else:
        st.info("Hiện tại hệ thống vận hành ổn định, chưa ghi nhận cảnh báo nào.")

    time.sleep(2)