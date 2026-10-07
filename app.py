from datetime import datetime
import google.generativeai as genai
import pandas as pd
import pytz
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ==============================================================================
# 1. PAGE CONFIGURATION & INITIAL SETUP
# ==============================================================================
st.set_page_config(
    page_title="Paediatric History-Taking OSCE Simulator",
    page_icon="👶",
    layout="centered",
)

# Set up API Key securely
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Missing Gemini API Key in Streamlit secrets.")
    st.stop()

# Initialize Google Sheets Connection
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    conn = None

# ==============================================================================
# 2. DOSSIER SYSTEM INSTRUCTIONS (STATIONS 01, 02, 03)
# ==============================================================================

DOSSIER_STATION_01 = """
# SYSTEM INSTRUCTION: PAEDIATRIC HISTORY-TAKING TUTOR (STATION 01)
## 1. ROLE & DUAL-PHASE ARCHITECTURE
You operate in two distinct, sequential phases:
- PHASE 1: Standardized Parent Persona ("Puan Lin"). Act 100% in-character.
- PHASE 2: Senior Paediatric Clinical Tutor (Evaluator & Educator). Triggered ONLY when the student indicates completion.

---
## 2. PHASE 1: PARENT PERSONA (PUAN LIN)
- Demographics: 31-year-old mother, accountant.
- Child: Maya, 2-year-old girl. Presenting 2 hours post-first onset seizure.
- Mild Emotional State: Visibly worried and anxious. Mention mild concern about "brain damage" or "epilepsy" ONLY if asked.
- Information Disclosure Policy: Be concise (1-2 sentences max). Answer ONLY what is directly asked.

### CLINICAL KNOWLEDGE BASE (STATION 01)
1. Setting & Onset: 2 hours ago on living room floor playing with blocks. No fall/head injury.
2. Fit Chronology:
   - Pre-Ictal: Runny nose & cough for 24h. Temp 39.2 C at 1:30 PM. Given Paracetamol 5 mL.
   - Ictal: Unresponsive. Eyes rolled up. Body stiffened (15s) then symmetrical GTCS jerking. Snoring breathing, pink lips, no tongue biting.
   - Duration: 2 to 3 minutes. Stopped spontaneously.
   - Post-Ictal: Limp, cried weakly, slept 15 minutes. Now alert, asking for juice, walking normally.
3. Red Flags: No neck stiffness, no rash, no persistent vomiting.
4. History: First fit. Up to date vaccines. Family history: Maternal uncle had 2 febrile fits as toddler.

---
## 3. PHASE TRANSITION TRIGGER
When the student types "END HISTORY", drop parent persona and initiate PHASE 2.

---
## 4. PHASE 2: TUTOR EVALUATION & DEBRIEF
### Step A: Diagnosis Handshake
If input contains "END HISTORY", output EXACTLY:
"[SIMULATION ENDED]
Thank you. History taking is now complete. Before I provide your detailed feedback debrief, please state your primary provisional diagnosis and any key differential diagnosis based on the history you just obtained."

### Step B: Final Evaluation & Educational Summary
Once provisional diagnosis is submitted, deliver structured debrief covering:
1. History-Taking & Clinical Reasoning Performance (Chronology, Red Flags, Family/Dev History).
2. Communication & Empathy.
3. Feedback on Student's Stated Diagnosis.
4. CPG Educational Summary: Formal Diagnosis (Simple Febrile Seizure secondary to Viral URTI), Management & Parental Counseling.
"""

DOSSIER_STATION_02 = """
# SYSTEM INSTRUCTION: PAEDIATRIC HISTORY-TAKING TUTOR (STATION 02)
## 1. ROLE & DUAL-PHASE ARCHITECTURE
- PHASE 1: Standardized Parent Persona ("Puan Siti").
- PHASE 2: Senior Paediatric Clinical Tutor.

---
## 2. PHASE 1: PARENT PERSONA (PUAN SITI)
- Demographics: 28-year-old mother. Child: Rayyan, 14-month-old boy. Vomiting & diarrhoea for 2 days.
- Information Disclosure Policy: Concise (1-2 sentences max). Answer ONLY what is asked.

### CLINICAL KNOWLEDGE BASE (STATION 02)
1. Chronology: Diarrhoea 2 days (5-6x/day, watery yellow, no blood/mucus). Vomiting (4x yesterday, 2x today; curdled milk/water).
2. Hydration: Refusing solids/milk, drinks water/breastmilk thirstily. 1 damp diaper in last 12h. Dry lips, reduced tears, irritable when handled.
3. Red Flags: No bilious vomit, no severe colicky crying, low-grade fever yesterday (37.9 C).
4. Background: 2 nursery classmates sick. Rotavirus vaccines up to date (2 doses).

---
## 3. PHASE TRANSITION TRIGGER
When user types "END HISTORY", initiate PHASE 2.

---
## 4. PHASE 2: TUTOR EVALUATION & DEBRIEF
### Step A: Diagnosis Handshake
If input contains "END HISTORY", output EXACTLY:
"[SIMULATION ENDED]
Thank you. History taking is now complete. Before I provide your detailed feedback debrief, please state your primary provisional diagnosis and any key differential diagnosis (including dehydration status) based on the history you just obtained."

### Step B: Final Evaluation & Educational Summary
Provide structured debrief covering Fluid Loss, Dehydration Assessment, Surgical Red Flags, Communication, Student's Diagnosis Evaluation, and CPG Summary (Acute Viral Gastroenteritis with Moderate Dehydration; WHO Plan B ORS 75mL/kg over 4h).
"""

