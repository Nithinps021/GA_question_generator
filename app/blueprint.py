"""Daily randomized blueprint for the English Prelims quiz.

The LLM is bad at two things we care about: hitting an exact total count, and
genuinely varying question *patterns* (left to itself it clusters on its
favourite formats no matter the temperature). So we decide both in code and
hand the model a concrete, authoritative spec each run.

The blueprint randomizes, every single run:
  - how many questions each of the four blocks gets (always summing to 30),
  - which format(s) each block uses (drawn from a wide pool),
  - the overall difficulty target.

The result is a human-readable directive injected into the prompt template.
"""

import random

TOTAL_QUESTIONS = 30

# (min, max) questions per block. Mins sum to 21, maxes to 35, so 30 is always
# reachable while letting each block swing widely run to run.
BLOCKS = {
    "Reading Comprehension": (6, 10),
    "Grammar & Usage": (5, 8),
    "Vocabulary & Fillers": (5, 9),
    "Verbal Ability": (5, 8),
}

RC_GENRES = [
    "corporate / business",
    "socio-economic",
    "technology",
    "environment / climate",
    "health / medicine",
    "education",
    "science",
    "psychology / behaviour",
    "narrative / story-based",
    "history / culture",
]

RC_QUESTION_TYPES = [
    "main idea / central theme",
    "title selection",
    "specific detail (direct)",
    "specific detail (NOT / except)",
    "inference",
    "author's tone / attitude",
    "purpose of a word or phrase",
    "true / false statement check",
    "assumption",
    "choose the correct summary of the passage",
    "phrase meaning in context (what does the phrase 'X' in paragraph N mean)",
]

RC_VOCAB_TYPES = [
    "synonym (vocabulary-in-context)",
    "antonym (vocabulary-in-context)",
]

# Grammar formats are all "unit" style: one question each.
GRAMMAR_FORMATS = [
    "Error Spotting (sentence split into A/B/C/D parts; option E = 'No Error')",
    "Phrase Replacement (a **bolded** phrase with 4 alternatives + option E 'No correction required')",
    "Sentence Improvement (improve the **bolded** segment)",
    "Spot the correct sentence (choose the single grammatically error-free option)",
    "Fill in the blank (single blank testing preposition / tense / article / conjunction)",
    "Word Order / Sentence Formation (5–6 jumbled words given; arrange them into a grammatically correct meaningful sentence; options are different orderings)",
]

# Vocab formats: ("directive", kind). "set" formats absorb the whole block as
# one passage of N items; "unit" formats are one question each.
VOCAB_FORMATS = [
    ("Cloze Test passage", "set"),
    ("Double Fillers (two blanks per sentence; pick the correct word pair)", "unit"),
    ("Word Swap (two words in the sentence must be interchanged)", "unit"),
    ("Word Usage (in which sentence is the given word used correctly)", "unit"),
    ("Idioms & Phrases (choose the meaning of the idiom)", "unit"),
    ("Synonym / Antonym (direct vocabulary, not passage-based)", "unit"),
]

VERBAL_FORMATS = [
    ("Para Jumble", "set"),
    ("Sentence Rearrangement (fragments P/Q/R/S reordered into one coherent sentence)", "unit"),
    ("Para Completion (choose the sentence that best completes the paragraph)", "unit"),
    ("Odd Sentence Out (find the sentence that does not belong in the set)", "unit"),
    ("Sentence Connectors (combine two sentences using the correct connector)", "unit"),
]

DIFFICULTIES = ["moderate-hard", "hard"]


def _allocate_counts() -> dict[str, int]:
    """Randomly assign a question count to each block, summing to exactly 30."""
    counts = {block: lo for block, (lo, _hi) in BLOCKS.items()}
    remaining = TOTAL_QUESTIONS - sum(counts.values())
    while remaining > 0:
        candidates = [b for b, (_lo, hi) in BLOCKS.items() if counts[b] < hi]
        block = random.choice(candidates)
        counts[block] += 1
        remaining -= 1
    return counts


