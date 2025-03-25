"""
Flask web application for the Prisoner's Dilemma demo.
"""

from flask import Flask, render_template, request, jsonify
from pd_game import PDGame
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    """Render the main page."""
    # Get list of available strategies
    strategies = PDGame.get_available_strategies()
    
    # Get list of available models
    models = [
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo-preview"
    ]
    
    return render_template('index.html',
                         strategies=strategies,
                         models=models)

@app.route('/play', methods=['POST'])
def play():
    """Play a match with the specified configuration."""
    try:
        data = request.get_json()
        
        # Create game instance with specified model
        game = PDGame(
            model=data.get('model', 'gpt-3.5-turbo'),
            temperature=float(data.get('temperature', 0.7))
        )
        
        # Play match against specified strategy
        result = game.play_match(
            strategy_name=data.get('strategy', 'TitForTat'),
            turns=int(data.get('turns', 10))
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 