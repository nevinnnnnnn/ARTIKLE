import logging
from typing import Generator
import threading
import time
import os
import warnings
import sys
import ctypes

# Suppress CUDA and library warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Suppress stderr for library warnings
class SuppressStderr:
    def __enter__(self):
        self._original_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        return self
    
    def __exit__(self, *args):
        sys.stderr.close()
        sys.stderr = self._original_stderr

logger = logging.getLogger(__name__)

class GPT4AllGenerator:
    def __init__(self):
        self.model = None
        self.model_lock = threading.Lock()
        self.model_type = None
        self.load_model()
    
    def load_model(self):
        """Load AI model - try multiple backends"""
        # Try GPT4All first
        if self._try_load_gpt4all():
            return
        
        # Try Ollama as fallback
        if self._try_load_ollama():
            return
        
        # Try transformers/HuggingFace as last resort
        if self._try_load_transformers():
            return
        
        logger.error("No AI models available - all backends failed")
        self.model = None
    
    def _try_load_gpt4all(self) -> bool:
        """Try to load GPT4All models"""
        try:
            logger.debug("Attempting to load GPT4All model...")
            
            # Suppress warnings during import and loading
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from gpt4all import GPT4All
            
            # Try different models - start with smallest for faster loading
            MODEL_OPTIONS = [
                "orca-mini-3b-gguf2-q4_0.gguf",
                "gpt4all-falcon-newbpe-q4_0.gguf",
                "mistral-7b-openorca.Q4_0.gguf",
            ]
            
            for model_name in MODEL_OPTIONS:
                try:
                    logger.debug(f"Loading GPT4All: {model_name}")
                    
                    # Suppress stderr for DLL warnings
                    with SuppressStderr():
                        self.model = GPT4All(model_name)
                    
                    self.model_type = "gpt4all"
                    logger.info(f"✓ GPT4All model loaded: {model_name}")
                    return True
                except Exception as e:
                    logger.debug(f"Failed to load {model_name}: {type(e).__name__}")
                    continue
            
            return False
        except ImportError:
            logger.debug("GPT4All not installed")
            return False
        except Exception as e:
            logger.debug(f"GPT4All error: {type(e).__name__}")
            return False
    
    def _try_load_ollama(self) -> bool:
        """Try to use Ollama as a local LLM service"""
        try:
            logger.info("Attempting to connect to Ollama...")
            import requests
            
            # Check if Ollama is running
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if models:
                    # Use first available model or prefer popular ones
                    preferred = [m for m in models if any(x in m['name'] for x in ['neural-chat', 'mistral', 'llama2'])]
                    selected_model = preferred[0]['name'] if preferred else models[0]['name']
                    logger.info(f"✓ Ollama connected, using model: {selected_model}")
                    self.model = {'type': 'ollama', 'model': selected_model, 'endpoint': 'http://localhost:11434'}
                    self.model_type = "ollama"
                    return True
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
        
        return False
    
    def _try_load_transformers(self) -> bool:
        """Try to load a HuggingFace transformers model"""
        try:
            logger.info("Attempting to load HuggingFace transformers model...")
            from transformers import pipeline
            
            # Use a small, efficient model
            logger.info("Loading distilgpt2 model (lightweight)...")
            pipe = pipeline("text-generation", model="distilgpt2", device=-1)  # CPU only
            self.model = pipe
            self.model_type = "transformers"
            logger.info("✓ Successfully loaded HuggingFace model")
            return True
        except ImportError:
            logger.debug("Transformers not installed")
            return False
        except Exception as e:
            logger.debug(f"Transformers loading failed: {e}")
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
        """Generate response using available model - thread-safe"""
        if not self.model:
            yield "Sorry, the AI model is not available at the moment. \n\nPlease ensure you have one of the following installed:\n- GPT4All: `pip install gpt4all`\n- Ollama running locally\n- PyTorch and Transformers: `pip install torch transformers`"
            return
        
        try:
            start_time = time.time()
            
            with self.model_lock:
                full_response = ""
                logger.info(f"Generating response ({self.model_type}) for: {question[:50]}...")
                
                if self.model_type == "gpt4all":
                    yield from self._generate_gpt4all(context, question)
                elif self.model_type == "ollama":
                    yield from self._generate_ollama(context, question)
                elif self.model_type == "transformers":
                    yield from self._generate_transformers(context, question)
                else:
                    yield "Unknown model type"
            
            end_time = time.time()
            generation_time = end_time - start_time
            logger.info(f"Response generated in {generation_time:.2f}s via {self.model_type}")
                
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            yield f"\n\nError: {str(e)}"
    
    def _generate_gpt4all(self, context: str, question: str) -> Generator[str, None, None]:
        """Generate using GPT4All"""
        prompt = self.format_prompt(context, question)
        try:
            for token in self.model.generate(prompt, streaming=True, max_tokens=512):
                yield token
        except Exception as e:
            logger.error(f"GPT4All generation error: {e}")
            yield f"Error: {str(e)}"
    
    def _generate_ollama(self, context: str, question: str) -> Generator[str, None, None]:
        """Generate using Ollama API"""
        import requests
        import json
        try:
            prompt = self.format_prompt(context, question)
            endpoint = f"{self.model['endpoint']}/api/generate"
            
            logger.info(f"Calling Ollama with model: {self.model['model']}")
            
            response = requests.post(
                endpoint,
                json={
                    "model": self.model['model'],
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "num_predict": 512,
                        "temperature": 0.1,  # Very low - deterministic, reduces hallucination
                        "top_p": 0.7,  # Reduced - less randomness
                        "top_k": 20,  # Reduced - restrict choices
                        "repeat_penalty": 1.2  # Reduce repetition
                    }
                },
                stream=True,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code}")
                yield f"Ollama Error {response.status_code}"
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
                            # Stop if done
                            if data.get('done', False):
                                break
                    except json.JSONDecodeError as e:
                        logger.debug(f"JSON decode error: {e}")
                        pass
                    except Exception as e:
                        logger.error(f"Line parsing error: {e}")
                        pass
            
            logger.info(f"Ollama response complete, total length: {len(full_text)}")
            
        except Exception as e:
            logger.error(f"Ollama generation error: {e}", exc_info=True)
            yield f"Error connecting to Ollama: {str(e)}"
    
    def _generate_transformers(self, context: str, question: str) -> Generator[str, None, None]:
        """Generate using HuggingFace transformers"""
        try:
            prompt = self.format_prompt(context, question)
            # Truncate prompt if too long
            if len(prompt) > 1024:
                prompt = prompt[-1024:]
            
            result = self.model(prompt, max_length=256, num_return_sequences=1, do_sample=False)
            text = result[0]['generated_text']
            # Get only the response part (after the prompt)
            response = text[len(prompt):].strip()
            yield response if response else "Unable to generate a response."
        except Exception as e:
            logger.error(f"Transformers generation error: {e}")
            yield f"Error: {str(e)}"

# Create global instance
gpt4all_generator = GPT4AllGenerator()