import streamlit as st
import fitz  # PyMuPDF
from groq import Groq
from pymongo import MongoClient
from datetime import datetime
import io

# Initialize the Groq client
client = Groq(api_key='Enter Your__API key')  # Replace with your actual API key

# Initialize MongoDB Client
mongo_client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB connection string
db = mongo_client["pdf_history_db"]
pdf_collection = db["pdf_files"]

def store_pdf_in_db(file, text):
    file_id = pdf_collection.insert_one({
        "filename": file.name,
        "upload_date": datetime.now(),
        "content": text,
        "summaries": [],
        "questions": []
    }).inserted_id
    return file_id

def save_summary(file_id, summary):
    pdf_collection.update_one({"_id": file_id}, {"$push": {"summaries": summary}})

def save_question(file_id, question, answer):
    pdf_collection.update_one({"_id": file_id}, {"$push": {"questions": {"question": question, "answer": answer}}})

def get_pdf_history():
    return pdf_collection.find()

def delete_pdf_history():
    pdf_collection.delete_many({})  # Deletes all documents in the collection

def extract_text_from_pdf(uploaded_file):
    try:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        st.error(f"Error reading the PDF file: {e}")
        return ""

def summarize_text(text):
    try:
        summary_response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Summarize the following text: {text}"}
            ],
            model="llama-3.1-8b-instant",
        )
        return summary_response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {e}"

def ask_question(context, question):
    try:
        answer_response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Context: {context} Question: {question}"}
            ],
            model="llama-3.1-8b-instant",
        )
        return answer_response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {e}"

# Streamlit UI
#st.title("PDF Summarizer and Question Answering with History")

st.markdown("<h1 style='color: green;'>Chatty Llama Assistant</h1>", unsafe_allow_html=True)

# Add an image to the app
image_path = 'C:\\Users\W10-Dell\Desktop\pythonProject1\Docs\AI_PIC_2.png'  # Replace with your image file path
#image_path = "path_to_your_image.png"  # Update this to your actual image path
st.image(image_path, caption="Using FaceBook's Llama models to summarise and question a pdf", use_column_width=True)

uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file is not None:
    pdf_text = extract_text_from_pdf(uploaded_file)

    st.subheader("Text Extracted from PDF:")
    st.write(pdf_text[:500])  # Display a snippet of the text for review

    # Store PDF and get its ID
    file_id = store_pdf_in_db(uploaded_file, pdf_text)

    # Button to summarize the extracted text
    summary_button = st.button("Summarize Text")
    if summary_button:
        summary = summarize_text(pdf_text)
        st.subheader("Summary:")
        st.write(summary)
        save_summary(file_id, summary)

    # Text input for asking questions
    question = st.text_input("Ask a question about the PDF:")
    if question:
        answer = ask_question(pdf_text, question)
        st.subheader("Answer:")
        st.write(answer)
        save_question(file_id, question, answer)

# Display History
st.sidebar.title("History")
for pdf in get_pdf_history():
    st.sidebar.write(f"**{pdf['filename']}** - {pdf['upload_date']}")
    st.sidebar.write("Summaries:")
    for summary in pdf["summaries"]:
        st.sidebar.write(f"- {summary}")
    st.sidebar.write("Questions:")
    for q in pdf["questions"]:
        st.sidebar.write(f"- Q: {q['question']}\n  A: {q['answer']}")
# Button to delete history
if st.sidebar.button("Delete History"):
    delete_pdf_history()
    st.sidebar.write("History deleted successfully.")
