import streamlit as st
import numpy as np
import joblib
import random
import io
from datetime import datetime

# -------- PDF IMPORTS (UPDATED) --------
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="ASD Screening",
    page_icon="🧠",
    layout="centered"
)

# --------------------------------------------------
# CSS
# --------------------------------------------------
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}

.block-container {
    max-width: 420px;
    padding-top: 1.5rem;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0px 8px 20px rgba(0,0,0,0.08);
    margin-bottom: 22px;
}

.advice {
    background-color: #f5f7fa;
    padding: 15px;
    border-radius: 12px;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------
model = joblib.load("autism_rf_highprob.pkl")

# --------------------------------------------------
# SESSION STATE INIT
# --------------------------------------------------
if "step" not in st.session_state:
    st.session_state.step = 1

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown("""
<h3 style="text-align:center;">🧠 Autism Spectrum Disorder Screening</h3>
<p style="text-align:center;color:gray;font-size:13px;">
Educational screening tool — Not a medical diagnosis
</p>
""", unsafe_allow_html=True)

# ==================================================
# SCREEN 1 — BASIC DETAILS
# ==================================================
if st.session_state.step == 1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.session_state.child_name = st.text_input("Child / Applicant Name")
    st.session_state.age = st.slider("Age", 1, 100, 18)
    st.session_state.gender = st.selectbox("Gender", ["Male", "Female"])
    st.session_state.ethnicity = st.selectbox(
        "Ethnicity", ["Asian", "White-European", "Latino", "Black", "Others"]
    )
    st.session_state.jaundice = st.selectbox("Had jaundice at birth?", ["Yes", "No"])
    st.session_state.family_history = st.selectbox("Family member with autism?", ["Yes", "No"])
    st.session_state.used_app_before = st.selectbox("Used screening app before?", ["Yes", "No"])
    st.session_state.relation = st.selectbox(
        "Who completed the test?",
        ["Self", "Parent", "Relative", "Health care professional", "Others"]
    )
    st.session_state.country = st.selectbox("Country", ["India", "USA", "UK", "Others"])
    st.session_state.age_desc = st.selectbox("Age category", ["18 and more", "Less than 18"])

    if st.button("Next ➡️"):
        st.session_state.step = 2

    st.markdown("</div>", unsafe_allow_html=True)

# ==================================================
# SCREEN 2 — A1 TO A10
# ==================================================
elif st.session_state.step == 2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    questions = [
        "Looks at you when you call their name?",
        "Easy to get eye contact?",
        "Points to indicate they want something?",
        "Points to share interest with you?",
        "Pretends (e.g. plays house)?",
        "Follows where you’re looking?",
        "Comforts when someone is upset?",
        "First words were unusual?",
        "Uses simple gestures?",
        "Stares at nothing with no purpose?"
    ]

    for i, q in enumerate(questions, start=1):
        st.session_state[f"A{i}"] = st.radio(
            f"A{i}: {q}", [0, 1], horizontal=True
        )

    if st.button("Get Result 🔍"):
        st.session_state.step = 3

    st.markdown("</div>", unsafe_allow_html=True)

# ==================================================
# SCREEN 3 — RESULT + PDF + RESTART
# ==================================================
elif st.session_state.step == 3:

    # ---------- FEATURE ENCODING ----------
    gender = 1 if st.session_state.gender == "Male" else 0
    jaundice = 1 if st.session_state.jaundice == "Yes" else 0
    family = 1 if st.session_state.family_history == "Yes" else 0
    used = 1 if st.session_state.used_app_before == "Yes" else 0
    age_desc = 1 if st.session_state.age_desc == "18 and more" else 0

    input_features = np.array([[ 
        st.session_state[f"A{i}"] for i in range(1, 11)
    ] + [
        gender,
        hash(st.session_state.ethnicity) % 100,
        jaundice,
        family,
        used,
        st.session_state.age,
        age_desc,
        hash(st.session_state.relation) % 100,
        hash(st.session_state.country) % 100
    ]])

    prediction = model.predict(input_features)[0]
    probability = model.predict_proba(input_features)[0][1] * 100

    severity = (
        "Low Risk" if probability < 35
        else "Moderate Risk" if probability < 65
        else "High Risk"
    )

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📊 Screening Result")

    st.write(f"**Name:** {st.session_state.child_name}")
    st.write(f"**Probability:** {probability:.2f}%")
    st.write(f"**Severity Level:** {severity}")

    if prediction == 1:
        result_text = "Autistic traits may be present"
        st.error(result_text)

        guidance = (
            "Early intervention is strongly recommended. "
            "Speech therapy, occupational therapy, behavioral therapy "
            "and professional consultation can improve outcomes."
        )
    else:
        result_text = "Lower likelihood of autistic traits"
        st.success(result_text)

        guidance = random.choice([
            "Different, not less.",
            "Neurodiversity is a strength.",
            "Awareness creates acceptance."
        ])

    st.markdown(f"<div class='advice'>{guidance}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ==================================================
    # ✅ FIXED PDF GENERATION (NO OVERFLOW)
    # ==================================================
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(
        "<b>Autism Spectrum Disorder Screening Report</b>",
        styles["Title"]
    ))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph(f"<b>Name:</b> {st.session_state.child_name}", styles["Normal"]))
    story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d-%m-%Y')}", styles["Normal"]))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph(f"<b>Age:</b> {st.session_state.age}", styles["Normal"]))
    story.append(Paragraph(f"<b>Gender:</b> {st.session_state.gender}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph(f"<b>Result:</b> {result_text}", styles["Normal"]))
    story.append(Paragraph(f"<b>Probability:</b> {probability:.2f}%", styles["Normal"]))
    story.append(Paragraph(f"<b>Severity Level:</b> {severity}", styles["Normal"]))
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("<b>Guidance:</b>", styles["Normal"]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(guidance, styles["Normal"]))

    doc.build(story)
    buffer.seek(0)

    st.download_button(
        "📄 Download PDF Report",
        buffer,
        "ASD_Screening_Report.pdf",
        "application/pdf"
    )

    # ---------- SAFE RESTART ----------
    if st.button("🔁 Restart Screening"):
        st.session_state.clear()
        st.session_state.step = 1
