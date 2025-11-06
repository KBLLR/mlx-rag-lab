
# Phi-3 Vision MLX Examples

## 1. Decoding Strategies

### **Code Generation with Constrained Decoding**
```python
from phi_3_vision_mlx import constrain

# Prompt for generating a factorial function
prompt = "Write a Python function to calculate the factorial of a given number n."

# Constraints
constraints = [
    (100, "\n```python\n"),  # Begin code block
    (150, " def "),            # Ensure a function definition
    (200, " return "),         # Ensure a return statement
    (250, "\n```")            # End code block
]

# Generate code with constraints
generated_code = constrain(prompt, constraints, use_beam=False)
print(generated_code)
```

### **Multiple Choice Question Answering**
#### **Constrained Decoding for Structured Answers**
```python
from phi_3_vision_mlx import constrain

# Prompt for a multiple-choice question
prompt = (
    "Which of the following gases is the primary contributor to the greenhouse effect? "
    "A: Oxygen B: Nitrogen C: Carbon Dioxide D: Methane E: Ozone"
)

# Constraints to structure the output
constraints = [
    (0, '\nThe'), 
    (50, ' correct answer is '), 
    (1, 'C.')  # Suggesting Carbon Dioxide as the answer
]

# Generate structured answer
answer = constrain(prompt, constraints, use_beam=True)
print(answer)
```

#### **Choosing from Options**
```python
from phi_3_vision_mlx import choose

# Prompt with a history-related question
prompt = (
    "Who was the first President of the United States? "
    "A: Thomas Jefferson B: Abraham Lincoln C: George Washington D: John Adams E: James Madison"
)

# Choose the correct answer
chosen_answer = choose([prompt], choices='ABCDE')
print(chosen_answer)
```

## 2. LoRA (Low-Rank Adaptation)

### **Training a LoRA Adapter**
```python
from phi_3_vision_mlx import train_lora

# Training a LoRA adapter
train_lora(
    lora_layers=4,    # Apply LoRA to 4 layers
    lora_rank=8,      # Low rank for efficiency
    epochs=5,         # Short training cycle
    lr=5e-5,          # Lower learning rate
    warmup=0.2,       # Shorter warmup period
    dataset_path="datasets/sentiment_analysis"  # Dataset for training
)
```

### **Testing LoRA Adapters**
```python
from phi_3_vision_mlx import test_lora

# Without LoRA adapter
baseline = test_lora(adapter_path=None)
print("Baseline performance:", baseline)

# With a specific LoRA adapter
lora_adapter = test_lora(adapter_path="adapters/translation_adapter")
print("With LoRA adapter:", lora_adapter)
```

## 3. Agent Interactions

### **Multi-turn Visual Question Answering (VQA)**
```python
from phi_3_vision_mlx import Agent

# Initialize the agent
agent = Agent()

# Multi-turn interaction
agent('Describe the main object in this image.', 'https://example.com/image1.jpg')
agent('What is the estimated time period of the object?')
agent('Provide cultural significance of this object.')
agent.end()
```

### **Generative Feedback Loop**
```python
agent('Plot a 2D sine wave.')
agent('Modify the plot to include cosine wave.')
agent('Adjust the axis labels to "Time" and "Amplitude".')
agent.end()
```

### **API Tool Use**
```python
agent('Generate an image of "a futuristic city at sunset, cyberpunk style".')
agent.end()

agent('Describe the generated image as if narrating a story.')
agent('Speak the description aloud.')
agent.end()
```

## 4. Toolchain

### **LLM Backend Hotswap**
```python
from phi_3_vision_mlx import Agent

# Initialize the agent with a general-purpose model
agent = Agent(toolchain="responses, history = gpt_api(prompt, history)")

# Ask general questions
agent('Write a short story about a futuristic city.')
agent('Summarize the main themes of the story.')
agent.end()

# Switch to a medical-specific model
agent = Agent(toolchain="responses, history = medqa_api(prompt, history)")

# Ask medical questions
agent('Write a detailed neurology ICU admission note.')
agent('Provide differential diagnoses for sudden loss of consciousness.')
agent.end()
```

## 5. Miscellaneous

### **In-Context Learning (ICL)**
```python
from phi_3_vision_mlx import add_text

# Adding a reference text
add_text('How to use the OpenWeatherMap API to fetch weather data: @https://openweathermap.org/api.')

# Querying the model
query = 'Explain how to set up authentication for this API.'
response = add_text(query)
print(response)
```

### **Retrieval-Augmented Generation (RAG)**
```python
from phi_3_vision_mlx import rag

# Query for financial analysis
response = rag('Analyze the volatility of Bitcoin versus Ethereum over the past year.')
print(response)
```

### **Multimodal Reddit Thread Summarizer**
```python
try:
    from rd2md import rd2md
    from pathlib import Path
    import json

    # Extract Reddit thread
    filename, contents, images = rd2md()

    # Summarize the thread
    prompt = (
        'Summarize the Reddit thread above in 200 words, highlighting key arguments, opinions, and consensus without quoting specific users.'
    )
    prompts = [f'{s}\n\n{prompt}' for s in contents]

    # Generate summaries for each segment
    results = [
        pv.generate(prompts[i], images[i], max_tokens=512, blind_model=False, quantize_model=True, quantize_cache=False, verbose=False)
        for i in range(len(prompts))
    ]

    # Save the summaries to a file
    with open(Path(filename).with_suffix('.json'), 'w') as f:
        json.dump({'prompts': prompts, 'images': images, 'results': results}, f, indent=4)

except Exception as e:
    print("Error:", e)
    print("Install 'rd-to-md' package for this example: pip install rd-to-md")
```

## 6. Benchmark

### **Benchmarking Model Performance**
```python
from phi_3_vision_mlx import benchmark

# Run benchmarks
results = benchmark(
    tasks=['translation', 'summarization', 'question_answering'],
    dataset='WMT20_en_de',  # Example dataset for translation
    metrics=['BLEU', 'ROUGE', 'Accuracy']
)
print(results)
```

---

Enjoy exploring the power of Phi-3 Vision MLX!
