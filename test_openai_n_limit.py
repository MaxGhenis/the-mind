#!/usr/bin/env python3
"""
Test OpenAI's n parameter limit with the new API key.
"""

import os
from openai import OpenAI

def test_openai_n_limits():
    """Test OpenAI n parameter to find the maximum limit."""
    
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    
    print("=" * 60)
    print("Testing OpenAI n Parameter Maximum Limit")
    print("=" * 60)
    
    model = "gpt-4o-mini"
    print(f"\nModel: {model}")
    print("-" * 40)
    
    # Test increasing values of n
    test_values = [1, 5, 10, 15, 20, 25, 30, 40, 50, 100, 128]
    max_working = 0
    
    for n_value in test_values:
        print(f"\nTesting n={n_value}:")
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "random number 1-100 nothing else"}
                ],
                n=n_value,
                temperature=1.0,
                max_tokens=5
            )
            
            num_received = len(response.choices)
            
            if num_received == n_value:
                print(f"  ✅ SUCCESS: Requested {n_value}, got {num_received}")
                max_working = n_value
                
                # Show first few numbers
                if n_value <= 10:
                    numbers = [choice.message.content.strip() for choice in response.choices]
                    print(f"  Numbers: {', '.join(numbers)}")
                else:
                    # Just show first 5 for large n
                    numbers = [choice.message.content.strip() for choice in response.choices[:5]]
                    print(f"  First 5: {', '.join(numbers)}...")
                
                # Show token usage
                print(f"  Tokens: {response.usage.prompt_tokens} prompt (charged once!), "
                      f"{response.usage.completion_tokens} completion total")
                
            else:
                print(f"  ⚠️  PARTIAL: Requested {n_value}, got {num_received}")
                break
                
        except Exception as e:
            error_msg = str(e)
            if "Invalid" in error_msg or "maximum" in error_msg or "must be" in error_msg:
                print(f"  ❌ LIMIT REACHED: {error_msg}")
                print(f"\n  → Maximum n for {model}: {max_working}")
                break
            else:
                print(f"  ❌ Error: {error_msg[:100]}...")
                if "quota" not in error_msg.lower():
                    break
    
    return max_working

def compare_with_gemini():
    """Compare OpenAI and Gemini limits."""
    print("\n" + "=" * 60)
    print("Comparison: OpenAI vs Gemini")
    print("=" * 60)
    
    print("\n📊 Multiple Completion Limits:")
    print("  • Gemini (candidateCount): 1-8 (hard limit)")
    print("  • OpenAI (n): Testing to find limit...")
    
    print("\n💰 Cost Model (both providers):")
    print("  • Input tokens: Charged ONCE regardless of n/candidateCount")
    print("  • Output tokens: Charged for all completions")
    print("  • Savings: Up to 90% on input tokens for multiple samples")

def main():
    """Run the test."""
    
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not set")
        return
    
    # Test OpenAI limits
    max_n = test_openai_n_limits()
    
    # Compare with Gemini
    compare_with_gemini()
    
    if max_n > 0:
        print(f"\n✅ OpenAI {model} maximum n: {max_n}")
        
        if max_n > 8:
            print(f"   OpenAI supports {max_n/8:.1f}x more completions than Gemini!")
        elif max_n == 8:
            print("   Same as Gemini's candidateCount limit")
        else:
            print(f"   Less than Gemini's limit of 8")
    
    print("\n" + "=" * 60)
    print("Recommendation for EDSL")
    print("=" * 60)
    print(f"\n• For OpenAI: Use n up to {max_n if max_n > 0 else '?'}")
    print("• For Gemini: Use candidateCount up to 8")
    print("• Both provide major cost savings on input tokens!")

if __name__ == "__main__":
    main()