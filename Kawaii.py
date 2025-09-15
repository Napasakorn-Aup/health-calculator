import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import io

# Global data stores (not persistent, for demonstration within the session)
bmi_history = {}
daily_calories = {}
tdee_value = 0 # To store the TDEE value for use in the food tracker tab

# Helper function to create a blank plot with a specific message
def create_empty_plot(message="No Data to Display"):
    """Creates a blank plot with a custom message for display in Gradio."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(message, fontsize=16)
    ax.axis('off') # Hide axes for a blank plot
    return fig

# Helper function to convert inches to cm and lbs to kg
def convert_to_metric(height, weight, units):
    if units == "in/lbs":
        height_cm = height * 2.54
        weight_kg = weight * 0.453592
    else:
        height_cm = height
        weight_kg = weight
    return height_cm, weight_kg

# Tab 1: BMI Calculator
def calculate_and_track_bmi(height, weight, units, date_str):
    """Calculates BMI, determines category, and tracks it over time."""
    global bmi_history
    
    if height <= 0 or weight <= 0:
        return 0, "Invalid input", "Please enter positive values for height and weight."

    try:
        # Convert the string date input to a datetime object
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return 0, "Invalid date format", "Please enter date in YYYY-MM-DD format."

    height_cm, weight_kg = convert_to_metric(height, weight, units)

    # Convert height to meters for BMI calculation
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    bmi = round(bmi, 2)

    # Determine BMI category
    if bmi < 18.5:
        category = "Underweight"
    elif 18.5 <= bmi < 24.9:
        category = "Normal weight"
    elif 25 <= bmi < 29.9:
        category = "Overweight"
    else:
        category = "Obese"

    # Add to history
    date_str = date.strftime('%Y-%m-%d')
    bmi_history[date_str] = bmi
    
    return bmi, category, f"Your BMI is {bmi}. Category: {category}"

# Tab 2: Daily Metabolic Rate Calculator
def calculate_bmr_tdee(age, gender, height, weight, activity_level):
    """Calculates BMR and TDEE based on the Harris-Benedict equation."""
    global tdee_value
    
    if age <= 0 or height <= 0 or weight <= 0:
        return 0, 0, 0, 0, 0, "Please enter positive values for age, height, and weight."

    # Harris-Benedict Equation for BMR
    if gender == "Male":
        bmr = 66.5 + (13.75 * weight) + (5.003 * height) - (6.75 * age)
    else: # Female
        bmr = 655.1 + (9.563 * weight) + (1.850 * height) - (4.676 * age)
    
    # Activity multipliers
    activity_multipliers = {
        "Sedentary (little to no exercise)": 1.2,
        "Lightly active (1-3 days/week)": 1.375,
        "Moderately active (3-5 days/week)": 1.55,
        "Very active (6-7 days/week)": 1.725,
        "Extra active (daily intense exercise)": 1.9
    }
    
    tdee = bmr * activity_multipliers.get(activity_level, 1.2)
    
    # Calorie goals
    loss_calories = tdee - 500
    gain_calories = tdee + 500
    
    # Store TDEE for the other tab
    tdee_value = tdee
    
    return bmr, tdee, tdee, loss_calories, gain_calories, "Results updated! ✨"

# Tab 3: Food Tracker
def log_food_and_plot(food, manual_food_name, manual_calories):
    """Logs food calories and returns the updated daily calories data and a plot."""
    global daily_calories
    global tdee_value

    calories_to_add = 0
    food_name_to_log = ""
    log_status_message = ""
    
    if food != "Other":
        calories_to_add = int(food.split(" - ")[-1].replace(" kcal", ""))
        food_name_to_log = food.split(" - ")[0]
    elif manual_calories is not None and manual_calories > 0 and manual_food_name:
        calories_to_add = manual_calories
        food_name_to_log = manual_food_name
    
    if calories_to_add <= 0 or not food_name_to_log:
        log_status_message = "Please enter a valid calorie amount and food name. 😟"
        return (daily_calories.get(datetime.now().strftime('%Y-%m-%d'), 0), create_empty_plot(log_status_message), log_status_message)

    # Log food
    today_str = datetime.now().strftime('%Y-%m-%d')
    if today_str in daily_calories:
        daily_calories[today_str] += calories_to_add
    else:
        daily_calories[today_str] = calories_to_add
    
    log_status_message = f"Food logged successfully! Logged: {food_name_to_log} - {calories_to_add} kcal 🎉"

    # Create the plot
    if tdee_value == 0:
        return (daily_calories.get(today_str, 0), create_empty_plot("Please calculate your TDEE in Tab 2 first! ☝️"), "Please calculate your TDEE in Tab 2 first! ☝️")

    # If there's no food data, return an empty plot
    if not daily_calories:
        return (0, create_empty_plot(), "No food logged yet. 🥗")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Prepare data for plotting
    dates = sorted(daily_calories.keys())
    calories = [daily_calories[d] for d in dates]

    df = pd.DataFrame({'date': dates, 'calories': calories})
    df['date'] = pd.to_datetime(df['date'])

    # Plot
    df.plot(kind='bar', x='date', y='calories', ax=ax, legend=False, color='#5DADE2')
    
    # Add TDEE line
    tdee_line_label = f"Your TDEE ({round(tdee_value)} kcal)"
    ax.axhline(y=tdee_value, color='r', linestyle='--', label=tdee_line_label)

    # Customize plot
    ax.set_title("Daily Calorie Intake vs. TDEE", fontsize=16)
    ax.set_xlabel("Date")
    ax.set_ylabel("Calories (kcal)")
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(loc='upper left')

    # Ensure integer ticks for dates
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    
    return daily_calories.get(today_str, 0), fig, log_status_message


# Define common foods for the dropdown
# รายการอาหารไทยยอดฮิตพร้อมปริมาณแคลอรี่โดยประมาณ
common_foods = [
    "Chicken with bazil - 500 kcal",
    "Omelet - 450 kcal",
    "Tom Yum Kung - 90 kcal",
    "Phad Thai - 550 kcal",
    "Chicken Green Curry - 240 kcal",
    "Papaya Salad - 70 kcal",
    "Stew Pork Leg - 650 kcal",
    "Chicken Rice - 600 kcal",
    "Chicken Massaman - 400 kcal",
    "Phad See Ew - 550 kcal",
    "Rice - 130 kcal",
    "Other"
]

# Build the Gradio interface
with gr.Blocks(title="Health Calculator Suite", theme="soft") as app:
    gr.Markdown("# 🥗 BME Health Calculator Suite ✨")
    gr.Markdown("A multi-tab application for all your health tracking needs. 💖")

    # --- Tab 1: BMI Calculator ---
    with gr.Tab(label="BMI Calculator 💖"):
        gr.Markdown("### 🍎 **BMI Calculator** ❤️")
        gr.Markdown("Enter your details to calculate your Body Mass Index.")
        with gr.Column(variant="panel"):
            with gr.Row():
                height_input = gr.Slider(minimum=50, maximum=250, value=170, label="Height", step=1)
                weight_input = gr.Slider(minimum=20, maximum=200, value=70, label="Weight", step=0.1)
            unit_selector = gr.Radio(choices=["cm/kg", "in/lbs"], value="cm/kg", label="Units")
            date_input = gr.Textbox(value=datetime.now().strftime('%Y-%m-%d'), label="Date of Measurement (YYYY-MM-DD)")
            
        calculate_button = gr.Button("Calculate BMI 📈")

        with gr.Column(variant="panel"):
            gr.Markdown("### **Your BMI & Health Status**")
            bmi_output = gr.Number(label="BMI Value")
            category_output = gr.Textbox(label="Category")
            indicator_output = gr.Label(label="BMI Status")

        calculate_button.click(
            calculate_and_track_bmi,
            inputs=[height_input, weight_input, unit_selector, date_input],
            outputs=[bmi_output, category_output, indicator_output]
        )

    # --- Tab 2: Metabolic Rate Calculator ---
    with gr.Tab(label="Daily Metabolic Rate Calculator ⚡"):
        gr.Markdown("### ⚡️ **Daily Calorie Needs Calculator** ✨")
        gr.Markdown("Calculate your Basal Metabolic Rate (BMR) and Total Daily Energy Expenditure (TDEE) to understand your energy needs.")
        
        with gr.Column(variant="panel"):
            age_input = gr.Slider(minimum=10, maximum=100, value=30, label="Age", step=1)
            gender_input = gr.Radio(choices=["Male", "Female"], value="Male", label="Gender")
            with gr.Row():
                height_bmr = gr.Slider(minimum=50, maximum=250, value=170, label="Height (cm)", step=1)
                weight_bmr = gr.Slider(minimum=20, maximum=200, value=70, label="Weight (kg)", step=0.1)
            activity_input = gr.Dropdown(
                choices=["Sedentary (little to no exercise)", "Lightly active (1-3 days/week)", "Moderately active (3-5 days/week)", "Very active (6-7 days/week)", "Extra active (daily intense exercise)"],
                label="Activity Level",
                value="Moderately active (3-5 days/week)"
            )
        
        calculate_bmr_button = gr.Button("Calculate BMR & TDEE 💥")

        with gr.Column(variant="panel"):
            gr.Markdown("### **Your Daily Calorie Goals**")
            bmr_output = gr.Number(label="Basal Metabolic Rate (BMR)")
            tdee_output_display = gr.Number(label="Total Daily Energy Expenditure (TDEE)")
            maintenance_output = gr.Number(label="Calories for Maintenance")
            loss_output = gr.Number(label="Calories for Weight Loss (-500 kcal)")
            gain_output = gr.Number(label="Calories for Weight Gain (+500 kcal)")
            status_output = gr.Textbox(label="Status")

        calculate_bmr_button.click(
            calculate_bmr_tdee,
            inputs=[age_input, gender_input, height_bmr, weight_bmr, activity_input],
            outputs=[bmr_output, tdee_output_display, maintenance_output, loss_output, gain_output, status_output]
        )

    # --- Tab 3: Food Tracker ---
    with gr.Tab(label="Food Tracker 📝"):
        gr.Markdown("### 📝 **Daily Food & Calorie Tracker** 🍲")
        gr.Markdown("Log your food intake and track your daily calories against your TDEE from the previous tab.")
        
        with gr.Row():
            food_dropdown = gr.Dropdown(choices=common_foods, label="Common Foods", value="Other")
            with gr.Column(visible=True) as manual_input_col:
                manual_food_name = gr.Textbox(label="Food Name")
                manual_calories_input = gr.Number(label="Manual Calorie Entry (kcal)")

        log_button = gr.Button("Log Food 🥗")

        with gr.Column(variant="panel"):
            gr.Markdown("### **Summary**")
            daily_total_output = gr.Number(label="Today's Total Calories")
            calorie_plot = gr.Plot()
            log_status_output = gr.Textbox(label="Log Status")

        # Dynamic visibility for manual calorie input
        food_dropdown.change(
            lambda x: gr.update(visible=x == "Other"),
            inputs=food_dropdown,
            outputs=[manual_input_col]
        )
            
        log_button.click(
            log_food_and_plot,
            inputs=[food_dropdown, manual_food_name, manual_calories_input],
            outputs=[daily_total_output, calorie_plot, log_status_output]
        )

# Launch the app
if __name__ == "__main__":
    app.launch(server_port=8001, share=True)

