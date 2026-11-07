import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from rag_engine import LocalRAGEngine

def main():
    print("=" * 60)
    print("Telecom Resilience AI - Interactive Local RAG Tester")
    print("=" * 60)

    try:
        engine = LocalRAGEngine(auto_load_llm=True)
    except Exception as e:
        print(f"[ERROR] Could not start RAG Engine: {e}")
        return

    sample_questions = [
        "What are the business continuity requirements for banking payment systems?",
        "What are the protection switching architectures recommended by ITU-T for optical networks?",
        "How should telecom operators handle submarine cable disruption events?",
    ]

    print("\nPre-configured test questions:")
    for i, q in enumerate(sample_questions, 1):
        print(f"  [{i}] {q}")

    while True:
        print("\n" + "-" * 60)
        user_input = input("Enter question (1-3, type your own question, or 'exit'): ").strip()
        if not user_input or user_input.lower() in ("exit", "quit", "q"):
            print("Exiting RAG Tester.")
            break

        if user_input in ("1", "2", "3"):
            query = sample_questions[int(user_input) - 1]
        else:
            query = user_input

        print(f"\n[QUERY] {query}")
        print("Thinking & Searching Knowledge Base...")
        
        try:
            result = engine.ask(query)
            print("\n" + "=" * 60)
            print("GENERATED ANSWER:")
            print("=" * 60)
            print(result["answer"])

            print("\n" + "=" * 60)
            print("CITED SOURCES & CHUNKS:")
            print("=" * 60)
            for idx, ctx in enumerate(result["contexts"], 1):
                print(f"[{idx}] Source  : {ctx['source']} (Category: {ctx['category']})")
                print(f"    Chunk ID: {ctx['chunk_id']} | Score: {ctx['score']:.4f}")
                print(f"    Snippet : {ctx['text'][:200]}...\n")
        except Exception as e:
            print(f"[ERROR] Query failed: {e}")

if __name__ == "__main__":
    main()
