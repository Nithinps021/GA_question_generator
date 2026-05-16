
from typing import List

from pydantic import BaseModel, Field


class QuestionItem(BaseModel):
    question: str = Field(description="The multiple-choice question focusing on recent financial/banking news.")
    options: List[str] = Field(description="Exactly 4 string options, labeled cleanly as ['A) ...', 'B) ...', 'C) ...', 'D) ...'].")
    answer: str = Field(description="The single correct letter matching the options, exactly 'A', 'B', 'C', or 'D'.")
    explanation: str = Field(description="A comprehensive but concise explanation explaining the correct financial rule, regulatory framework, or context.")

class DailyQuiz(BaseModel):
    date: str = Field(description="Today's date in YYYY-MM-DD format.")
    quiz: List[QuestionItem] = Field(description="An array containing exactly 20 curated banking awareness and current affairs questions.")