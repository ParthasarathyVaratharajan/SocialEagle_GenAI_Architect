import google.generativeai as genai

genai.configure(api_key="AIzaSyCjnkh0RWVE-VCe966tjVD_oVYFXAD4mKg")


for m in genai.list_models():
    print(m.name, m.supported_generation_methods)

model = genai.GenerativeModel(model_name="models/gemini-2.5-pro-preview-03-25")
response = model.generate_content("Explain how AI works in a few words")

print(response.text)