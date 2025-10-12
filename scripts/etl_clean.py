import pandas as pd
import numpy as np
from sqlalchemy import create_engine



def yes_no_to_binary(val):
    if isinstance(val, str):
        val = val.strip().lower()
        if val in ["yes", "y", "true", "1"]:
            return 1
        elif val in ["no", "n", "false", "0"]:
            return 0
    return np.nan

def map_scale(val, mapping):
    if pd.isna(val):
        return np.nan
    return mapping.get(str(val).strip().lower(), np.nan)

def range_to_midpoint(val):
    if isinstance(val, str) and "-" in val:
        nums = [float(x) for x in val.replace("hours","").replace("days","").strip().split("-") if x.strip().isdigit()]
        if len(nums) == 2:
            return sum(nums) / 2
    try:
        return float(val)
    except:
        return np.nan



def load_lifestyle(path):
    df = pd.read_csv(path)
    return pd.DataFrame({
        "source":"lifestyle",
        "country": df.get("Country"),
        "age": pd.to_numeric(df.get("Age"), errors="coerce"),
        "gender": df.get("Gender"),
        "exercise_level": df.get("Exercise Level").str.lower().map({"low":1,"moderate":2,"high":3}),
        "diet_type": df.get("Diet Type"),
        "sleep_hours": pd.to_numeric(df.get("Sleep Hours"), errors="coerce"),
        "stress_level": df.get("Stress Level").str.lower().map({"low":1,"medium":2,"high":3}),
        "mental_condition": df.get("Mental Health Condition"),
        "work_hours": pd.to_numeric(df.get("Work Hours per Week"), errors="coerce"),
        "screen_time": pd.to_numeric(df.get("Screen Time per Day (Hours)"), errors="coerce"),
        "social_interaction": pd.to_numeric(df.get("Social Interaction Score"), errors="coerce"),
        "happiness_score": pd.to_numeric(df.get("Happiness Score"), errors="coerce")
    })

def load_stress(path):
    df = pd.read_csv(path)
    return pd.DataFrame({
        "source":"stress_coping",
        "age": pd.to_numeric(df.get("Age"), errors="coerce"),
        "gender": df.get("Gender"),
        "gpa": pd.to_numeric(df.get("Academic Performance (GPA)"), errors="coerce"),
        "study_hours": pd.to_numeric(df.get("Study Hours Per Week"), errors="coerce"),
        "social_media_hours": pd.to_numeric(df.get("Social Media Usage (Hours per day)"), errors="coerce"),
        "sleep_hours": pd.to_numeric(df.get("Sleep Duration (Hours per night)"), errors="coerce"),
        "exercise_hours": pd.to_numeric(df.get("Physical Exercise (Hours per week)"), errors="coerce"),
        "family_support": pd.to_numeric(df.get("Family Support"), errors="coerce"),
        "financial_stress": pd.to_numeric(df.get("Financial Stress"), errors="coerce"),
        "peer_pressure": pd.to_numeric(df.get("Peer Pressure"), errors="coerce"),
        "relationship_stress": pd.to_numeric(df.get("Relationship Stress"), errors="coerce"),
        "mental_stress": pd.to_numeric(df.get("Mental Stress Level"), errors="coerce"),
        "counseling": df.get("Counseling Attendance").map(yes_no_to_binary),
        "diet_quality": pd.to_numeric(df.get("Diet Quality"), errors="coerce"),
        "cognitive_distortions": pd.to_numeric(df.get("Cognitive Distortions"), errors="coerce"),
        "family_history": df.get("Family Mental Health History").map(yes_no_to_binary),
        "medical_condition": df.get("Medical Condition").map(yes_no_to_binary),
        "substance_use": pd.to_numeric(df.get("Substance Use"), errors="coerce")
    })

def load_depression(path):
    df = pd.read_csv(path)
    return pd.DataFrame({
        "source":"depression",
        "id": df.get("id"),
        "age": pd.to_numeric(df.get("Age"), errors="coerce"),
        "gender": df.get("Gender"),
        "city": df.get("City"),
        "profession": df.get("Profession"),
        "academic_pressure": pd.to_numeric(df.get("Academic Pressure"), errors="coerce"),
        "work_pressure": pd.to_numeric(df.get("Work Pressure"), errors="coerce"),
        "cgpa": pd.to_numeric(df.get("CGPA"), errors="coerce"),
        "study_satisfaction": pd.to_numeric(df.get("Study Satisfaction"), errors="coerce"),
        "job_satisfaction": pd.to_numeric(df.get("Job Satisfaction"), errors="coerce"),
        "sleep_hours": df.get("Sleep Duration").apply(range_to_midpoint),
        "dietary_habits": df.get("Dietary Habits"),
        "degree": df.get("Degree"),
        "suicidal_thoughts": df.get("Have you ever had suicidal thoughts ?").map(yes_no_to_binary),
        "work_study_hours": pd.to_numeric(df.get("Work/Study Hours"), errors="coerce"),
        "financial_stress": pd.to_numeric(df.get("Financial Stress"), errors="coerce"),
        "family_history": df.get("Family History of Mental Illness").map(yes_no_to_binary),
        "depression": pd.to_numeric(df.get("Depression"), errors="coerce")
    })

