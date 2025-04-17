import streamlit as st
import requests
import google.generativeai as genai
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import time

# ----- Configuration Section -----
# Initialize Gemini first to check available models
try:
    # Replace with your actual API keys
    NUTRITIONIX_APP_ID = "86fa04aa"
    NUTRITIONIX_APP_KEY = "716e0158803762211a05efdf5ead8962"
    GEMINI_API_KEY = "AIzaSyCW0Zy224PWYZDE4e-sd2EfU-RXzDEtws4"

    genai.configure(api_key=GEMINI_API_KEY)

    # List available models to debug
    available_models = [m.name for m in genai.list_models()]
    print("Available models:", available_models)  # Check your console output

    # Select the correct model name from available models
    if 'models/gemini-1.5-pro-latest' in available_models:
        MODEL_NAME = 'models/gemini-1.5-pro-latest'
    elif 'models/gemini-pro' in available_models:
        MODEL_NAME = 'models/gemini-pro'
    else:
        MODEL_NAME = available_models[0]  # Fallback to first available model
except Exception as e:
    st.error(f"Failed to initialize Gemini: {str(e)}")
    st.stop()

# ----- Initialize Session State -----
if 'meal_log' not in st.session_state:
    st.session_state['meal_log'] = []
if 'water_intake' not in st.session_state:
    st.session_state['water_intake'] = 0
if 'exercise_log' not in st.session_state:
    st.session_state['exercise_log'] = []
if 'user_goals' not in st.session_state:
    st.session_state['user_goals'] = {
        'daily_calories': 2000,
        'daily_protein': 50,
        'daily_carbs': 300,
        'daily_fat': 65,
        'daily_water': 8  # glasses
    }
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = False


# ----- Functions -----
def get_gemini_response(prompt):
    """Universal function to handle Gemini responses with proper model selection"""
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        error_msg = f"Gemini API Error: {str(e)}"
        print(error_msg)  # Debug in console
        return error_msg


def get_diet_advice(meal_description, nutrition_summary, diet_pref=""):
    prompt = f"""
    I just ate: {meal_description}.
    Nutrition: {nutrition_summary}
    Diet Preference: {diet_pref if diet_pref else 'None'}

    Please provide:
    1. Health evaluation (brief, bullet points)
    2. Specific suggestions for improvement
    3. Diet compatibility analysis
    4. Healthier alternatives (3 options)
    5. Nutrient balance assessment

    Format the response in clear markdown sections.
    """
    return get_gemini_response(prompt)


def get_nutrition_data(query):
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_APP_KEY,
        "Content-Type": "application/json"
    }
    data = {"query": query}
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def get_exercise_data(query):
    url = "https://trackapi.nutritionix.com/v2/natural/exercise"
    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_APP_KEY,
        "Content-Type": "application/json"
    }
    data = {"query": query}
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def calculate_bmi(weight, height):
    return weight / ((height / 100) ** 2)


def get_bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 25:
        return "Normal weight"
    elif 25 <= bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def calculate_tdee(weight, height, age, gender, activity_level):
    """Calculate Total Daily Energy Expenditure"""
    if gender.lower() == 'male':
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)

    activity_multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very active': 1.9
    }

    return bmr * activity_multipliers.get(activity_level.lower(), 1.2)


def create_nutrition_radar_chart(meals):
    if not meals:
        return None

    df = pd.DataFrame(meals)
    totals = df[['calories', 'protein', 'carbs', 'fat']].sum()

    # Normalize values for radar chart (0-100 scale)
    max_values = pd.Series({
        'calories': st.session_state.user_goals['daily_calories'],
        'protein': st.session_state.user_goals['daily_protein'] * 4,  # Convert to calories
        'carbs': st.session_state.user_goals['daily_carbs'] * 4,
        'fat': st.session_state.user_goals['daily_fat'] * 9
    })

    normalized = (totals / max_values * 100).clip(0, 100)

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=normalized.values,
        theta=normalized.index,
        fill='toself',
        name='Today'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="Daily Nutrition Progress"
    )

    return fig


