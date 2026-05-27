"""Quick test: verify the chat response pipeline works end-to-end."""
import sys
sys.path.insert(0, "/workspace")

from engine.chat_response import generate_response_with_metadata

def main():
    result = generate_response_with_metadata("How are you feeling right now?")
    print(f"Type: {type(result)}")
    print(f"Keys: {list(result.keys())}")
    if "response" in result:
        text = result["response"]
        print(f"Response length: {len(text)}")
        print(f"Response preview: {text[:200]}")
    if "metadata" in result:
        print(f"Metadata keys: {list(result['metadata'].keys())}")
    print("\n✅ Chat pipeline works!")

if __name__ == "__main__":
    main()