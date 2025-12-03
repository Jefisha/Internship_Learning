

import google.generativeai as genai
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import chromadb
from chromadb.utils import embedding_functions

# --------------------------------------
# 1. CONFIGURE GEMINI API
# --------------------------------------

GEMINI_API_KEY = "your api-key"

genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-2.5-flash")

# --------------------------------------
# 2. SETUP CHROMADB
# --------------------------------------

client = chromadb.Client(
    chromadb.config.Settings(
        persist_directory="study_store"
    )
)

embedder = embedding_functions.DefaultEmbeddingFunction()

quiz_collection = client.get_or_create_collection(
    name="quiz_store",
    embedding_function=embedder
)

# --------------------------------------
# 3. LANGGRAPH STATE
# --------------------------------------

class StudyState(TypedDict):
    query: str
    answer: str
    quiz: List[dict]
    level: str
    user_answers: List[str]
    results: List[dict]

# --------------------------------------
# 4. NODES
# --------------------------------------

def answer_query(state: StudyState):
    """LLM answers the user's question."""
    prompt = f"Answer clearly and shortly:\n\n{state['query']}"
    response = gemini.generate_content(prompt)
    state["answer"] = response.text
    return state

def ask_quiz(state: StudyState):
    """Ask user whether to generate quiz."""
    print("\nLLM Answer:")
    print(state["answer"])
    print("\nDo you want to generate a quiz? (yes/no): ")
    choice = input("> ").strip().lower()

    if choice != "yes":
        return state  # end flow

    level = input("Enter level (easy / medium / hard): ").lower()
    state["level"] = level
    return state

def generate_quiz(state: StudyState):
    """LLM generates quiz based on the topic with safe JSON parsing."""
    import json, re

    prompt = f"""
    Generate a {state['level']} level quiz (5 questions) based ONLY on this topic:
    {state['query']}

    STRICT RULES:
    - Output VALID JSON only.
    - No markdown.
    - No explanations.
    - Format:
    [
      {{ "question": "...", "answer": "..." }},
      ...
    ]
    """

    print("\nGenerating quiz...")

    response = gemini.generate_content(prompt)

    raw = response.text.strip()
    print("\nRAW MODEL OUTPUT:\n", raw)  # DEBUG view

    # -------- FIX 1: Extract JSON block --------
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if not match:
        raise ValueError("Model did not return JSON.")

    json_text = match.group(0)

    # -------- FIX 2: Try loading JSON --------
    try:
        quiz = json.loads(json_text)
    except json.JSONDecodeError as e:
        print("\nMODEL RETURNED INVALID JSON!")
        print("JSON TEXT:\n", json_text)
        raise e

    state["quiz"] = quiz

    # Display quiz
    print("\nGenerated Quiz:")
    for i, q in enumerate(quiz):
        print(f"Q{i+1}: {q['question']}")

    # Store in Chroma
    quiz_collection.add(
        ids=[f"quiz_{state['query']}"],
        documents=[json.dumps(quiz)]
    )

    return state

def evaluate_quiz(state: StudyState):
    """Collect user answers and evaluate."""
    state["user_answers"] = []
    state["results"] = []

    print("\nAnswer the quiz below:\n")

    for q in state["quiz"]:
        print(q["question"])
        usr = input("Your answer: ").strip()
        state["user_answers"].append(usr)

        explanation_prompt = f"""
        Correct answer: {q['answer']}
        User answer: {usr}
        Explain if correct/incorrect and give explanation.
        """
        explain = gemini.generate_content(explanation_prompt).text

        state["results"].append({
            "question": q["question"],
            "correct": q["answer"],
            "user": usr,
            "explanation": explain
        })

    # Store evaluation in Chroma
    for i, item in enumerate(state["results"]):
        quiz_collection.add(
            ids=[f"result_{i}_{state['query']}"],
            documents=[str(item)]
        )

    print("\n=== RESULTS ===")
    for r in state["results"]:
        print("\nQ:", r["question"])
        print("Correct:", r["correct"])
        print("Your answer:", r["user"])
        print("Explanation:", r["explanation"])

    return state

# --------------------------------------
# 5. BUILD GRAPH
# --------------------------------------

graph = StateGraph(StudyState)

graph.add_node("answer_query", answer_query)
graph.add_node("ask_quiz", ask_quiz)
graph.add_node("generate_quiz", generate_quiz)
graph.add_node("evaluate_quiz", evaluate_quiz)

graph.set_entry_point("answer_query")
graph.add_edge("answer_query", "ask_quiz")
graph.add_edge("ask_quiz", "generate_quiz")
graph.add_edge("generate_quiz", "evaluate_quiz")
graph.add_edge("evaluate_quiz", END)

app = graph.compile()

# --------------------------------------
# 6. RUN LOOP
# --------------------------------------

print("Enter your study question:")
user_query = input("> ")

initial = {
    "query": user_query,
    "answer": "",
    "quiz": [],
    "level": "",
    "user_answers": [],
    "results": []
}

output = app.invoke(initial)

print("\nBackend Test Complete.")