def create_water_tracker():
    glasses = st.session_state.water_intake
    goal = st.session_state.user_goals['daily_water']
    percent = min(100, (glasses / goal) * 100)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percent,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Water Intake"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "blue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 75], 'color': "gray"},
                {'range': [75, 100], 'color': "darkblue"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 100}
        }
    ))

    fig.update_layout(height=200, margin=dict(t=0, b=0, l=0, r=0))
    return fig


def create_calorie_tracker():
    if not st.session_state.meal_log:
        return None

    df = pd.DataFrame(st.session_state.meal_log)
    total_calories = df['calories'].sum()
    goal = st.session_state.user_goals['daily_calories']
    percent = min(100, (total_calories / goal) * 100)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percent,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Calorie Intake"},
        gauge={
            'axis': {'range': [None, 125]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, 60], 'color': "lightgreen"},
                {'range': [60, 90], 'color': "green"},
                {'range': [90, 125], 'color': "darkgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 100}
        }
    ))

    fig.update_layout(height=200, margin=dict(t=0, b=0, l=0, r=0))
    return fig


def generate_meal_plan(diet_pref, calories, restrictions=""):
    prompt = f"""
    Generate a one-day meal plan with:
    - Diet preference: {diet_pref}
    - Target calories: {calories}
    - Dietary restrictions: {restrictions if restrictions else 'None'}

    Include:
    1. Breakfast
    2. Lunch
    3. Dinner
    4. 2 Snacks

    For each meal, provide:
    - Meal name
    - Ingredients list
    - Preparation steps (brief)
    - Estimated calories
    - Macronutrient breakdown

    Format the response in clear markdown sections.
    """
    return get_gemini_response(prompt)


# ----- UI Layout -----
# Main App
st.sidebar.title("Welcome!")

# User Profile Section
with st.sidebar.expander("👤 Profile Settings"):
    with st.form("profile_form"):
        age = st.number_input("Age", 10, 100, 25)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        weight = st.number_input("Weight (kg)", 30.0, 200.0, 70.0)
        height = st.number_input("Height (cm)", 100.0, 250.0, 170.0)
        activity_level = st.selectbox("Activity Level",
                                      ["Sedentary", "Light", "Moderate", "Active", "Very Active"])

        if st.form_submit_button("Update Profile"):
            tdee = calculate_tdee(weight, height, age, gender, activity_level)
            st.session_state.user_goals['daily_calories'] = round(tdee)
            st.session_state.user_goals['daily_protein'] = round(weight * 1.6)  # 1.6g per kg of body weight
            st.session_state.user_goals['daily_carbs'] = round((tdee * 0.5) / 4)  # 50% of calories from carbs
            st.session_state.user_goals['daily_fat'] = round((tdee * 0.3) / 9)  # 30% of calories from fat
            st.success("Profile updated!")

# Goals Section
with st.sidebar.expander("🎯 Daily Goals"):
    st.write("Calories:", st.session_state.user_goals['daily_calories'])
    st.write("Protein:", st.session_state.user_goals['daily_protein'], "g")
    st.write("Carbs:", st.session_state.user_goals['daily_carbs'], "g")
    st.write("Fat:", st.session_state.user_goals['daily_fat'], "g")
    st.write("Water:", st.session_state.user_goals['daily_water'], "glasses")

# Dark Mode Toggle
st.session_state.dark_mode = st.sidebar.toggle("Dark Mode", st.session_state.dark_mode)

# Main Content
st.title("🍏 AI Health & Nutrition Assistant")

# Dashboard Overview
st.header("📊 Your Daily Dashboard")
col1, col2, col3 = st.columns(3)

with col1:
    if st.session_state.meal_log:
        df = pd.DataFrame(st.session_state.meal_log)
        total_calories = df['calories'].sum()
        st.metric("Calories Consumed", f"{total_calories} / {st.session_state.user_goals['daily_calories']}")

with col2:
    st.metric("Water Intake",
              f"{st.session_state.water_intake} / {st.session_state.user_goals['daily_water']} glasses")

