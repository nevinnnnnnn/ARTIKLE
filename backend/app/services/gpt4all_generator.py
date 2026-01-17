import logging
from typing import Generator
import threading
import time

logger = logging.getLogger(__name__)

class GPT4AllGenerator:
    def __init__(self):
        self.model = None
        self.model_lock = threading.Lock()
        self.load_model()
    
    def load_model(self):
        """Load GPT4All model"""
        try:
            logger.info("Loading GPT4All model...")
            # Import here to avoid dependency issues if not installed
            from gpt4all import GPT4All
            
            # Try different models
            MODEL_OPTIONS = [
                "orca-mini-3b-gguf2-q4_0.gguf",  # Default
                "gpt4all-falcon-newbpe-q4_0.gguf",  # Alternative
                "mistral-7b-openorca.Q4_0.gguf",   # Larger but better
            ]
            
            for model_name in MODEL_OPTIONS:
                try:
                    logger.info(f"Trying to load model: {model_name}")
                    self.model = GPT4All(model_name)
                    logger.info(f"Successfully loaded model: {model_name}")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load {model_name}: {e}")
                    continue
            
            logger.error("All GPT4All models failed to load")
            self.model = None
            
        except ImportError:
            logger.error("GPT4All package not installed. Run: pip install gpt4all")
            self.model = None
        except Exception as e:
            logger.error(f"Error loading GPT4All: {e}")
            self.model = None
    
    def format_prompt(self, context: str, question: str) -> str:
        """Format prompt for RAG with strict instructions"""
        return f"""### CONTEXT (Use ONLY this information):
{context}

### INSTRUCTION:
Answer the question based ONLY on the context above.
If the answer cannot be found in the context, say: "The question is irrelevant to the document content."
Do not use any outside knowledge.
Do not mention that you are using context.

### QUESTION:
{question}

### ANSWER (based ONLY on context):"""
    
    def generate_response(self, context: str, question: str) -> Generator[str, None, None]:
        """Generate response using GPT4All - thread-safe"""
        if not self.model:
            yield "AI model is not available. Please ensure GPT4All is installed and configured."
            return
        
        prompt = self.format_prompt(context, question)
        
        try:
            start_time = time.time()
            
            # Thread-safe generation
            with self.model_lock:
                full_response = ""
                logger.info(f"Generating response for question: {question[:50]}...")
                
                # Generate with streaming
                for token in self.model.generate(prompt, streaming=True):
                    full_response += token
                    yield token
            
            end_time = time.time()
            generation_time = end_time - start_time
            logger.info(f"Generated {len(full_response)} characters in {generation_time:.2f} seconds")
            
            # Add generation time info (optional)
            if generation_time > 5:
                yield f"\n\n[Generated in {generation_time:.1f} seconds]"
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            yield "Error generating AI response. Please try again."

# Create global instance
gpt4all_generator = GPT4AllGenerator()