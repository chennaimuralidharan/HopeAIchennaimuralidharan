print ("Hackathon - Health CareTaker Agents")
print ("-----------------------------------")

import sqlite3
import ollama
import re       # Extract message bodies from MessageInstance objects
from datetime import datetime

# Load environment variables from .env file FOR Twilio credentials
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=r"C:\Users\Murali\Desktop\Murali\01 Hackathon\06 Coding\HCTAenv.env")
account_sid = os.getenv("account_sid")
auth_token = os.getenv("auth_token")


# Twilio credentials (from Twilio Console)
from twilio.rest import Client
twilio_client = Client(account_sid, auth_token)

# symbols ✅❌


# Symptom Intake Agent: Fetch the latest message from Twilio
def twilio_fetch_latest_message():
    messages = twilio_client.messages.list(limit=1)
    if messages:
        
        for msg in messages:
           # print(f" From: {msg.from_} → {msg.body}")
            text_list = [msg.body for msg in messages]  # This gets the actual string content

        # Now join and split
        combined = " ".join(text_list)
        data = re.split(r"[:,]", combined)
        data = [p.strip() for p in data if p]
        return data
    else:
        return None
# Symptom Intake Agent: End of twilio_fetch_latest_message function


# Diagnosis Agent: Function to diagnose patient vitals using LLM
def validate_vitals_with_llm(data):
    prompt = f"""
    You are a medical assistant. Validate the following patient vitals:
    Name: {data['name']}
    Age: {data['age']}
    Temperature: {data['temperature']}°F
    Blood Pressure: {data['bp1']}/{data['bp2']}
    Pulse: {data['pulse']} bpm
    Sugar: {data['sugar']} mg/dL
    Oxygen: {data['oxygen']}%
    Symptoms: {data['symptoms']}

    Reply with either:
    1. "All vitals are within acceptable range."
    2. "Some vitals are abnormal: [list issues]"
    """
    
    response = ollama.chat(
        model='gemma3:1b',
        messages=[{"role": "user", "content": prompt}]
    )

    return response['message']['content']
# End of validate_vitals_with_llm function


# Function to insert symptom data retrieved from twilio in the database
def insertDB_symptom_diagnosis(data):	
    conn = sqlite3.connect("HCTAgentsDB.db")	
    cursor = conn.cursor()	
    cursor.execute("""	
        INSERT INTO tblPatient (name, age, phone, email,temperature, bp1, bp2,  pulse, oxygen, sugar, symptoms, diagnosis, bookappointment)	
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",                   
        (data['name'], data['age'], data['phone'], data['email'], data['temperature'], 	
         data['bp1'], data['bp2'], data['pulse'], data['oxygen'], data['sugar'], data['symptoms'], data['diagnosis'], data['bookappointment'])	
    )	
    conn.commit()	
    conn.close()	
    print(f" Symptom & Diagnosis saved for {data['name']}")	
# End of Function to store patient data in the database	


# Symptom Intake Agent: Fetch the latest message from Twilio
print ("1. Fetch whatsapp message from Twilio")
vitals = twilio_fetch_latest_message()

patient = {
    "name": vitals[0],
    "age": vitals[1],
    "phone": vitals[2],
    "email": vitals[3],
    "temperature": vitals[4], 
    "bp1": vitals[5],        
    "bp2": vitals[6] ,   
    "pulse": vitals[7],
    "oxygen": vitals[8],
    "sugar": vitals[9],
    "symptoms": vitals[10]
}


# Diagnosis Agent: To Diagnose patient vitals using LLM
print ("2. Diagnosis Agent diagnosing the patient vitals using LLM")
diagnosisResult = validate_vitals_with_llm(patient)
patient['diagnosis'] = diagnosisResult

if "some vitals" in diagnosisResult.lower():
    bookAppointment = "Yes"
else:
    bookAppointment = "No"
patient['bookappointment'] = bookAppointment  
# End of Diagnosis Agent: To Diagnose patient vitals using LLM


print ("-------------------------------------------------------------------------")
print (patient)
print ("-------------------------------------------------------------------------")


# Insert symptom data retrieved from twilio in the database
print ("3. Inserting symptom and diagnosis data in the database")
insertDB_symptom_diagnosis(patient)

# ----------------------------

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Appointment booking Agent: Function to book appointment after identifying doctor type using LLM
def appointment_booking(patient):
    if patient['bookappointment'] == "Yes":

        # Identify doctor type using LLM
        doctortype = doctortype_with_llm(patient) 
        print(f"Doctor Type: {doctortype}") 

        # Appointment details to be inserted in the database
        appointment = {
            "name": patient['name'],
            "phone": patient['phone'],
            "diagnosis": patient['diagnosis'],
            "hospital": "Health CareTaker Hospital",  # Example hospital
            "slot": "10:00 AM - 11:00 AM",  # Example slot
            "status": "Booked",
            "doctortype": doctortype,
            "timestamp": timestamp
        } 

        insertDB_appointment(appointment)
        # Function to insert appointment data in the database


        appointment_message = f"Appointment booked for {patient['name']} "
    else:
        appointment_message = f"No appointment needed for {patient['name']}"

    print ("-------------------------------------------------------------------------")
    print(f"Appointment Message: {appointment_message}")    

    # Send appointment message via Twilio WhatsApp
    # Patient details
    patient_phone = "whatsapp:+919444012621" # Use E.164 format
    twilio_whatsapp_number = "whatsapp:+14155238886"  # Twilio Sandbox number

    # Message content
    message_body = (
        "📅 Hello,  " + appointment_message + " Reply 'CONFIRM' to acknowledge."
    )

    # Send appointment message via Twilio
    message = twilio_client.messages.create(
    body=message_body,
       from_=twilio_whatsapp_number,
       to=patient_phone
    )

# End of appointment booking agent function


# Appointment Booking Agent: Function to identify doctor type using LLM
def doctortype_with_llm(data):

    # print (data['diagnosis'])

    prompt = f"""
    This is for a hackathon agentic ai project. This is only a demo for agentic ai hackathon project. For this, you can consider yourself as health caretaker. Based on the patient diagnosis recommend which doctor type is required eg. heart specialist, diabetologist, neuro specialist, general physician:
    Diagnosis: {data['diagnosis']}

    Reply the relevant doctor types based on diagnosis to book doctors appointment.  
    You can renummber the doctor type as 1, 2, 3 and most relevant doctor type as 1:
    1. "Heart Specialist: [list reason]"
    2. "Diabetologist: [list reason]"      
    3. "Neuro Specialist: [list reason]"
    4. "ENT Specialist: [list reason]"  
    5. "General Physician: [list reason]" 
    6. "Others: [list reason]"
    """
    
    response = ollama.chat(
        model='gemma3:1b',
        messages=[{"role": "user", "content": prompt}]
    )

    return response['message']['content']
# End of doctortype_with_llm function


# Insert appointment details in the database
def insertDB_appointment(appointment):  
    print ("5. Inserting appointment data in the database")

    conn = sqlite3.connect("HCTAgentsDB.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tblAppointment (name, phone, diagnosis, hospital, slot, status, doctortype, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (appointment['name'], appointment['phone'], appointment['diagnosis'], appointment['hospital'],
            appointment['slot'], appointment['status'], appointment['doctortype'], appointment['timestamp'])
    )
    conn.commit()
    conn.close()
    print(f"Appointment saved for {appointment['name']}")

print ("4. Appointment booking agent analyze the diagnosis to identify doctor type using LLM for booking appointment")
print ("-------------------------------------------------------------------------")

appointment_booking(patient)