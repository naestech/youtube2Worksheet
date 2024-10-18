import os
import random
import re
import string

import nltk
from googleapiclient.discovery import build
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from youtube_transcript_api import YouTubeTranscriptApi

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

YOUTUBE_API_KEY = '***'

def get_video_id(url):
    video_id = re.findall(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return video_id[0] if video_id else None

def get_video_title(video_id):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.videos().list(part='snippet', id=video_id)
    response = request.execute()
    return response['items'][0]['snippet']['title']

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return ' '.join([entry['text'] for entry in transcript])
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def extract_key_terms(text):
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    key_terms = [word for word in words if word.isalnum() and word not in stop_words and len(word) > 3]
    return list(set(key_terms))

def generate_questions(text, key_terms):
    sentences = sent_tokenize(text)
    questions = []
    answers = []

    for _ in range(15):  # Generate 15 questions
        question_type = random.choice(['free_response', 'multiple_choice'])
        sentence = random.choice(sentences)
        
        if question_type == 'free_response':
            question, answer = generate_free_response_question(sentence, key_terms)
        else:
            question, answer = generate_multiple_choice_question(sentence, key_terms, text)
        
        questions.append(question)
        answers.append(answer)
    
    return questions, answers

def generate_free_response_question(sentence, key_terms):
    relevant_terms = [term for term in key_terms if term in sentence.lower()]
    if not relevant_terms:
        question = f"Explain the significance of this statement in the context of the video: '{sentence}'"
        answer = "Answer will vary based on student's understanding of the video content."
    else:
        term = random.choice(relevant_terms)
        question_types = [
            f"How does the concept of '{term}' relate to the main theme of the video?",
            f"What implications does the idea of '{term}' have for our understanding of the world?",
            f"Analyze the role of '{term}' in the broader context of the video's message.",
            f"How does the mention of '{term}' contribute to the speaker's argument?",
            f"Discuss the potential consequences of '{term}' as presented in the video."
        ]
        question = random.choice(question_types)
        answer = "Answer will vary based on student's understanding of the video content and the term's context."
    
    return question, answer

def generate_multiple_choice_question(sentence, key_terms, full_text):
    relevant_terms = [term for term in key_terms if term in sentence.lower()]
    if not relevant_terms:
        return generate_free_response_question(sentence, key_terms)
    
    correct_answer = random.choice(relevant_terms)
    other_terms = [term for term in key_terms if term != correct_answer and term not in sentence.lower()]
    if len(other_terms) < 3:
        return generate_free_response_question(sentence, key_terms)
    
    incorrect_options = random.sample(other_terms, 3)
    options = [correct_answer] + incorrect_options
    random.shuffle(options)
    
    question = f"In the context of the following statement, which term best fits the video's message?\n"
    question += f"'{sentence}'\n"
    for i, option in enumerate(['A', 'B', 'C', 'D']):
        question += f"{option}) {options[i]}\n"
    
    answer = f"Correct answer: {options.index(correct_answer) + 1}) {correct_answer}"
    return question, answer

def create_worksheet(title, questions, output_file):
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    content = []

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=12
    )
    content.append(Paragraph(f"Worksheet for: {title}", title_style))
    content.append(Paragraph("Answer the following questions:", styles['Heading2']))
    content.append(Spacer(1, 12))

    for i, question in enumerate(questions, 1):
        content.append(Paragraph(f"{i}. {question}", styles['Normal']))
        content.append(Spacer(1, 36))  # Add more space for answers

    doc.build(content)

def create_answer_key(title, questions, answers, output_file):
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    content = []

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=12
    )
    content.append(Paragraph(f"Answer Key for: {title}", title_style))
    content.append(Spacer(1, 12))

    for i, (question, answer) in enumerate(zip(questions, answers), 1):
        content.append(Paragraph(f"{i}. {question}", styles['Normal']))
        content.append(Paragraph(f"Answer: {answer}", styles['Normal']))
        content.append(Spacer(1, 12))

    doc.build(content)

def sanitize_filename(filename):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    sanitized = ''.join(c for c in filename if c in valid_chars)
    return sanitized[:255]

def main():
    url = input("Enter the YouTube video URL: ")
    video_id = get_video_id(url)
    
    if not video_id:
        print("Invalid YouTube URL")
        return

    title = get_video_title(video_id)
    transcript = get_transcript(video_id)

    if not transcript:
        print("Couldn't retrieve the transcript. The video might not have subtitles.")
        return

    key_terms = extract_key_terms(transcript)
    questions, answers = generate_questions(transcript, key_terms)
    
    worksheet_file = f"{sanitize_filename(title)}_worksheet.pdf"
    create_worksheet(title, questions, worksheet_file)
    print(f"Worksheet created: {worksheet_file}")
    
    answer_key_file = f"{sanitize_filename(title)}_answer_key.pdf"
    create_answer_key(title, questions, answers, answer_key_file)
    print(f"Answer key created: {answer_key_file}")

if __name__ == "__main__":
    main()
