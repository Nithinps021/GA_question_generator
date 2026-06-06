from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class QuestionItem(BaseModel):
    topic: str = Field(description="The exact topic, e.g., 'Error Spotting', 'Phrase Replacement', 'Word Swap', 'Idioms & Phrases', or 'Double Fillers'.")
    direction: str = Field(description="The specific instruction text for the student, mimicking real bank exams.")
    question: str = Field(description="The multiple-choice question focusing on recent financial/banking news.")
    options: List[str] = Field(description="Exactly 4 string options, labeled cleanly as ['A) ...', 'B) ...', 'C) ...', 'D) ...'].")
    answer: str = Field(description="The single correct letter matching the options, exactly 'A', 'B', 'C', or 'D'.")
    explanation: str = Field(description="A comprehensive but concise explanation explaining the correct financial rule, regulatory framework, or context.")

class DailyQuiz(BaseModel):
    date: str = Field(description="Today's date in YYYY-MM-DD format.")
    quiz: List[QuestionItem] = Field(description="An array containing exactly 20 curated banking awareness and current affairs questions.")


class EnglishQuestionItem(BaseModel):
    topic: str = Field(description="The exact topic, e.g., 'Error Spotting', 'Phrase Replacement', 'Word Swap', 'Idioms & Phrases', or 'Double Fillers'.")
    direction: str = Field(description="The specific instruction text for the student, mimicking real bank exams.")
    question: str = Field(description="The sentence or paragraph. Use Markdown to **bold** parts if needed for Phrase Replacement or Word Swap.")
    options: List[str] = Field(description="Exactly 5 string options labeled 'A) ...', 'B) ...', 'C) ...', 'D) ...', 'E) ...'. For Error Spotting, option E is usually 'No Error'.")
    answer: str = Field(description="The exact correct letter: 'A', 'B', 'C', 'D', or 'E'.")
    explanation: str = Field(description="A highly detailed explanation of the grammatical rule, vocabulary context, or idiom meaning. It must perfectly explain why the answer is right and why the others fail.")
    topic_block: str = Field(description="String (e.g., Reading Comprehension, Grammar & Usage, Vocabulary & Fillers, Verbal Ability)")
    sub_topic: str = Field(description="String (e.g., Error Spotting, Cloze Test, Para jumble)")
    verified_quality_score: str = Field(description="")

class DailyEnglishQuiz(BaseModel):
    date: str = Field(description="Today's date in YYYY-MM-DD format.", default=datetime.now().strftime("%Y-%m-%d"))
    quiz: List[EnglishQuestionItem] = Field(description="An array containing the generated medium-to-hard English questions.")


class ReferenceQuestion(BaseModel):
    exam_name: str = Field(description="The exam this question appeared in, e.g., 'SBI PO Prelims'.")
    year: int = Field(description="The year the question appeared in the exam.")
    question: str = Field(description="The full question text with labeled parts.")
    options: List[str] = Field(description="List of answer options, e.g., ['A', 'B', 'C', 'D', 'E'].")
    answer: str = Field(description="The correct option letter.")
    explanation: str = Field(description="Explanation of why the answer is correct.")


class ReferenceSection(BaseModel):
    collection: str = Field(description="The collections this section belongs to.")
    section_name: str = Field(description="The topic/section name, e.g., 'Error Spotting', 'Phrase Replacement'.")
    questions: List[ReferenceQuestion] = Field(description="List of reference questions for this section.")