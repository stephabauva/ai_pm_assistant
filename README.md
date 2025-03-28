# AI-Powered Product Management Assistant

An AI-powered web application for product managers, focusing on competitive analysis using LLMs with structured outputs via Pydantic AI.

## Features

- **Multi-Model Support**: Use Ollama, LMStudio (local), or Gemini (cloud) for AI processing
- **Structured AI Responses**: Leverages Pydantic AI for consistent, structured outputs
- **Competitive Analysis**: Get detailed insights about competitors and market trends
- **Modern UI**: Clean interface built with FastHTML and Tailwind CSS
- **Google OAuth Authentication**: Secure user authentication

## Technical Stack

- **Frontend**: FastHTML with Tailwind CSS
- **Backend**: FastAPI (Python)
- **AI Framework**: Pydantic AI for structured outputs
- **Session Management**: Redis
- **Authentication**: Google OAuth2

## Getting Started

### Prerequisites

- Python 3.8+
- Redis server running locally
- For local models:
  - Ollama with llama3 model installed
  - LMStudio (optional)
- For cloud models:
  - Gemini API key

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai_pm_assistant.git
   cd ai_pm_assistant
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv ai_pm_assistant
   source ai_pm_assistant/bin/activate  # On Windows: ai_pm_assistant\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   cp .env.example .env
   ```
   Edit `.env` to add your Gemini API key and adjust other settings as needed.

5. Run the application:
   ```
   python main.py
   ```

6. Open your browser and navigate to `http://localhost:5001`

## Using Pydantic AI

This application uses Pydantic AI to create structured outputs from LLM responses. The main components are:

- `CompetitorInfo`: Model for competitor details
- `MarketTrend`: Model for market trend information
- `CompetitiveAnalysis`: AI model that structures the complete analysis

Example usage:
```python
from ai_agent import AIClient

client = AIClient()
result = await client.analyze_competition("Analyze CRM market competitors", "ollama")
```

## Testing

Run tests with pytest:
```
pytest
```

## Project Structure

- `main.py`: Application entry point
- `auth.py`: Google OAuth authentication
- `dashboard.py`: Main UI components
- `analysis.py`: LLM query processing
- `ai_agent.py`: Pydantic AI implementation
- `utils.py`: Utility functions
- `tests/`: Test files

## License

MIT