#!/usr/bin/env python3
"""
Test OpenAI's n parameter and Google Gemini's candidateCount parameter
to demonstrate they work directly via APIs.
"""

import os
import sys

def test_openai_n_parameter():
    """Test OpenAI's n parameter directly."""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        print("Testing OpenAI's n parameter directly (without EDSL):\n")
        
        # Single API call with n=5
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Pick a random number between 1 and 100. Reply with just the number."}
            ],
            n=5,  # Request 5 completions
            temperature=1.0,
            max_tokens=10
        )
        
        print(f"API call made: 1")
        print(f"Completions received: {len(response.choices)}")
        print("\nNumbers generated:")
        for i, choice in enumerate(response.choices):
            print(f"  Completion {i+1}: {choice.message.content.strip()}")
        
        # Show token usage
        print(f"\nToken usage:")
        print(f"  Prompt tokens: {response.usage.prompt_tokens} (charged once)")
        print(f"  Completion tokens: {response.usage.completion_tokens} (total for all {len(response.choices)} completions)")
        print(f"  Total tokens: {response.usage.total_tokens}")
        
        # Cost calculation
        prompt_cost = response.usage.prompt_tokens * 0.00015 / 1000
        completion_cost = response.usage.completion_tokens * 0.00060 / 1000
        print(f"\nCost for {len(response.choices)} completions:")
        print(f"  Prompt cost: ${prompt_cost:.6f}")
        print(f"  Completion cost: ${completion_cost:.6f}")
        print(f"  Total: ${prompt_cost + completion_cost:.6f}")
        print(f"  Cost per completion: ${(prompt_cost + completion_cost) / len(response.choices):.6f}")
        
        return len(response.choices) == 5
        
    except Exception as e:
        print(f"Error testing OpenAI: {e}")
        return False

def test_gemini_candidate_count():
    """Test Google Gemini's candidateCount parameter."""
    try:
        import google.generativeai as genai
        
        # Configure with API key
        genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
        
        print("\n" + "="*60)
        print("Testing Google Gemini's candidateCount parameter:\n")
        
        # Try with Gemini 2.0 Flash (supports candidateCount)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Test with candidateCount
        generation_config = genai.GenerationConfig(
            candidate_count=4,  # Request 4 candidates
            temperature=1.0,
            max_output_tokens=10
        )
        
        response = model.generate_content(
            "Pick a random number between 1 and 100. Reply with just the number.",
            generation_config=generation_config
        )
        
        print(f"Model: gemini-2.0-flash-exp")
        print(f"candidateCount requested: 4")
        print(f"Candidates received: {len(response.candidates)}")
        print("\nNumbers generated:")
        for i, candidate in enumerate(response.candidates):
            if candidate.content and candidate.content.parts:
                print(f"  Candidate {i+1}: {candidate.content.parts[0].text.strip()}")
        
        # Check token usage if available
        if hasattr(response, 'usage_metadata'):
            print(f"\nToken usage:")
            print(f"  Prompt tokens: {response.usage_metadata.prompt_token_count}")
            print(f"  Candidates tokens: {response.usage_metadata.candidates_token_count}")
            print(f"  Total tokens: {response.usage_metadata.total_token_count}")
        
        success_2_0 = len(response.candidates) == 4
        
        # Try with older model for comparison
        print("\n" + "-"*40)
        print("Testing with older Gemini 1.5 Flash model:\n")
        model_15 = genai.GenerativeModel('gemini-1.5-flash')
        
        generation_config_15 = genai.GenerationConfig(
            candidate_count=2,  # Try requesting 2 candidates
            temperature=1.0,
            max_output_tokens=10
        )
        
        try:
            response_15 = model_15.generate_content(
                "Pick a random number between 1 and 100. Reply with just the number.",
                generation_config=generation_config_15
            )
            
            print(f"Model: gemini-1.5-flash")
            print(f"candidateCount requested: 2")
            print(f"Candidates received: {len(response_15.candidates)}")
            
            if len(response_15.candidates) == 1:
                print("❌ Gemini 1.5 Flash only returns 1 candidate (candidateCount not supported)")
                
        except Exception as e:
            print(f"Error: {e}")
            if "candidate" in str(e).lower():
                print("❌ Gemini 1.5 Flash doesn't support candidateCount > 1")
        
        return success_2_0
        
    except Exception as e:
        print(f"Error testing Gemini: {e}")
        return False

def test_edsl_with_params():
    """Test EDSL with n and candidateCount parameters."""
    try:
        from edsl import Model, QuestionFreeText
        
        print("\n" + "="*60)
        print("Testing EDSL with multiple completion parameters:\n")
        
        question = QuestionFreeText(
            question_name="number",
            question_text="Pick a random number between 1 and 100. Reply with just the number:"
        )
        
        # Test OpenAI n parameter through EDSL
        print("1. OpenAI with n=3 through EDSL:")
        model_openai = Model('gpt-4o-mini', service_name='openai', n=3)
        result_openai = question.by(model_openai).run()
        results_openai = result_openai.to_list()
        
        print(f"   Results received: {len(results_openai)}")
        print(f"   Expected: 3")
        if len(results_openai) == 1:
            print("   ❌ n parameter not working in EDSL")
        else:
            print("   ✅ n parameter working!")
        
        # Test Gemini candidateCount through EDSL
        print("\n2. Gemini with candidateCount=3 through EDSL:")
        model_gemini = Model('gemini-2.0-flash-exp', service_name='google', candidateCount=3)
        
        try:
            result_gemini = question.by(model_gemini).run()
            results_gemini = result_gemini.to_list()
            
            print(f"   Results received: {len(results_gemini)}")
            print(f"   Expected: 3")
            if len(results_gemini) == 1:
                print("   ❌ candidateCount parameter not working in EDSL")
            else:
                print("   ✅ candidateCount parameter working!")
                
        except Exception as e:
            print(f"   Error: {e}")
            print("   ❌ EDSL may not support candidateCount parameter")
            
    except Exception as e:
        print(f"Error testing EDSL: {e}")

def main():
    """Run all tests."""
    print("="*60)
    print("Testing Multiple Completion Parameters in LLM APIs")
    print("="*60)
    
    # Check for API keys
    if not os.environ.get('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY not set")
    if not os.environ.get('GOOGLE_API_KEY'):
        print("Warning: GOOGLE_API_KEY not set")
    if not os.environ.get('EXPECTED_PARROT_API_KEY'):
        print("Warning: EXPECTED_PARROT_API_KEY not set")
    
    # Run tests
    openai_success = test_openai_n_parameter()
    gemini_success = test_gemini_candidate_count()
    test_edsl_with_params()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"OpenAI n parameter: {'✅ Working' if openai_success else '❌ Failed'}")
    print(f"Gemini candidateCount: {'✅ Working' if gemini_success else '❌ Failed'}")
    print("\nConclusion:")
    print("- OpenAI's n parameter generates multiple completions in one API call")
    print("- Gemini 2.0+ supports candidateCount for multiple candidates")
    print("- Both charge input tokens only once (significant cost savings)")
    print("- EDSL should leverage these native features for efficiency")

if __name__ == "__main__":
    main()