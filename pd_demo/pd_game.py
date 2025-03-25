"""
Simplified Prisoner's Dilemma implementation with LLM player.
"""

import os
import openai
from typing import List, Dict, Tuple

class Strategy:
    """Base class for opponent strategies."""
    def __init__(self, name: str):
        self.name = name
        
    def get_move(self, history: List[str]) -> str:
        raise NotImplementedError

class TitForTat(Strategy):
    """Implements the Tit-for-Tat strategy."""
    def __init__(self):
        super().__init__("TitForTat")
        
    def get_move(self, history: List[str]) -> str:
        if not history:
            return 'cooperate'  # Start with cooperation
        return history[-1]  # Copy opponent's last move

class AlwaysDefect(Strategy):
    """Always defects."""
    def __init__(self):
        super().__init__("AlwaysDefect")
        
    def get_move(self, history: List[str]) -> str:
        return 'defect'

class AlwaysCooperate(Strategy):
    """Always cooperates."""
    def __init__(self):
        super().__init__("AlwaysCooperate")
        
    def get_move(self, history: List[str]) -> str:
        return 'cooperate'

STRATEGIES = {
    'TitForTat': TitForTat,
    'AlwaysDefect': AlwaysDefect,
    'AlwaysCooperate': AlwaysCooperate
}

class PDGame:
    """
    Simple implementation of Prisoner's Dilemma game with an LLM player.
    """
    
    def __init__(self, model: str = "gpt-3.5-turbo", temperature: float = 0.7):
        """
        Initialize the game with LLM configuration.
        
        Args:
            model: The OpenAI model to use
            temperature: Temperature for LLM responses (0.0 to 1.0)
        """
        self.model = model
        self.temperature = temperature
        
        # Set up OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        openai.api_key = api_key

    def get_llm_move(self, history: List[Tuple[str, str]]) -> str:
        """
        Get the next move from the LLM based on game history.
        
        Args:
            history: List of (llm_move, opponent_move) tuples
            
        Returns:
            'cooperate' or 'defect'
        """
        # Create a simple, focused prompt
        prompt = "You are playing the Prisoner's Dilemma game. For each round, both players choose to either cooperate or defect.\n\n"
        prompt += "Scoring:\n"
        prompt += "- Both cooperate: 3 points each\n"
        prompt += "- Both defect: 1 point each\n"
        prompt += "- One defects, one cooperates: Defector gets 5, Cooperator gets 0\n\n"
        
        # Add recent history (last 5 moves)
        if history:
            prompt += "Recent moves:\n"
            for i, (my_move, opp_move) in enumerate(history[-5:]):
                round_num = len(history) - len(history[-5:]) + i + 1
                prompt += f"Round {round_num}: You {my_move}, Opponent {opp_move}\n"
        
        prompt += "\nWhat is your next move? Answer with exactly one word: cooperate or defect"

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are playing Prisoner's Dilemma. Respond only with 'cooperate' or 'defect'."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=self.temperature,
                max_tokens=10
            )
            
            move = response.choices[0].message.content.strip().lower()
            return 'cooperate' if move not in ['cooperate', 'defect'] else move
            
        except Exception as e:
            print(f"Error getting LLM move: {str(e)}")
            return 'cooperate'  # Default to cooperation on error

    def play_match(self, strategy_name: str = "TitForTat", turns: int = 10) -> Dict:
        """
        Play a match against a specified strategy.
        
        Args:
            strategy_name: Name of the strategy to play against
            turns: Number of rounds to play
            
        Returns:
            Dictionary containing match results
        """
        try:
            # Create strategy instance
            strategy_class = STRATEGIES.get(strategy_name)
            if not strategy_class:
                raise ValueError(f"Strategy '{strategy_name}' not found")
            strategy = strategy_class()
            
        except Exception as e:
            raise ValueError(f"Error creating strategy: {str(e)}")

        history = []
        scores = {'llm': 0, 'strategy': 0}
        
        # Play the specified number of turns
        for turn in range(turns):
            # Get moves from both players
            llm_move = self.get_llm_move(history)
            strategy_move = strategy.get_move([h[0] for h in history])
            
            # Calculate scores
            if llm_move == strategy_move == 'cooperate':
                scores['llm'] += 3
                scores['strategy'] += 3
            elif llm_move == strategy_move == 'defect':
                scores['llm'] += 1
                scores['strategy'] += 1
            elif llm_move == 'cooperate':  # and strategy defected
                scores['strategy'] += 5
            else:  # llm defected and strategy cooperated
                scores['llm'] += 5
            
            # Record moves
            history.append((llm_move, strategy_move))

        return {
            'scores': scores,
            'history': history,
            'strategy': strategy_name,
            'turns': turns
        }

    @staticmethod
    def get_available_strategies() -> List[str]:
        """Get list of available strategies."""
        return list(STRATEGIES.keys()) 