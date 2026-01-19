"""
Ollama LLM Generator - Using Mistral or other available models
No GPT4All dependency required
"""

import logging
import requests
import json
import time
import threading
from typing import Generator, Optional, Dict, Any

logger = logging.getLogger(__name__)

class OllamaGenerator:
    """Generate responses using Ollama API - Mistral model"""
    
    def __init__(self, endpoint: str = "http://localhost:11434", default_model: str = "mistral"):
        self.endpoint = endpoint
        self.default_model = default_model
        self.model_lock = threading.Lock()
        self.model_type = "ollama"
        self.available_model = None
        self.verify_connection()
    
    def verify_connection(self):
        """Check if Ollama is running and get available models"""
        try:
            logger.info(f"Connecting to Ollama at {self.endpoint}...")
            response = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                if models:
                    # Try to use preferred models
                    model_names = [m.get('name', '').lower() for m in models]
                    
                    # Prefer Mistral
                    if any('mistral' in m for m in model_names):
                        self.available_model = next(m for m in [m.get('name') for m in models] 
                                                   if 'mistral' in m.lower())
                    # Fallback to first available
                    else:
                        self.available_model = models[0].get('name')
                    
                    logger.info(f"✓ Ollama connected successfully")
                    logger.info(f"✓ Using model: {self.available_model}")
                    return True
            else:
                logger.warning(f"Ollama returned status code {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Cannot connect to Ollama at {self.endpoint}")
            logger.info("Make sure Ollama is running: ollama serve")
        except Exception as e:
            logger.error(f"Error connecting to Ollama: {e}")
        
        return False
    
    def format_prompt(self, context: str, question: str) -> str:
        """Format prompt for RAG - Anti-hallucination version"""
        return f"""You are a helpful assistant that answers questions ONLY based on the provided document content.

**STRICT RULES:**
1. ONLY use information from the document below
2. If the answer is NOT in the document, respond: "I cannot find this information in the document."
3. Always cite which part of the document your answer comes from
4. Do NOT make up, infer, or add information not in the document
5. If unsure, say "I'm not certain about this based on the document"

Document Content:
{context}

Question: {question}

Answer (based only on the document above):"""
    
    def generate_response(self, context: str, question: str) -> Generator[str, None, None]:
        """
        Generate response using Ollama API
        Streams tokens as they're generated
        """
        if not self.available_model:
            yield "ERROR: Ollama is not available. Please ensure Ollama is running.\n"
            yield "Run: ollama serve\n"
            yield f"Expected at: {self.endpoint}"
            return
        
        try:
            start_time = time.time()
            prompt = self.format_prompt(context, question)
            
            logger.info(f"Generating response via Ollama ({self.available_model})")
            logger.debug(f"Question: {question[:50]}...")
            
            endpoint = f"{self.endpoint}/api/generate"
            
            payload = {
                "model": self.available_model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "num_predict": 512,
                    "temperature": 0.1,      # Very low - deterministic, reduces hallucination
                    "top_p": 0.7,            # Reduced - less randomness
                    "top_k": 20,             # Reduced - restrict choices
                    "repeat_penalty": 1.2    # Reduce repetition
                }
            }
            
            logger.debug(f"Calling Ollama API: {endpoint}")
            
            response = requests.post(
                endpoint,
                json=payload,
                stream=True,
                timeout=120  # 2 minute timeout for long responses
            )
            
            if response.status_code != 200:
                error_msg = f"Ollama API error: HTTP {response.status_code}"
                logger.error(error_msg)
                yield f"ERROR: {error_msg}\n"
                return
            
            full_text = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if 'response' in data:
                            chunk = data['response']
                            full_text += chunk
                            yield chunk
                            
                            # Stop if generation is done
                            if data.get('done', False):
                                logger.debug(f"Ollama finished generation")
                                break
                    except json.JSONDecodeError as e:
                        logger.debug(f"JSON decode error on line: {e}")
                    except Exception as e:
                        logger.error(f"Error processing line: {e}")
            
            end_time = time.time()
            generation_time = end_time - start_time
            logger.info(f"Response generated in {generation_time:.2f}s")
            logger.info(f"Response length: {len(full_text)} characters")
            
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out (120s)")
            yield "\nERROR: Request timed out. The response took too long to generate."
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to Ollama: {e}")
            yield f"\nERROR: Cannot connect to Ollama at {self.endpoint}"
            yield "\nMake sure Ollama is running: ollama serve"
        except Exception as e:
            logger.error(f"Ollama generation error: {e}", exc_info=True)
            yield f"\nERROR: {str(e)}"


# Create global instance
ollama_generator = OllamaGenerator()
