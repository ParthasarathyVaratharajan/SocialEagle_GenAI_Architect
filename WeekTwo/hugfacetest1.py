from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

# Step 1: Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased")

# Step 2: Prepare input text
text = "Planetary pedagogy is poetic governance"
inputs = tokenizer(text, return_tensors="pt")

# Step 3: Run inference
outputs = model(**inputs)

# Step 4: Extract logits and convert to probabilities
logits = outputs.logits
probs = F.softmax(logits, dim=1)

# Step 5: Display results
print("Logits:", logits)
print("Probabilities:", probs)