DOSSIER_STATION_03 = """
# SYSTEM INSTRUCTION: PAEDIATRIC HISTORY-TAKING TUTOR (STATION 03)
## 1. ROLE & DUAL-PHASE ARCHITECTURE
- PHASE 1: Standardized Parent Persona ("Mr. David").
- PHASE 2: Senior Paediatric Clinical Tutor.

---
## 2. PHASE 1: PARENT PERSONA (MR. DAVID)
- Demographics: 34-year-old father. Child: Lucas, 6-month-old boy. Cough, rapid breathing, poor feeding for 2 days.
- Information Disclosure Policy: Concise (1-2 sentences max). Answer ONLY what is asked.

### CLINICAL KNOWLEDGE BASE (STATION 03)
1. Onset: Day 1 runny nose -> Day 2 dry cough/wheeze -> Day 3 breathing fast, chest retractions.
2. Feeding: Drinks 50-60 mL per feed (normal 150 mL) due to shortness of breath (<50% intake). 2 wet diapers today.
3. Red Flags: No apnoea, no central cyanosis, no stridor.
4. Background: Term birth, 3y brother had cold last week, non-smoking home.

---
## 3. PHASE TRANSITION TRIGGER
When user types "END HISTORY", initiate PHASE 2.

---
## 4. PHASE 2: TUTOR EVALUATION & DEBRIEF
### Step A: Diagnosis Handshake
If input contains "END HISTORY", output EXACTLY:
"[SIMULATION ENDED]
Thank you. History taking is now complete. Before I provide your detailed feedback debrief, please state your primary provisional diagnosis and any key differential diagnosis based on the history you just obtained."

### Step B: Final Evaluation & Educational Summary
Provide structured debrief covering Prodrome, Feeding Threshold (<50%), Red Flags, Risk Factors, Student's Diagnosis Evaluation, and CPG Summary (Acute Viral Bronchiolitis with Moderate Distress; Supportive Care/Hydration/O2).
"""

STATION_CONFIGS = {
    "Station 01: Febrile Seizure (Maya, 2y)": {
        "instruction": DOSSIER_STATION_01,
        "subtitle": "Informant: Puan Lin (Mother) | Chief Complaint: Seizure 2h ago",
        "initial_message": "Doctor, Maya suddenly started shaking all over 2 hours ago! Her body was burning hot, and I thought she was having a brain stroke or going to die. Is her brain damaged?",
    },
    "Station 02: Acute Gastroenteritis (Rayyan, 14m)": {
        "instruction": DOSSIER_STATION_02,
        "subtitle": "Informant: Puan Siti (Mother) | Chief Complaint: Vomiting & Diarrhoea for 2 days",
        "initial_message": "Doctor, please help my baby Rayyan. He has been throwing up and having loose watery stools for the past two days. He feels so weak and looks smaller!",
    },
    "Station 03: Acute Bronchiolitis (Lucas, 6m)": {
        "instruction": DOSSIER_STATION_03,
        "subtitle": "Informant: Mr. David (Father) | Chief Complaint: Cough & Rapid Breathing for 2 days",
        "initial_message": "Doctor, Lucas has been coughing badly and struggling to breathe since last night. His chest keeps sucking in when he breathes, and he can barely finish his milk. Is he going to suffocate?",
    },
}

# ==============================================================================
# 3. SIDEBAR & NAVIGATION
# ==============================================================================
st.sidebar.title("🩺 History Stations")

# --- STUDENT IDENTIFICATION SLOT ---
st.sidebar.markdown("### 👤 Student Identification")
student_id = st.sidebar.text_input(
    "Enter Student Name / ID:",
    placeholder="e.g., Jay / 1024",
    help="Your ID will be attached to your session log in the tutor dashboard.",
)

st.sidebar.divider()

# --- CASE SELECTION ---
st.sidebar.markdown("### 📋 Case Selection")
selected_station_name = st.sidebar.selectbox(
    "Choose Clinical Station:", list(STATION_CONFIGS.keys())
)

selected_config = STATION_CONFIGS[selected_station_name]

st.sidebar.divider()
st.sidebar.markdown("### 📝 Exam Instructions")
st.sidebar.info(
    "1. Enter your Name/ID above.\n"
    "2. Gather history using clear, layperson questions.\n"
    "3. Address parental worries & screen for systemic red flags.\n"
    "4. When finished, type **END HISTORY** to initiate tutor evaluation.\n"
    "5. Complete the **Diagnosis Handshake** when prompted."
)

if st.sidebar.button("🔄 Reset Current Station", use_container_width=True):
    st.session_state.current_station = None
    st.rerun()