def load_mobile(path):
    df = pd.read_csv(path)
    return pd.DataFrame({
        "source":"mobile",
        "age": df.get("Age"),
        "gender": df.get("Gender"),
        "mobile_use_hours": df.get("Daily usages").apply(range_to_midpoint),
        "performance_impact": df.get("Performance impact").str.lower().map({"strongly agree":3,"agree":2,"neutral":1}),
        "attention_span": df.get("Attention span").map(yes_no_to_binary),
        "health_risks": df.get("Health Risks").map(yes_no_to_binary),
        "symptoms": df.get("Usage symptoms"),
        "symptom_freq": df.get("Symptom frequency")
    })

def load_global(path):
    df = pd.read_csv(path)
    return pd.DataFrame({
        "source":"global",
        "user_id": df.get("User_ID"),
        "age": pd.to_numeric(df.get("Age"), errors="coerce"),
        "gender": df.get("Gender"),
        "occupation": df.get("Occupation"),
        "country": df.get("Country"),
        "mental_condition": df.get("Mental_Health_Condition").map(yes_no_to_binary),
        "severity": df.get("Severity").str.lower().map({"none":0,"low":1,"medium":2,"high":3}),
        "consultation_history": df.get("Consultation_History").map(yes_no_to_binary),
        "stress_level": df.get("Stress_Level").str.lower().map({"low":1,"medium":2,"high":3}),
        "sleep_hours": pd.to_numeric(df.get("Sleep_Hours"), errors="coerce"),
        "work_hours": pd.to_numeric(df.get("Work_Hours"), errors="coerce"),
        "exercise_hours": pd.to_numeric(df.get("Physical_Activity_Hours"), errors="coerce")
    })

def load_generic(path):
    df = pd.read_csv(path)
    return pd.DataFrame({
        "source":"survey",
        "gender": df.get("Gender"),
        "country": df.get("Country"),
        "occupation": df.get("Occupation"),
        "family_history": df.get("family_history").map(yes_no_to_binary),
        "treatment": df.get("treatment").map(yes_no_to_binary),
        "days_indoors": df.get("Days_Indoors").apply(range_to_midpoint),
        "growing_stress": df.get("Growing_Stress").map(yes_no_to_binary),
        "changes_habits": df.get("Changes_Habits").map(yes_no_to_binary),
        "mental_history": df.get("Mental_Health_History").map(yes_no_to_binary),
        "mood_swings": df.get("Mood_Swings").str.lower().map({"low":1,"medium":2,"high":3}),
        "coping_struggles": df.get("Coping_Struggles").map(yes_no_to_binary),
        "work_interest": df.get("Work_Interest").map(yes_no_to_binary),
        "social_weakness": df.get("Social_Weakness").map(yes_no_to_binary)
    })


def run_all():
    dfs = []
    dfs.append(load_lifestyle("/Users/danzhou/Downloads/5120dataset/Mental_Health_Lifestyle_Dataset.csv"))
    dfs.append(load_stress("/Users/danzhou/Downloads/5120dataset/Student_Mental_Stress_and_Coping_Mechanisms.csv"))
    dfs.append(load_depression("/Users/danzhou/Downloads/5120dataset/student_depression_dataset.csv"))
    dfs.append(load_mobile("/Users/danzhou/Downloads/5120dataset/Impact_of_Mobile_Phone_on_Students_Health.csv"))
    dfs.append(load_global("/Users/danzhou/Downloads/5120dataset/global_mental_health_dataset.csv"))
    dfs.append(load_generic("/Users/danzhou/Downloads/5120dataset/Mental_Health_Dataset.csv"))

    combined = pd.concat(dfs, ignore_index=True)
    print("✅ Combined shape:", combined.shape)

    
    engine = create_engine("sqlite:///app.db")
    combined.to_sql("student_wide", engine, if_exists="replace", index=False)
    print("✅ Saved to app.db (student_wide table)")


if __name__ == "__main__":
    run_all()
