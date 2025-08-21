"""
themind: LLM agents playing The Mind card game.

A research package for studying emergent coordination in multi-agent
LLM systems through The Mind card game.
"""

__version__ = "0.1.0"

from themind.core.card import Card, Deck
from themind.core.player import Player, LLMPlayer

__all__ = [
    "Player",
    "LLMPlayer", 
    "Card",
    "Deck",
]