import streamlit as st
import pandas as pd
from streamlit_mic_recorder import speech_to_text
import openai
from gtts import gTTS
from io import BytesIO

# Load API key
openai.api_key = open("api_key.txt", "r").read().strip()

# Load CSV dataset
df = pd.read_csv('interview_questions.csv')
domains = df['Domain'].unique()

def text_to_audio(text):
    tts = gTTS(text=text, lang='en')
    audio_bytes = BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    return audio_bytes

def play_audio(audio_bytes):
    st.audio(audio_bytes, format='audio/mp3')

st.title("Interviewer AI")
st.markdown("""
Hi!! Welcome to the **AI Interviewer**!  
Choose Your Domain and Attend the Interview to find your accuracy, completeness and clarity 
""")

# Initialize session state for question index, domain, and answers
if 'question_index' not in st.session_state:
    st.session_state.question_index = -1
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'domain' not in st.session_state:
    st.session_state.domain = None

def next_question():
    st.session_state.question_index += 1

# Domain selection
if st.session_state.domain is None:
    st.markdown("### Select a Domain")
    selected_domain = st.selectbox("Choose a domain", options=domains)
    if st.button("Start the interview"):
        st.session_state.domain = selected_domain
        next_question()
        st.rerun()

# Interview in progress
if st.session_state.domain and st.session_state.question_index >= 0:
    questions = df[df['Domain'] == st.session_state.domain]['Questions'].tolist()
    
    if st.session_state.question_index < len(questions):
        question = questions[st.session_state.question_index]
        st.markdown("### Question: ")
        st.info(question)

        # Convert question to audio and play it
        audio_bytes = text_to_audio(question)
        play_audio(audio_bytes)

        st.markdown("#### Your Answer:")
        text = speech_to_text(language='en', use_container_width=True, just_once=True, key='STT')

        if text:
            st.session_state.answers.append(text)
            st.text_area("Your Answer So Far:", value=st.session_state.answers[-1], height=100)

        submit = st.button("Submit Your Answer")

        if submit:
            next_question()
            st.rerun()
    else:
        st.markdown("### Interview Completed!")
        st.markdown("You have answered all the questions. Generating feedback...")

        with st.spinner('Waiting for feedback...'):
            feedback_summary = []
            for i, answer in enumerate(st.session_state.answers):
                prompt = (
                    f"The interview question asked is: '{questions[i]}'. "
                    f"The answer provided was: '{answer}'. "
                    "Could you rate this answer out of 10, and provide detailed feedback on its accuracy, completeness, "
                    "clarity, and how it can be improved?"
                )
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an AI Interviewer, designed to assess and provide feedback on technical questions based on user responses."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                feedback_content = completion.choices[0].message['content']
                feedback_summary.append(f"**Question {i+1}:** {questions[i]}\n\n**Feedback:**\n{feedback_content}\n\n")

        st.success("Analysis Complete!")

        st.markdown("### Detailed Feedback:")
        for feedback in feedback_summary:
            st.markdown(feedback)

        st.markdown("Thank you for participating!")
