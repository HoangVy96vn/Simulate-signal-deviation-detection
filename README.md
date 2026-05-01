**Overview**
This simulates a real-world industrial monitoring system. It features real-time data visualization and an deviation detection system.

**Architecture**
The project demonstrates a modern data pipeline using three core components:

1/ Data Generation (machine.py): A Python script that simulates complex industrial sensor signals with random noise and spikes. - In industry, the signals are collected via MES
2/ Backend API (app.py): Powered by FastAPI, handling data ingestion and processing. - In industry, there are several applications for data collect to MES, but working principle is through API
3/ Live Dashboard (dashboard.py): Built with Streamlit and Plotly for high-performance, real-time monitoring. - Same as SCADA, Grafana in the industry

**How to Experience
**You can explore this project in two ways:

**A/ Quick Web Demo:** Click the link below to see the live dashboard. In this version, data is generated directly within Streamlit for a seamless web experience.
👉 https://simulate-signal-deviation-detection-2urhcqgk84k5xejin9vrgg.streamlit.app/

**B/ Full Industrial Workflow:** To see the complete system architecture in action on your local machine (run requirement.txt), then run the components in this order:

Step 1: Start FastAPI (The data receiver)

Step 2: Run machine.py (The data generator)

Step 3: Launch dashboard.py (The visualization)

(Or run docker-compose.yml file if you have Docker Desktop)

This setup mimics how data flows from a physical machine on a factory floor to a cloud-based monitoring center.