with col3:
    if st.session_state.exercise_log:
        df = pd.DataFrame(st.session_state.exercise_log)
        total_calories_burned = df['calories'].sum()
        st.metric("Calories Burned", total_calories_burned)

# Visualization Row
viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    radar_chart = create_nutrition_radar_chart(st.session_state.meal_log)
    if radar_chart:
        st.plotly_chart(radar_chart, use_container_width=True)

with viz_col2:
    water_chart = create_water_tracker()
    st.plotly_chart(water_chart, use_container_width=True)

    calorie_chart = create_calorie_tracker()
    if calorie_chart:
        st.plotly_chart(calorie_chart, use_container_width=True)

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Nutrition Analysis",
    "BMI Calculator",
    "Meal Log",
    "Exercise",
    "Meal Planner",
    "Ask AI"
])

with tab1:
    st.header("🍎 Food Nutrition Analyzer")
    user_input = st.text_area("Describe your meal:", placeholder="e.g., grilled chicken with rice and salad")
    diet_pref = st.selectbox("Your Diet Preference",
                             ["None", "Keto", "Vegan", "Low Carb", "High Protein", "Mediterranean"])

    if st.button("Analyze Meal"):
        if not user_input.strip():
            st.warning("Please enter a meal description")
        else:
            with st.spinner("Analyzing your meal..."):
                nutrition_data = get_nutrition_data(user_input)
                if "error" in nutrition_data:
                    st.error("Failed to fetch data.")
                    st.code(nutrition_data["error"])
                else:
                    summary_text = ""
                    meal_record = []
                    for item in nutrition_data['foods']:
                        st.subheader(f"🍽️ {item['food_name'].title()}")
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Calories", f"{item['nf_calories']} kcal")
                        col2.metric("Protein", f"{item['nf_protein']} g")
                        col3.metric("Carbs", f"{item['nf_total_carbohydrate']} g")
                        col4.metric("Fat", f"{item['nf_total_fat']} g")

                        summary_text += f"{item['food_name'].title()}: {item['nf_calories']} kcal, {item['nf_protein']}g protein, {item['nf_total_carbohydrate']}g carbs, {item['nf_total_fat']}g fat\n"
                        meal_record.append({
                            "food": item['food_name'].title(),
                            "calories": item['nf_calories'],
                            "protein": item['nf_protein'],
                            "carbs": item['nf_total_carbohydrate'],
                            "fat": item['nf_total_fat'],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })

                    st.session_state.meal_log.extend(meal_record)

                    with st.expander("💡 AI Nutritionist's Advice"):
                        advice = get_diet_advice(user_input, summary_text, diet_pref)
                        st.markdown(advice)

with tab2:
    st.header("📊 Health Metrics")

    with st.expander("BMI Calculator"):
        weight = st.number_input("Weight (kg)", 30.0, 200.0, 70.0, key="bmi_weight")
        height = st.number_input("Height (cm)", 100.0, 250.0, 170.0, key="bmi_height")
        if st.button("Calculate BMI"):
            bmi = calculate_bmi(weight, height)
            category = get_bmi_category(bmi)
            st.metric("Your BMI", f"{bmi:.1f}", category)

            # BMI Chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=bmi,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "BMI Scale"},
                gauge={
                    'axis': {'range': [10, 50]},
                    'steps': [
                        {'range': [10, 18.5], 'color': "lightblue"},
                        {'range': [18.5, 25], 'color': "lightgreen"},
                        {'range': [25, 30], 'color': "yellow"},
                        {'range': [30, 50], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': bmi}
                }
            ))
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("TDEE Calculator"):
        tdee = calculate_tdee(weight, height, age, gender, activity_level)
        st.metric("Your TDEE", f"{tdee:.0f} kcal/day")
        st.caption("Total Daily Energy Expenditure - calories you burn per day")

