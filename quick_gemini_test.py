#!/usr/bin/env python3
"""Quick test to see which Gemini models support candidateCount."""

# List of Gemini models and expected candidateCount support based on documentation
GEMINI_MODELS = {
    # Gemini 2.5 (newest)
    "gemini-2.5-flash": "Unknown - needs testing",
    "gemini-2.5-flash-lite": "Unknown - needs testing", 
    "gemini-2.5-pro": "Unknown - needs testing",
    
    # Gemini 2.0 (documented support)
    "gemini-2.0-flash": "1-8 candidates (documented)",
    "gemini-2.0-flash-lite": "1-8 candidates (documented)",
    
    # Gemini 1.5 (older)
    "gemini-1.5-flash": "Limited to 1 (known limitation)",
    "gemini-1.5-pro": "Limited to 1 (known limitation)",
}

print("Gemini Model candidateCount Support Status")
print("=" * 60)
print("\nBased on Google Cloud documentation:")
print("https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/inference#generationconfig")
print()

for model, status in GEMINI_MODELS.items():
    print(f"• {model:30} {status}")

print("\n" + "=" * 60)
print("KEY POINTS:")
print("=" * 60)
print()
print("1. Gemini 2.0 models (flash, flash-lite) support candidateCount 1-8")
print("2. Gemini 2.5 support needs to be tested empirically")
print("3. Gemini 1.5 models are limited to candidateCount=1")
print()
print("IMPORTANT: You're only charged for input tokens ONCE regardless")
print("of candidateCount value, making this very cost-effective for")
print("research requiring multiple samples.")
print()
print("To test with actual API:")
print("1. Set GOOGLE_API_KEY environment variable")
print("2. Run: python test_gemini_25_models.py")