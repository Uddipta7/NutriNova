# NutriNova - AI-Powered Nutrition & Fitness Assistant 🍏🏋️‍♂️

## 🌟 Overview
NutriNova is an intelligent health companion that combines **nutrition analysis**, **fitness tracking**, and **AI-powered advice** into one powerful Streamlit application. It helps users:

- 🔍 Analyze food nutrition using AI vision
- 📊 Track calories, macros, and water intake
- 🏋️‍♂️ Log exercises and calculate calories burned
- 🧠 Get personalized meal plans and health advice
- 📈 Visualize progress with interactive dashboards

## 🚀 Key Features
| Feature | Description |
|---------|-------------|
| **🍎 Food Analysis** | Get instant nutrition facts for any meal description |
| **📉 Calorie Tracker** | Log meals and monitor daily intake vs goals |
| **💧 Hydration Monitor** | Track water consumption with visual gauge |
| **🏃 Exercise Logger** | Calculate calories burned from workout descriptions |
| **🧮 Health Calculators** | BMI, TDEE, and body metrics analysis |
| **📅 AI Meal Planner** | Generate personalized meal plans based on diet |
| **🤖 Nutrition Assistant** | Ask health questions to Gemini AI |

## 🛠️ Tech Stack
### Core Technologies
- **Frontend**: 
  ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=Streamlit&logoColor=white)
  ![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat&logo=plotly)
  
- **Backend**: 
  ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
  ![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas)
  ![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat&logo=numpy)

- **APIs**:
  ![Nutritionix](https://img.shields.io/badge/Nutritionix-00B140?style=flat)
  ![Gemini AI](https://img.shields.io/badge/Google_Gemini-4285F4?style=flat&logo=google)

### Data Visualization
- Interactive charts with Plotly
- Real-time gauges for water/calorie tracking
- Nutrition radar charts for macro balance

## 📦 Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Uddipta7/NutriNova.git
   cd NutriNova
2. Set Up Virtual Environment:
   Windows:
   ```
   python -m venv venv
   venv\Scripts\activate
3. Install Dependencies
   ```
   pip install -r requirements.txt
4. Configure API Keys
   Create .streamlit/secrets.toml file with:
   ```
   NUTRITIONIX_APP_ID = "your_nutritionix_app_id"
   NUTRITIONIX_APP_KEY = "your_nutritionix_app_key"
   GEMINI_API_KEY = "your_google_gemini_key"
5. Run the Application
   ```
   streamlit run app.py
6. Access the App
   Open your browser and navigate to:
   ```
   http://localhost:8501
