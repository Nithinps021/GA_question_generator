from app.types import QuestionItem, EnglishQuestionItem


def format_question(question: QuestionItem | EnglishQuestionItem, index: int, total: int) -> str:
    options_text = "\n".join(question.options)
    header = f"<b>Question {index + 1} of {total}</b>"
    if hasattr(question, "direction") and question.direction:
        header += f"\n<i>{question.direction}</i>"
    return (
        f"{header}\n\n"
        f"{question.question}\n\n"
        f"{options_text}"
    )


def build_options_keyboard(
    quiz_type: str,
    quiz_date: str,
    question_index: int,
    correct_answer: str,
    score: int,
    num_options: int = 4,
) -> dict:
    all_options = ["A", "B", "C", "D", "E"]
    options = all_options[:num_options]
    buttons = []
    for opt in options:
        callback_data = f"{quiz_type}:{quiz_date}:{question_index}:{correct_answer}:{opt}:{score}"
        buttons.append({"text": opt, "callback_data": callback_data})
    # Layout: rows of 2, with remainder on last row
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    return {"inline_keyboard": rows}


def format_correct_response(
    question: QuestionItem | EnglishQuestionItem, index: int, total: int, selected: str
) -> str:
    base = format_question(question, index, total)
    return (
        f"{base}\n\n"
        f"\u2705 Correct! You selected {selected}.\n\n"
        f"<b>Explanation:</b> {question.explanation}"
    )


def format_wrong_response(
    question: QuestionItem | EnglishQuestionItem, index: int, total: int, selected: str
) -> str:
    base = format_question(question, index, total)
    return (
        f"{base}\n\n"
        f"\u274c Wrong! You selected {selected}. The correct answer is {question.answer}.\n\n"
        f"<b>Explanation:</b> {question.explanation}"
    )


def format_quiz_complete(score: int, total: int) -> str:
    percentage = round((score / total) * 100)
    if percentage >= 80:
        emoji = "\U0001f3c6"
    elif percentage >= 50:
        emoji = "\U0001f44d"
    else:
        emoji = "\U0001f4aa"
    return (
        f"{emoji} <b>Quiz Complete!</b>\n\n"
        f"Your score: <b>{score}/{total}</b> ({percentage}%)\n\n"
        f"Keep practicing for your bank exams!"
    )
