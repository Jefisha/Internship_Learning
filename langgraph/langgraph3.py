from langgraph.graph import StateGraph, END
from typing import TypedDict
from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Enable LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")

# -------------------------------
# 1. Define LangGraph State
# -------------------------------
class GraphState(TypedDict):
    question: str
    answer: str

# -------------------------------
# 2. Gemini Model
# -------------------------------
model = GoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.2
)

# -------------------------------
# 3. Node Function
# -------------------------------
def answer_node(state: GraphState):
    question = state["question"]
    response = model.invoke(question)
    return {"answer": response}

# -------------------------------
# 4. Build Graph
# -------------------------------
graph = StateGraph(GraphState)
graph.add_node("answer_node", answer_node)
graph.set_entry_point("answer_node")
graph.add_edge("answer_node", END)

app = graph.compile()

# -------------------------------
# 5. Run
# -------------------------------
if __name__ == "__main__":
    user_q = input("Enter your question: ")
    result = app.invoke({"question": user_q})
    print("\n--- Gemini Response ---\n")
    print(result["answer"])