def _partition(count: int, max_parts: int) -> list[int]:
    """Split `count` into a random number (1..max_parts) of positive integers."""
    parts = random.randint(1, min(max_parts, count))
    sizes = [1] * parts
    for _ in range(count - parts):
        sizes[random.randrange(parts)] += 1
    return sizes


def _rc_directive(count: int) -> str:
    genre = random.choice(RC_GENRES)
    # 2-3 of the questions are vocabulary-in-context, the rest are comprehension.
    n_vocab = min(random.choice([2, 3]), count - 1)
    n_comp = count - n_vocab
    comp = random.sample(RC_QUESTION_TYPES, min(n_comp, len(RC_QUESTION_TYPES)))
    while len(comp) < n_comp:  # allow repeats if we need more than the pool size
        comp.append(random.choice(RC_QUESTION_TYPES))
    vocab = [random.choice(RC_VOCAB_TYPES) for _ in range(n_vocab)]
    mix = comp + vocab
    random.shuffle(mix)
    length = random.choice(["300-360", "330-400", "360-450"])
    lines = [
        f"  - ONE passage, genre: {genre}, length {length} words.",
        f"  - {count} questions off that passage, one each of these types (in this order):",
    ]
    lines += [f"      {i}. {t}" for i, t in enumerate(mix, 1)]
    return "\n".join(lines)


def _grammar_directive(count: int) -> str:
    n_formats = random.randint(1, min(3, count))
    chosen = random.sample(GRAMMAR_FORMATS, n_formats)
    sizes = _partition(count, n_formats)
    return "\n".join(f"  - {n} x {fmt}" for n, fmt in zip(sizes, chosen))


def _vocab_directive(count: int) -> str:
    # Sometimes one Cloze passage absorbs the whole block; otherwise unit formats.
    if random.random() < 0.4:
        return (
            f"  - 1 x Cloze Test: a single passage (100-160 words) with {count} "
            f"numbered blanks, i.e. {count} questions drawn from that one passage."
        )
    unit_formats = [f for f, kind in VOCAB_FORMATS if kind == "unit"]
    n_formats = random.randint(1, min(3, count))
    chosen = random.sample(unit_formats, n_formats)
    sizes = _partition(count, n_formats)
    return "\n".join(f"  - {n} x {fmt}" for n, fmt in zip(sizes, chosen))


def _verbal_directive(count: int) -> str:
    # Sometimes one Para Jumble of N sentences; otherwise unit formats.
    if random.random() < 0.45:
        labels = ",".join(["P", "Q", "R", "S", "T", "U", "V", "W"][:count])
        return (
            f"  - 1 x Para Jumble: a {count}-sentence jumbled paragraph labelled "
            f"{labels}. Each of the {count} questions asks for the position of one "
            f"sentence (e.g. FIRST/SECOND...); options are different orderings or "
            f"sentence labels mapped to A-E."
        )
    unit_formats = [f for f, kind in VERBAL_FORMATS if kind == "unit"]
    n_formats = random.randint(1, min(3, count))
    chosen = random.sample(unit_formats, n_formats)
    sizes = _partition(count, n_formats)
    return "\n".join(f"  - {n} x {fmt}" for n, fmt in zip(sizes, chosen))


def build_daily_blueprint() -> str:
    """Build a fully randomized, authoritative blueprint string for one run."""
    counts = _allocate_counts()
    difficulty = random.choice(DIFFICULTIES)

    directive_fns = {
        "Reading Comprehension": _rc_directive,
        "Grammar & Usage": _grammar_directive,
        "Vocabulary & Fillers": _vocab_directive,
        "Verbal Ability": _verbal_directive,
    }

    sections = []
    for i, (block, count) in enumerate(counts.items(), 1):
        body = directive_fns[block](count)
        sections.append(f"Block {i} — {block}: {count} questions\n{body}")

    header = (
        f"Total questions: {TOTAL_QUESTIONS} (the four block counts below already "
        f"sum to {TOTAL_QUESTIONS} — do not change them).\n"
        f"Overall difficulty target for today: {difficulty}."
    )
    return header + "\n\n" + "\n\n".join(sections)
