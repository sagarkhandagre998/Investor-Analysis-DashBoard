# Investor-Analysis-DashBoard

This project is a Dash + Plotly based interactive dashboard for analyzing vehicle registration trends across categories, manufacturers, and time periods.
It allows filtering, YoY/QoQ comparisons, and top manufacturer insights for investors.

Implementation and Video WalkThrough - https://drive.google.com/drive/folders/1YRmZFLMHhmstSdHGWupvujvyZobjpR90?usp=drive_link

🚀 Setup Instructions

1️⃣ Clone the Repository

git clone https://github.com/sagarkhandagre998/Investor-Analysis-DashBoard.git

cd Investor-Analysis-DashBoard

2️⃣ Activate Virtual Environment

# Activate venv (Windows)
venv\Scripts\activate

# Activate venv (Mac/Linux)
source venv/bin/activate

3️⃣ Install Dependencies (if needed)

pip install -r requirements.txt

5️⃣ Run the Application

python scripts\dashboard.py or py scripts\dashboard.py

6️⃣ Access the Dashboard
  http://127.0.0.1:8050/

🛠 Tech Stack
  
Python 3.9+

Dash (for UI)

Plotly (for graphs)

Pandas (for data processing)

🚀 Future Enhancements

This project can be extended with the following features to improve usability, performance, and analytical capabilities:

🔹 Short-Term (1–2 weeks)

UI/UX Improvements: Better color palettes, consistent category colors, and responsive filter alignment.

Export Options: Download filtered datasets as CSV/Excel and export graphs as images.

Default Dashboard Insights: Show top-performing manufacturers and quick summaries on initial load.

🔹 Mid-Term (1–2 months)

Advanced Filtering: Grouped category dropdowns, combined year-month filtering.

Performance Boost: Use caching to improve load times and precompute aggregations.

Mobile Optimization: Fully responsive design for mobile and tablet devices.

Smart Filter Dependency: Auto-update manufacturer list dynamically based on selected category.

🔹 Long-Term (3–6 months)

Live Data Integration: Connect with VAHAN API for real-time updates.

User Profiles: Secure login for investors with saved preferences.

Predictive Analytics: Add sales forecasting using time-series modeling.

Comparative Analysis: Compare multiple manufacturers over time.

Cloud Deployment: Host on Heroku, AWS, or Azure with a custom domain and HTTPS.

