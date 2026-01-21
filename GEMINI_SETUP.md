# Gemini API Integration

This system now uses Google's Gemini API for both text generation (chat) and embeddings.

## Quick Start

### 1. Get Your API Key

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Click "Get API Key" 
3. Create a new API key in your Google Cloud project
4. Copy the API key

### 2. Configure Environment

Create a `.env` file in the backend directory (or set environment variables):

```bash
# .env file
GEMINI_API_KEY=your_api_key_here
```

Or set environment variable:
```bash
# Linux/Mac
export GEMINI_API_KEY="your_api_key_here"

# Windows PowerShell
$env:GEMINI_API_KEY="your_api_key_here"
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Test the Integration

```bash
python test_gemini_integration.py
```

Expected output:
```
✓ GEMINI_API_KEY is set
✓ google.generativeai imported successfully
✓ Gemini service modules imported successfully
✓ Successfully generated embedding
✓ Successfully generated response
```

## Architecture Changes

### Before (Ollama-based)
```
User Query
    ↓
Chat Service
    ├→ ollama_generator.py (LLaMA3-ChatQA local)
    └→ ollama_embeddings.py (nomic-embed-text local)
    ↓
Response
```

### After (Gemini API-based)
```
User Query
    ↓
Chat Service
    ├→ gemini_service.py → Gemini API (cloud-based)
    │  ├→ GeminiChat (text generation)
    │  └→ GeminiEmbeddings (embeddings)
    ↓
Response
```

## Files Changed

### New Files
- `backend/app/services/gemini_service.py` - Gemini API wrapper

### Updated Files
- `backend/app/services/__init__.py` - Updated imports
- `backend/app/services/chat_service.py` - Uses Gemini LLM
- `backend/app/utils/vector_store.py` - Uses Gemini embeddings
- `backend/app/config.py` - Added Gemini API key configuration
- `backend/requirements.txt` - Added google-generativeai

### Removed Files
- `backend/app/services/ollama_embeddings.py` ✓ Deleted
- `backend/app/services/ollama_generator.py` ✓ Deleted

## Key Features

### GeminiEmbeddings
- Uses `models/embedding-001` model
- 768-dimensional embeddings (compatible with previous nomic-embed-text)
- LRU cache for performance
- Direct API calls via Google SDK

### GeminiChat
- Uses `gemini-1.5-flash` for fast, efficient responses
- Configurable temperature and max tokens
- System prompts to prevent hallucination
- Context-aware responses

## Configuration

### Embedding Dimension
The Gemini embedding dimension is 768, matching the previous nomic-embed-text embeddings. Existing vector stores are compatible.

### Temperature & Tokens
Default chat settings:
```python
temperature=0.3  # Lower = more deterministic
max_tokens=1024  # Maximum response length
```

## Troubleshooting

### API Key Error
```
ERROR: GEMINI_API_KEY not set
```
**Solution:** Ensure API key is set in environment variables or .env file

### Import Error
```
ModuleNotFoundError: No module named 'google'
```
**Solution:** Run `pip install google-generativeai`

### Rate Limiting
If you hit rate limits, the Gemini API will return an error. Gemini has generous free tier limits.

### Embedding Mismatch
Old vector stores with nomic-embed-text embeddings can still be used but new documents will use Gemini embeddings. Consider regenerating old embeddings for consistency.

## Testing

Run the test suite:
```bash
python test_gemini_integration.py
```

Or test in your Python code:
```python
from app.services.gemini_service import GeminiChat, GeminiEmbeddings

# Test embeddings
embedding = GeminiEmbeddings.create_embedding("test text")

# Test chat
response = GeminiChat.generate_response(
    query="What is AI?",
    context_text="AI is artificial intelligence...",
    temperature=0.3
)
```

## Costs

- **Embeddings**: Free tier available
- **Chat/Text Generation**: Free tier available with usage limits
- Check [Google AI Pricing](https://ai.google.dev/pricing) for details

## Migration from Ollama

The migration is complete! The system no longer requires:
- Ollama server running locally
- Local model downloads (llama3-chatqa, nomic-embed-text)
- GPU/CPU resources for inference

All functionality is now cloud-based via Gemini API.
