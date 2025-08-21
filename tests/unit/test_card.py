"""Unit tests for Card and Deck classes."""

import pytest
from themind.core.card import Card, Deck


class TestCard:
    def test_card_creation(self):
        card = Card(42)
        assert card.value == 42
        assert str(card) == "42"
        assert repr(card) == "Card(42)"
    
    def test_card_comparison(self):
        card1 = Card(10)
        card2 = Card(20)
        card3 = Card(10)
        
        assert card1 < card2
        assert card2 > card1
        assert card1 == card3
        assert card1 <= card3
        assert card2 >= card1
        assert card1 != card2
    
    def test_card_validation(self):
        with pytest.raises(ValueError, match="Card value must be between 1 and 100"):
            Card(0)
        with pytest.raises(ValueError, match="Card value must be between 1 and 100"):
            Card(101)
        with pytest.raises(ValueError, match="Card value must be between 1 and 100"):
            Card(-5)


class TestDeck:
    def test_deck_creation(self):
        deck = Deck()
        assert len(deck) == 100
        assert all(1 <= card.value <= 100 for card in deck.cards)
    
    def test_deck_custom_range(self):
        deck = Deck(min_value=1, max_value=50)
        assert len(deck) == 50
        assert all(1 <= card.value <= 50 for card in deck.cards)
    
    def test_deck_shuffle(self):
        deck1 = Deck()
        deck2 = Deck()
        
        deck1.shuffle(seed=42)
        deck2.shuffle(seed=42)
        
        assert [c.value for c in deck1.cards] == [c.value for c in deck2.cards]
        
        deck2.shuffle(seed=43)
        assert [c.value for c in deck1.cards] != [c.value for c in deck2.cards]
    
    def test_deck_deal(self):
        deck = Deck()
        deck.shuffle()
        
        initial_size = len(deck)
        cards = deck.deal(5)
        
        assert len(cards) == 5
        assert len(deck) == initial_size - 5
        assert all(isinstance(card, Card) for card in cards)
    
    def test_deck_deal_too_many(self):
        deck = Deck(min_value=1, max_value=5)
        with pytest.raises(ValueError, match="Not enough cards in deck"):
            deck.deal(10)
    
    def test_deck_reset(self):
        deck = Deck(min_value=1, max_value=10)
        deck.shuffle()
        deck.deal(5)
        
        assert len(deck) == 5
        
        deck.reset()
        assert len(deck) == 10
        assert all(1 <= card.value <= 10 for card in deck.cards)