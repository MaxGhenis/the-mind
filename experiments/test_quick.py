"""Quick test to verify EDSL and API keys are working."""

import os
from dotenv import load_dotenv
from edsl import Model, QuestionFreeText

# Load environment variables
load_dotenv()

print("Testing EDSL setup...")
print("=" * 60)

# Check API keys
api_keys = {
    "OpenAI": os.getenv("OPENAI_API_KEY"),
    "Anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "Google": os.getenv("GOOGLE_API_KEY")
}

for provider, key in api_keys.items():
    status = "✓ Configured" if key else "✗ Missing"
    print(f"{provider:15s}: {status}")

print("\n" + "=" * 60)
print("Testing Gemini Flash (fastest, cheapest)...")
print("=" * 60)

try:
    # Create a simple test question
    model = Model("gemini-2.5-flash")

    q = QuestionFreeText(
        question_name="test",
        question_text="Respond with just the number 42:"
    )

    result = q.by(model).run()
    response = str(result.select("answer.test").first())

    print(f"✓ SUCCESS: Got response: '{response}'")
    print("\n✅ EDSL is working correctly!")
    print("\nReady to run experiments. Use:")
    print("  python experiments/comprehensive_experiment.py --test")

except Exception as e:
    print(f"✗ ERROR: {e}")
    print("\nTroubleshooting:")
    print("1. Check API keys in .env file")
    print("2. Verify GOOGLE_API_KEY has quota/credits")
    print("3. Try: pip install --upgrade edsl")
