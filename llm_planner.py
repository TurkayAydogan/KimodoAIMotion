import os
import re
import json
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
token = os.getenv("HF_TOKEN")

if not token:
    raise ValueError("HF_TOKEN .env dosyasında bulunamadı! Lütfen .env dosyanızı kontrol edin.")

# Hugging Face Inference Client ile Llama 3.3 70B Bağlantısı
client = InferenceClient(api_key=token)

SYSTEM_PROMPT = """You are an expert AI 3D Motion Planner. Your task is to analyze user text requests (which may be in Turkish or English) and convert them into precise English prompts and structured parameters for NVIDIA Kimodo.

Return ONLY a raw JSON object (without markdown code blocks) matching this format:
{
  "english_prompt": "Clear, detailed English motion description",
  "duration_seconds": 4.0,
  "action_type": "locomotion / interaction / gesture",
  "notes": "Short summary of what the character should do"
}
"""

def generate_motion_plan_with_llama70b(user_command: str) -> dict:
    """
    Kullanıcının doğal dildeki komutunu Meta Llama 3.3 70B kullanarak
    NVIDIA Kimodo için 3D hareket planına çevirir.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_command}
    ]
    
    # Meta Llama 3.3 70B Instruct modelini çağırıyoruz
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct",
        messages=messages,
        max_tokens=400,
        temperature=0.3
    )
    
    content = response.choices[0].message.content.strip()
    
    # Markdown kod bloklarını temizle
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
    if content.endswith("```"):
        content = content.rsplit("\n", 1)[0]
    if content.startswith("json"):
        content = content[4:].strip()
        
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Yanıt içinde JSON bloğunu regex ile bulmayı dene
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise

if __name__ == "__main__":
    test_input = "Karakter masaya yürüsün ve kutuyu kaldırsın"
    print(f"Test komutu: {test_input}")
    plan = generate_motion_plan_with_llama70b(test_input)
    print("Llama 3.3 70B Ürettiği Plan:")
    print(json.dumps(plan, indent=2, ensure_ascii=False))
