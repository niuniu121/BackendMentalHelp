-- SQL Script for Database
-- Description: Defines schema and indices for backend database

CREATE TABLE flip_card (
    id INTEGER NOT NULL,
    negative_text TEXT NOT NULL,
    positive_text TEXT NOT NULL,
    tag VARCHAR(32),
    PRIMARY KEY (id)
);
CREATE INDEX ix_flip_card_id ON flip_card (id);

CREATE TABLE tip (
    id INTEGER NOT NULL,
    text TEXT NOT NULL,
    mood_tag VARCHAR(32),
    PRIMARY KEY (id)
);
CREATE INDEX ix_tip_id ON tip (id);

CREATE TABLE IF NOT EXISTS Health_impact (
    id INTEGER NOT NULL,
    useful_features VARCHAR(255),
    health_risks VARCHAR(255),
    beneficial_subject VARCHAR(255),
    usage_symptoms VARCHAR(255),
    symptom_frequency VARCHAR(255),
    health_precaution VARCHAR(255),
    PRIMARY KEY (id)
);
CREATE INDEX ix_Health_impact_useful_features     ON Health_impact (useful_features);
CREATE INDEX ix_Health_impact_symptom_frequency   ON Health_impact (symptom_frequency);
CREATE INDEX ix_Health_impact_id                  ON Health_impact (id);
CREATE INDEX ix_Health_impact_health_precaution   ON Health_impact (health_precaution);
CREATE INDEX ix_Health_impact_health_risks        ON Health_impact (health_risks);
CREATE INDEX ix_Health_impact_usage_symptoms      ON Health_impact (usage_symptoms);
CREATE INDEX ix_Health_impact_beneficial_subject  ON Health_impact (beneficial_subject);

CREATE TABLE IF NOT EXISTS coping (
    age INTEGER,
    gender TEXT,
    mental_stress_level INTEGER,
    stress_coping_mechanisms TEXT,
    sleep_duration_hours_per_night INTEGER,
    sleep_hours INTEGER,
    coping_strategy_simple TEXT
);

CREATE TABLE IF NOT EXISTS depression (
    age INTEGER,
    gender TEXT,
    city TEXT,
    sleep_duration TEXT,
    academic_pressure INTEGER,
    work_pressure INTEGER,
    financial_stress REAL,
    depression INTEGER,
    sleep_hours REAL
);

CREATE TABLE IF NOT EXISTS lifestyle (
    country TEXT,
    age INTEGER,
    gender TEXT,
    sleep_hours REAL,
    stress_level TEXT
);

CREATE TABLE student_wide (
    source TEXT,
    country TEXT,
    age TEXT,
    gender TEXT,
    exercise_level FLOAT,
    diet_type TEXT,
    sleep_hours FLOAT,
    stress_level FLOAT,
    mental_condition TEXT,
    work_hours FLOAT,
    screen_time FLOAT,
    social_interaction FLOAT,
    happiness_score FLOAT,
    gpa FLOAT,
    study_hours FLOAT,
    social_media_hours FLOAT,
    exercise_hours FLOAT,
    family_support FLOAT,
    financial_stress FLOAT,
    peer_pressure FLOAT,
    relationship_stress FLOAT,
    mental_stress FLOAT,
    counseling FLOAT,
    diet_quality FLOAT,
    cognitive_distortions FLOAT,
    family_history FLOAT,
    medical_condition FLOAT,
    substance_use FLOAT,
    id FLOAT,
    city TEXT,
    profession TEXT,
    academic_pressure FLOAT,
    work_pressure FLOAT,
    cgpa FLOAT,
    study_satisfaction FLOAT,
    job_satisfaction FLOAT,
    dietary_habits TEXT,
    degree TEXT,
    suicidal_thoughts FLOAT,
    work_study_hours FLOAT,
    depression FLOAT,
    mobile_use_hours FLOAT,
    performance_impact FLOAT,
    attention_span FLOAT,
    health_risks FLOAT,
    symptoms TEXT,
    symptom_freq TEXT,
    user_id FLOAT,
    occupation TEXT,
    severity FLOAT,
    consultation_history FLOAT,
    treatment FLOAT,
    days_indoors FLOAT,
    growing_stress FLOAT,
    changes_habits FLOAT,
    mental_history FLOAT,
    mood_swings FLOAT,
    coping_struggles FLOAT,
    work_interest FLOAT,
    social_weakness FLOAT
);