with tab3:
    st.header("📜 Your Nutrition Log")

    # Water Tracker
    st.subheader("💧 Water Intake Tracker")
    water_col1, water_col2 = st.columns([1, 3])
    with water_col1:
        if st.button("+1 Glass"):
            st.session_state.water_intake += 1
            st.rerun()
        if st.button("Reset"):
            st.session_state.water_intake = 0
            st.rerun()
    with water_col2:
        st.write(f"Today's intake: {st.session_state.water_intake} glasses")

    # Meal Log
    st.subheader("🍽️ Meal History")
    if st.session_state.meal_log:
        df = pd.DataFrame(st.session_state.meal_log)

        # Daily Summary
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_summary = df.groupby('date').agg({
            'calories': 'sum',
            'protein': 'sum',
            'carbs': 'sum',
            'fat': 'sum'
        }).reset_index()

        st.write("Daily Summary:")
        st.dataframe(daily_summary)

        # Detailed Log
        st.write("Detailed Log:")
        st.dataframe(df)

        # Time-based Analysis
        st.subheader("⏰ Time Analysis")
        time_fig = px.line(df, x='timestamp', y='calories', title='Calorie Intake Throughout Day')
        st.plotly_chart(time_fig, use_container_width=True)

        # Download Button
        st.download_button("Download CSV", df.to_csv(index=False), "nutrition_log.csv")
    else:
        st.info("No meals logged yet.")

with tab4:
    st.header("🏋️ Exercise Tracking")
    exercise_input = st.text_area("Describe your exercise:", placeholder="e.g., ran 5 km in 30 minutes")

    if st.button("Log Exercise"):
        if not exercise_input.strip():
            st.warning("Please describe your exercise")
        else:
            with st.spinner("Calculating calories burned..."):
                exercise_data = get_exercise_data(exercise_input)
                if "error" in exercise_data:
                    st.error("Failed to fetch data.")
                    st.code(exercise_data["error"])
                else:
                    for exercise in exercise_data['exercises']:
                        st.subheader(f"🏃 {exercise['name'].title()}")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Duration", f"{exercise['duration_min']} min")
                        col2.metric("Calories Burned", f"{exercise['nf_calories']} kcal")
                        col3.metric("MET Value", f"{exercise['met']}")

                        st.session_state.exercise_log.append({
                            "exercise": exercise['name'].title(),
                            "duration": exercise['duration_min'],
                            "calories": exercise['nf_calories'],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })

    # Exercise Log
    st.subheader("Your Exercise History")
    if st.session_state.exercise_log:
        df = pd.DataFrame(st.session_state.exercise_log)
        st.dataframe(df)

        # Exercise Summary
        st.subheader("Exercise Summary")
        fig = px.bar(df, x='exercise', y='calories', title='Calories Burned by Exercise')
        st.plotly_chart(fig, use_container_width=True)

        st.download_button("Download Exercise Log", df.to_csv(index=False), "exercise_log.csv")
    else:
        st.info("No exercises logged yet.")

with tab5:
    st.header("📅 Meal Planner")

    with st.form("meal_plan_form"):
        diet_pref = st.selectbox("Diet Preference", ["Balanced", "Keto", "Vegan", "Low Carb", "High Protein"])
        calorie_target = st.number_input("Daily Calorie Target", 1200, 5000,
                                         st.session_state.user_goals['daily_calories'])
        restrictions = st.text_input("Dietary Restrictions (optional)", placeholder="e.g., no nuts, gluten-free")

        if st.form_submit_button("Generate Meal Plan"):
            with st.spinner("Creating your personalized meal plan..."):
                meal_plan = generate_meal_plan(diet_pref, calorie_target, restrictions)
                st.markdown(meal_plan)

with tab6:
    st.header("🤖 Ask AI Nutritionist")
    query = st.text_area("Ask any health, nutrition, or fitness question:")

    if st.button("Ask Gemini"):
        if query:
            with st.spinner("Getting expert advice..."):
                response = get_gemini_response(query)
                st.markdown(response)
        else:
            st.warning("Please enter a question")

# Footer
st.markdown("---")
st.caption(f"© {datetime.now().year} Health & Nutrition Assistant | Powered by Nutritionix and Google Gemini AI")