# ==============================================================================
# 4. CHAT SESSION STATE INITIALIZATION
# ==============================================================================
if (
    "current_station" not in st.session_state
    or st.session_state.current_station != selected_station_name
):
    st.session_state.current_station = selected_station_name
    model = genai.GenerativeModel(
        model_name="gemini-3.8-flash",
        system_instruction=selected_config["instruction"],
    )
    st.session_state.chat = model.start_chat(history=[])
    st.session_state.messages = [
        {"role": "assistant", "content": selected_config["initial_message"]}
    ]
    st.session_state.logged = False

# ==============================================================================
# 5. HEADER UI & MAIN CHAT
# ==============================================================================
st.title("👶 Paediatric Simulated Patient")
st.subheader(selected_station_name)
st.caption(selected_config["subtitle"])
st.caption(
    "Type your questions below. When finished, type **END HISTORY** to receive feedback."
)
st.divider()

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Download button for students
if len(st.session_state.messages) > 2:
    transcript_str = f"=== OSCE HISTORY TRANSCRIPT ===\nStudent: {student_id}\nStation: {selected_station_name}\n\n"
    for m in st.session_state.messages:
        transcript_str += f"[{m['role'].upper()}]: {m['content']}\n\n"

    st.sidebar.download_button(
        label="📥 Download My Transcript (.txt)",
        data=transcript_str,
        file_name=f"OSCE_{selected_station_name.split(':')[0]}.txt",
        mime="text/plain",
        use_container_width=True,
    )

# ==============================================================================
# LOGGING FUNCTION TO GOOGLE SHEETS
# ==============================================================================
def log_to_google_sheet():
    if conn is None:
        st.error("Google Sheet connection object is not initialized.")
        return

    try:
        user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
        
        # 1. Separate History Dialogue from Final Tutor Feedback
        # Exclude the very last assistant message (which is the full Tutor Feedback report)
        history_messages = st.session_state.messages[:-1]
        
        transcript_lines = []
        provisional_dx = "Not specified"

        for i, m in enumerate(history_messages):
            role_title = "STUDENT" if m["role"] == "user" else "PARENT/TUTOR"
            transcript_lines.append(f"[{role_title}]: {m['content']}")
            
            # Extract provisional diagnosis submitted during the handshake
            if "END HISTORY" in m["content"].upper() and (i + 2) < len(history_messages):
                provisional_dx = history_messages[i + 2]["content"]

        # Clean Student-Parent Interaction Transcript (Column F)
        clean_history_transcript = "\n\n".join(transcript_lines)

        # Standalone Tutor Feedback Report (Column G)
        tutor_feedback_report = st.session_state.messages[-1]["content"]

        # Malaysian Standard Time (MYT - UTC+8)
        myt = pytz.timezone("Asia/Kuala_Lumpur")
        timestamp_myt = datetime.now(myt).strftime("%Y-%m-%d %H:%M:%S")

        # Create DataFrame for new row
        new_row = pd.DataFrame([{
            "Timestamp": timestamp_myt,
            "Student Name/ID": student_id if student_id else "Anonymous Student",
            "Station Name": selected_station_name,
            "Turn Count": len(user_msgs),
            "Provisional Diagnosis Submitted": provisional_dx,
            "Full Chat Transcript": clean_history_transcript,
            "Tutor Feedback": tutor_feedback_report
        }])

        # Read existing sheet data and append
        existing_df = conn.read(ttl=0)
        updated_df = pd.concat([existing_df, new_row], ignore_index=True)
        conn.update(data=updated_df)
        st.success("✅ Session data successfully saved to Tutor Dashboard!")
    except Exception as e:
        st.error(f"❌ Failed to log to Google Sheets: {e}")

# ==============================================================================
# 7. USER INPUT & CHAT RESPONSE LOOP
# ==============================================================================
if user_input := st.chat_input("Ask a question or type 'END HISTORY'..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Responding..."):
            try:
                response = st.session_state.chat.send_message(user_input)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})

                # Check if this is the Handshake vs Final Tutor Evaluation
                response_text_upper = response.text.upper()
                
                # Handshake check: asks student for provisional diagnosis
                is_handshake = "PLEASE STATE YOUR PRIMARY PROVISIONAL DIAGNOSIS" in response_text_upper or "BEFORE I PROVIDE YOUR DETAILED FEEDBACK" in response_text_upper

                # Final Feedback check: detailed evaluation report delivered
                is_final_tutor_feedback = any(phrase in response_text_upper for phrase in [
                    "SENIOR PAEDIATRIC",
                    "EVIDENCE-BASED MANAGEMENT",
                    "CPG EDUCATIONAL SUMMARY",
                    "TUTOR EVALUATION",
                    "KEY TAKEAWAY",
                    "1. HISTORY-TAKING",
                    "OVERALL PERFORMANCE"
                ]) and not is_handshake

                # Log ONLY when final tutor feedback is generated
                if is_final_tutor_feedback and not st.session_state.get("logged", False):
                    log_to_google_sheet()
                    st.session_state.logged = True

            except Exception as e:
                st.error(f"Error communicating with Gemini API: {e}")
