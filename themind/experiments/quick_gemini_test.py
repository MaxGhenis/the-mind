"""Quick test of Gemini models on The Mind - single round comparison."""

import os
from edsl import Model, QuestionFreeText

os.environ['EXPECTED_PARROT_API_KEY'] = os.environ.get('EXPECTED_PARROT_API_KEY', '')


def test_model(model_name: str, card_values: list) -> list:
    """Test a model's timing decisions for given cards."""
    
    model = Model(model_name)
    wait_times = []
    
    print(f"\n{model_name}:")
    
    for i, card in enumerate(card_values, 1):
        prompt = f"""The Mind game: You have card {card}.
Cards 1-33 wait 0-10 seconds, 34-66 wait 10-20 seconds, 67-100 wait 20-30 seconds.
Reply with ONLY a number (seconds to wait):"""
        
        q = QuestionFreeText(question_name="wait", question_text=prompt)
        
        try:
            result = q.by(model).run()
            response = str(result.select("answer.wait").first())
            
            # Extract number
            for word in response.split():
                try:
                    wait = float(word.replace(',', '.'))
                    wait = max(0, min(30, wait))
                    wait_times.append(wait)
                    print(f"  Card {card}: {wait:.1f}s")
                    break
                except:
                    continue
            else:
                # Fallback
                wait = card / 100 * 30
                wait_times.append(wait)
                print(f"  Card {card}: {wait:.1f}s (fallback)")
                
        except Exception as e:
            print(f"  Card {card}: Error - {e}")
            wait_times.append(card / 100 * 30)
    
    return wait_times


def main():
    """Quick comparison of Gemini models."""
    
    print("="*60)
    print("QUICK GEMINI COMPARISON - The Mind")
    print("="*60)
    
    # Test cards: low, medium, high
    test_cards = [15, 50, 85]
    
    print(f"\nTest cards: {test_cards}")
    print("Expected: increasing wait times")
    
    # Test Flash Lite
    lite_times = test_model("gemini-2.5-flash-lite", test_cards)
    
    # Test Flash
    flash_times = test_model("gemini-2.5-flash", test_cards)
    
    # Analysis
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    
    print(f"\ngemini-2.5-flash-lite: {lite_times}")
    print(f"gemini-2.5-flash:      {flash_times}")
    
    # Check if ordering is correct
    lite_correct = lite_times == sorted(lite_times)
    flash_correct = flash_times == sorted(flash_times)
    
    print(f"\nCorrect ordering (increasing times):")
    print(f"  Flash Lite: {'✓' if lite_correct else '✗'}")
    print(f"  Flash:      {'✓' if flash_correct else '✗'}")
    
    # Compare spread (better differentiation)
    lite_spread = max(lite_times) - min(lite_times)
    flash_spread = max(flash_times) - min(flash_times)
    
    print(f"\nTime spread (larger is better):")
    print(f"  Flash Lite: {lite_spread:.1f}s")
    print(f"  Flash:      {flash_spread:.1f}s")
    
    print("\n" + "-"*60)
    if lite_correct and not flash_correct:
        print("WINNER: Gemini 2.5 Flash Lite - better coordination logic")
    elif flash_correct and not lite_correct:
        print("WINNER: Gemini 2.5 Flash - better coordination logic")
    elif flash_spread > lite_spread * 1.2:
        print("WINNER: Gemini 2.5 Flash - better time differentiation")
    elif lite_spread > flash_spread * 1.2:
        print("WINNER: Gemini 2.5 Flash Lite - better time differentiation")
    else:
        print("RESULT: Similar performance")
    
    print("\nNote: This is a quick test. Full experiments needed for statistical significance.")


if __name__ == "__main__":
    main()