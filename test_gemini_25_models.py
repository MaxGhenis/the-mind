#!/usr/bin/env python3
"""
Test candidateCount parameter across all Gemini 2.5 models.
"""

import os
import sys

def test_gemini_model(model_name, candidate_count=4):
    """Test a specific Gemini model with candidateCount."""
    try:
        import google.generativeai as genai
        
        # Configure with API key
        genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
        
        print(f"\nTesting {model_name}:")
        print("-" * 40)
        
        try:
            model = genai.GenerativeModel(model_name)
            
            # Test with candidateCount
            generation_config = genai.GenerationConfig(
                candidate_count=candidate_count,
                temperature=1.0,
                max_output_tokens=10
            )
            
            response = model.generate_content(
                "Pick a random number between 1 and 100. Reply with just the number.",
                generation_config=generation_config
            )
            
            print(f"  candidateCount requested: {candidate_count}")
            print(f"  Candidates received: {len(response.candidates)}")
            
            if len(response.candidates) == candidate_count:
                print(f"  ✅ SUCCESS: Got {candidate_count} candidates as requested")
            elif len(response.candidates) == 1:
                print(f"  ❌ LIMITED: Only got 1 candidate (candidateCount not supported)")
            else:
                print(f"  ⚠️  PARTIAL: Got {len(response.candidates)} candidates instead of {candidate_count}")
            
            # Show the generated numbers
            print("  Numbers generated:")
            for i, candidate in enumerate(response.candidates):
                if candidate.content and candidate.content.parts:
                    print(f"    Candidate {i+1}: {candidate.content.parts[0].text.strip()}")
            
            # Check token usage if available
            if hasattr(response, 'usage_metadata'):
                print(f"  Token usage:")
                print(f"    Prompt tokens: {response.usage_metadata.prompt_token_count}")
                print(f"    Total tokens: {response.usage_metadata.total_token_count}")
            
            return len(response.candidates)
            
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                print(f"  ❌ Model not found or not available")
            elif "candidate" in error_msg.lower():
                print(f"  ❌ Error: {error_msg}")
                if "must be 1" in error_msg or "only one" in error_msg.lower():
                    print(f"  → Model doesn't support candidateCount > 1")
            else:
                print(f"  ❌ Error: {error_msg}")
            return 0
            
    except ImportError:
        print(f"  ⚠️  google.generativeai not installed")
        return 0

def test_all_gemini_25_models():
    """Test all Gemini 2.5 model variants."""
    print("=" * 60)
    print("Testing candidateCount on all Gemini 2.5 Models")
    print("=" * 60)
    
    # List of Gemini 2.5 models to test
    models_to_test = [
        # Gemini 2.5 models
        ("gemini-2.5-flash", 4),
        ("gemini-2.5-flash-latest", 4),
        ("gemini-2.5-flash-lite", 4),
        ("gemini-2.5-flash-lite-latest", 4),
        ("gemini-2.5-pro", 4),
        ("gemini-2.5-pro-latest", 4),
        
        # Gemini 2.0 models for comparison
        ("gemini-2.0-flash", 4),
        ("gemini-2.0-flash-exp", 4),
        ("gemini-2.0-flash-lite", 4),
        
        # Gemini 1.5 models for comparison
        ("gemini-1.5-flash", 2),
        ("gemini-1.5-pro", 2),
    ]
    
    results = {}
    
    for model_name, candidate_count in models_to_test:
        result = test_gemini_model(model_name, candidate_count)
        results[model_name] = result
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    print("\n✅ Models supporting candidateCount > 1:")
    for model, count in results.items():
        if count > 1:
            print(f"  - {model}: {count} candidates")
    
    print("\n❌ Models limited to 1 candidate:")
    for model, count in results.items():
        if count == 1:
            print(f"  - {model}")
    
    print("\n⚠️  Models not available or errored:")
    for model, count in results.items():
        if count == 0:
            print(f"  - {model}")
    
    # Key findings
    print("\n" + "=" * 60)
    print("KEY FINDINGS")
    print("=" * 60)
    
    gemini_25_support = any(
        "2.5" in model and count > 1 
        for model, count in results.items()
    )
    
    if gemini_25_support:
        print("✅ Gemini 2.5 models DO support candidateCount > 1")
        print("   This enables cost-efficient multiple completions!")
    else:
        print("❌ Gemini 2.5 models do NOT support candidateCount > 1")
        print("   Multiple API calls would be required for multiple samples")
    
    print("\nRecommendation for EDSL:")
    print("- Detect model version and use candidateCount when supported")
    print("- This would provide significant cost savings for research")

def test_vertex_ai_models():
    """Test Vertex AI specific models if available."""
    print("\n" + "=" * 60)
    print("Testing Vertex AI Models (if available)")
    print("=" * 60)
    
    try:
        from google.cloud import aiplatform
        from vertexai.generative_models import GenerativeModel, GenerationConfig
        
        # Initialize Vertex AI
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            print("  ⚠️  GOOGLE_CLOUD_PROJECT not set")
            return
        
        aiplatform.init(project=project_id)
        
        vertex_models = [
            "gemini-2.5-flash-001",
            "gemini-2.5-flash-002", 
            "gemini-2.5-pro-001",
            "gemini-2.5-pro-002",
        ]
        
        for model_name in vertex_models:
            print(f"\nTesting Vertex AI {model_name}:")
            print("-" * 40)
            
            try:
                model = GenerativeModel(model_name)
                
                config = GenerationConfig(
                    candidate_count=4,
                    temperature=1.0,
                    max_output_tokens=10,
                )
                
                response = model.generate_content(
                    "Pick a random number between 1 and 100.",
                    generation_config=config,
                )
                
                print(f"  Candidates received: {len(response.candidates)}")
                if len(response.candidates) > 1:
                    print(f"  ✅ Vertex AI {model_name} supports candidateCount!")
                    
            except Exception as e:
                print(f"  Error: {e}")
                
    except ImportError:
        print("  ⚠️  Vertex AI SDK not installed")
        print("  Install with: pip install google-cloud-aiplatform")

def main():
    """Run all tests."""
    
    # Check for API key
    if not os.environ.get('GOOGLE_API_KEY'):
        print("⚠️  Warning: GOOGLE_API_KEY not set")
        print("Set it with: export GOOGLE_API_KEY='your-api-key'")
        print()
    
    # Test regular Gemini API models
    test_all_gemini_25_models()
    
    # Optionally test Vertex AI models
    if os.environ.get('TEST_VERTEX_AI'):
        test_vertex_ai_models()
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()