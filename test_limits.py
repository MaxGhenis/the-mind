#!/usr/bin/env python3
"""
Test the limits of candidateCount for Gemini and n for OpenAI.
"""

import os
import sys

def test_gemini_candidatecount_limits():
    """Test Gemini candidateCount with values 1-10 to find the limit."""
    import google.generativeai as genai
    
    genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
    
    print("=" * 60)
    print("Testing Gemini candidateCount Limits")
    print("=" * 60)
    
    # Test with Gemini 2.5 Flash (we know it supports candidateCount)
    model_name = "gemini-2.5-flash"
    model = genai.GenerativeModel(model_name)
    
    print(f"\nModel: {model_name}")
    print("-" * 40)
    
    # Test values from 1 to 10
    test_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    max_working = 0
    
    for count in test_values:
        print(f"\nTesting candidateCount={count}:")
        
        try:
            generation_config = genai.GenerationConfig(
                candidate_count=count,
                temperature=1.0,
                max_output_tokens=5
            )
            
            response = model.generate_content(
                "Pick a number between 1 and 10. Reply with just the number.",
                generation_config=generation_config
            )
            
            num_received = len(response.candidates)
            
            if num_received == count:
                print(f"  ✅ SUCCESS: Requested {count}, got {num_received}")
                max_working = count
            else:
                print(f"  ⚠️  PARTIAL: Requested {count}, got {num_received}")
                if num_received > max_working:
                    max_working = num_received
                    
        except Exception as e:
            error_msg = str(e)
            if "candidate" in error_msg.lower() or "range" in error_msg.lower():
                print(f"  ❌ FAILED: {error_msg}")
                print(f"  → Maximum supported appears to be {max_working}")
                break
            else:
                print(f"  ❌ Error: {error_msg[:100]}")
    
    print("\n" + "=" * 60)
    print(f"RESULT: Maximum candidateCount for {model_name}: {max_working}")
    print("=" * 60)
    
    return max_working

def test_openai_n_limits():
    """Test OpenAI n parameter limits."""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        print("\n" + "=" * 60)
        print("Testing OpenAI n Parameter Limits")
        print("=" * 60)
        
        # Test with GPT-4o-mini
        model_name = "gpt-4o-mini"
        print(f"\nModel: {model_name}")
        print("-" * 40)
        
        # Test various n values
        test_values = [1, 5, 10, 20, 50, 100, 128, 200]
        max_working = 0
        
        for n_value in test_values:
            print(f"\nTesting n={n_value}:")
            
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "user", "content": "Say 'hi'."}
                    ],
                    n=n_value,
                    temperature=1.0,
                    max_tokens=2
                )
                
                num_received = len(response.choices)
                
                if num_received == n_value:
                    print(f"  ✅ SUCCESS: Requested {n_value}, got {num_received}")
                    max_working = n_value
                else:
                    print(f"  ⚠️  PARTIAL: Requested {n_value}, got {num_received}")
                    
            except Exception as e:
                error_msg = str(e)
                if "invalid" in error_msg.lower() or "maximum" in error_msg.lower():
                    print(f"  ❌ FAILED: {error_msg}")
                    print(f"  → Maximum supported appears to be {max_working}")
                    break
                else:
                    print(f"  ❌ Error: {error_msg[:200]}")
                    # Continue testing if it's just a quota issue
                    if "quota" in error_msg.lower():
                        print("  (Quota exceeded, but parameter might still be valid)")
        
        print("\n" + "=" * 60)
        print(f"RESULT: Maximum n for {model_name}: {max_working if max_working > 0 else 'Unknown (quota issues)'}")
        print("=" * 60)
        
        return max_working
        
    except ImportError:
        print("\n⚠️  OpenAI library not available in this environment")
        return 0

def document_limits():
    """Document the known limits from documentation."""
    print("\n" + "=" * 60)
    print("Documented Limits (from official docs)")
    print("=" * 60)
    
    print("\nGoogle Gemini:")
    print("  • Gemini 2.0 models: candidateCount 1-8")
    print("  • Gemini 2.5 models: candidateCount 1-8 (per docs)")
    print("  • Actual tested limit will be shown above")
    
    print("\nOpenAI:")
    print("  • No documented hard limit for n parameter")
    print("  • Practical limit may be enforced by API")
    print("  • Cost increases linearly with n (for output tokens)")
    
    print("\nKey Differences:")
    print("  • Gemini: Hard limit of 8 candidates")
    print("  • OpenAI: No documented limit (but practical limits may apply)")
    print("  • Both: Input tokens charged once regardless of n/candidateCount")

def main():
    """Run all limit tests."""
    
    # Test Gemini limits
    if os.environ.get('GOOGLE_API_KEY'):
        gemini_max = test_gemini_candidatecount_limits()
    else:
        print("⚠️  GOOGLE_API_KEY not set")
        gemini_max = 0
    
    # Test OpenAI limits
    if os.environ.get('OPENAI_API_KEY'):
        openai_max = test_openai_n_limits()
    else:
        print("⚠️  OPENAI_API_KEY not set")
        openai_max = 0
    
    # Document known limits
    document_limits()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY OF FINDINGS")
    print("=" * 60)
    
    if gemini_max > 0:
        print(f"\n✅ Gemini 2.5 Flash: Maximum candidateCount = {gemini_max}")
        if gemini_max == 8:
            print("   Matches documented limit of 8")
    
    if openai_max > 0:
        print(f"\n✅ OpenAI GPT-4o-mini: Maximum n = {openai_max}+")
        print("   (May support higher values)")
    
    print("\nRecommendation for EDSL:")
    print("  • For Gemini: Use candidateCount up to 8")
    print("  • For OpenAI: Use n up to practical limits")
    print("  • Both provide major cost savings on input tokens!")

if __name__ == "__main__":
    # Set the Gemini API key if provided
    if len(sys.argv) > 1:
        os.environ['GOOGLE_API_KEY'] = sys.argv[1]
    
    main()