#!/usr/bin/env python3
"""
Test OpenAI's n parameter limit - testing higher values.
"""

import os
from openai import OpenAI

def test_openai_n_limits():
    """Test OpenAI n parameter to find the maximum limit."""
    
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    
    print("=" * 60)
    print("Testing OpenAI n Parameter Maximum Limit (Extended)")
    print("=" * 60)
    
    model = "gpt-4o-mini"
    print(f"\nModel: {model}")
    print("-" * 40)
    
    # Since 128 worked, test even higher values
    test_values = [128, 200, 256, 500, 1000]
    max_working = 128  # We know this works from previous test
    
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
                
                # Show token usage
                print(f"  Tokens: {response.usage.prompt_tokens} prompt (charged once!), "
                      f"{response.usage.completion_tokens} completion total")
                
                # Calculate cost savings
                savings = (1 - 1/n_value) * 100
                print(f"  Input token savings: {savings:.1f}% vs making {n_value} separate calls")
                
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
                print(f"  ❌ Error: {error_msg[:200]}...")
                if "timeout" in error_msg.lower():
                    print("     (Request timed out - n might be too high)")
                break
    
    return max_working

def main():
    """Run the test."""
    
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not set")
        return
    
    # Test OpenAI limits
    max_n = test_openai_n_limits()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    print(f"\n✅ OpenAI gpt-4o-mini maximum n: {max_n}+")
    
    if max_n >= 128:
        print(f"   • OpenAI supports {max_n/8:.0f}x more completions than Gemini!")
        print(f"   • At n={max_n}: {(1 - 1/max_n)*100:.1f}% savings on input tokens")
    
    print("\n📊 Provider Comparison:")
    print(f"  • OpenAI (n): 1-{max_n}+ (may support even higher)")
    print("  • Gemini (candidateCount): 1-8 (hard limit)")
    
    print("\n💰 Cost Implications:")
    print(f"  • For 100 samples: OpenAI can do it in 1 call, Gemini needs 13 calls")
    print(f"  • Input token savings at n=100: 99% for OpenAI, 87.5% max for Gemini")
    
    print("\n" + "=" * 60)
    print("Recommendation for EDSL")
    print("=" * 60)
    print(f"\n• For OpenAI: Use n up to at least {max_n}")
    print("• For Gemini: Use candidateCount up to 8")
    print("• Implement smart batching: use native parameters when available")
    print("• This would provide massive cost savings for research!")

if __name__ == "__main__":
    main()