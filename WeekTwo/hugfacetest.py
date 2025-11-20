from transformers import pipeline

generator = pipeline("text-generation", model="gpt2")
response = generator("Ceremonial pedagogy begins with", max_length=50, num_return_sequences=1)

print(response[0]['generated_text'])