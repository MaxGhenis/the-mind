"""Test if Expected Parrot actually uses the n parameter efficiently."""

import os
import time
from edsl import Model, QuestionFreeText

os.environ['EXPECTED_PARROT_API_KEY'] = os.environ.get('EXPECTED_PARROT_API_KEY', '')

def test_n_parameter():
    """Test if n parameter works in EDSL."""
    
    print("Testing n parameter in Expected Parrot...")
    
    # Create a simple question
    q = QuestionFreeText(
        question_name="test",
        question_text="Pick a random number between 1 and 10. Just respond with the number:"
    )
    
    # Test 1: Without n parameter (baseline)
    print("\n1. Single response (n=1):")
    model1 = Model('gpt-4o-mini', service_name='openai')
    start = time.time()
    result1 = q.by(model1).run()
    time1 = time.time() - start
    print(f"   Time: {time1:.2f}s")
    print(f"   Result: {result1.select('answer.test').first()}")
    
    # Test 2: With n=5 parameter
    print("\n2. Testing with n=5:")
    model2 = Model('gpt-4o-mini', service_name='openai', n=5)
    start = time.time()
    result2 = q.by(model2).run()
    time2 = time.time() - start
    print(f"   Time: {time2:.2f}s")
    
    # Check what we get back
    results_list = result2.to_list()
    print(f"   Number of results: {len(results_list)}")
    
    if len(results_list) > 1:
        print("   ✅ Got multiple results from single call!")
        print("   Values:", [r[0] if isinstance(r, tuple) else r for r in results_list[:5]])
    else:
        print("   ❌ Only got 1 result despite n=5")
        
    # Test 3: Check if it's actually more efficient
    print("\n3. Efficiency test - 10 calls with n=1 vs 1 call with n=10:")
    
    # Method A: 10 separate calls
    model_a = Model('gpt-4o-mini', service_name='openai')
    start = time.time()
    for i in range(10):
        q.by(model_a).run()
    time_a = time.time() - start
    print(f"   10 separate calls: {time_a:.2f}s")
    
    # Method B: 1 call with n=10
    model_b = Model('gpt-4o-mini', service_name='openai', n=10)
    start = time.time()
    result_b = q.by(model_b).run()
    time_b = time.time() - start
    results_b = result_b.to_list()
    print(f"   1 call with n=10: {time_b:.2f}s")
    print(f"   Got {len(results_b)} results")
    
    if len(results_b) == 10:
        print(f"\n✅ n parameter works! Speedup: {time_a/time_b:.1f}x")
    else:
        print(f"\n❌ n parameter doesn't work as expected")

if __name__ == "__main__":
    test_n_parameter()