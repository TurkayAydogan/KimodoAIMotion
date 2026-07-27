import os
import sys
import json
from llm_planner import generate_motion_plan_with_llama70b
from motion_generator import KimodoMotionGenerator

# Windows konsol Türkçe/UTF-8 uyumluluğu
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def run_pipeline(user_prompt: str):
    print("=" * 60)
    print("[PIPELINE] META LLAMA 3.3 70B + NVIDIA KIMODO + HUGGING FACE")
    print("=" * 60)
    
    print(f"\n[Adim 1] Kullanici Turkce Dogal Dil Komutu:")
    print(f" -> '{user_prompt}'")
    
    print(f"\n[Adim 2] Meta Llama 3.3 70B (Hugging Face API) Cagriliyor...")
    motion_plan = generate_motion_plan_with_llama70b(user_prompt)
    
    print("\n[Llama 3.3 70B Analiz Sonucu]:")
    print(json.dumps(motion_plan, indent=2, ensure_ascii=False))
    
    print(f"\n[Adim 3] NVIDIA Kimodo 3D Motion Generator Cagriliyor...")
    kimodo = KimodoMotionGenerator()
    
    english_prompt = motion_plan.get("english_prompt", user_prompt)
    duration = motion_plan.get("duration_seconds", 3.5)
    
    output_path = kimodo.generate_3d_motion(
        prompt=english_prompt,
        duration=duration,
        output_dir="outputs"
    )
    
    print("=" * 60)
    if output_path and os.path.exists(output_path):
        print(f"[BAŞARILI] İŞLEM TAMAMLANDI!")
        print(f"📁 Oluşan 3D Hareket Dosyası: {output_path}")
        print(f"🔗 Sabit Takip Dosyası: outputs/latest_motion.bvh")
    else:
        print(f"[HATA] 3D Hareket Dosyası Oluşturulamadı!")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
    else:
        command = "Robot ileri doğru 3 adım yürüsün, dursun ve sağ elini kaldırsın."
        
    run_pipeline(command)
