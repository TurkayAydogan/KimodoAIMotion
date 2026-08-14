import os
import sys
import json
from dotenv import load_dotenv

# Windows konsol Türkçe/UTF-8 uyumluluğu
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv(override=True)
os.environ["LOCAL_CACHE"] = "true"
os.environ["TEXT_ENCODER_MODE"] = "local"

from llm_planner import generate_motion_plan_with_llama70b
from motion_generator import KimodoMotionGenerator


def run_pipeline(user_prompt: str, override_duration: float = None) -> bool:
    print("=" * 60)
    print("[PIPELINE] META LLAMA 3.3 70B + NVIDIA KIMODO + HUGGING FACE")
    print("=" * 60)
    
    print(f"\n[Adım 1] Kullanıcı Türkçe Doğal Dil Komutu:")
    print(f" ➔ '{user_prompt}'")
    
    print(f"\n[Adım 2] Yerel NVIDIA Kimodo 3D Model Belleğe Yükleniyor...")
    kimodo = KimodoMotionGenerator()
    kimodo._get_model()

    print(f"\n[Adım 3] Meta Llama 3.3 70B (Hugging Face API) Çağrılıyor...")
    motion_plan = generate_motion_plan_with_llama70b(user_prompt)
    
    print("\n[Llama 3.3 70B Analiz Sonucu]:")
    print(json.dumps(motion_plan, indent=2, ensure_ascii=False))
    
    english_prompt = motion_plan.get("english_prompt", user_prompt)
    duration = override_duration if override_duration is not None else motion_plan.get("duration_seconds", 3.5)
    
    print(f"\n[Adım 4] 3D Animasyon Üretiliyor (Süre: {duration}s)...")
    output_path = kimodo.generate_3d_motion(
        prompt=english_prompt,
        duration=duration,
        output_dir="outputs"
    )

    print("=" * 60)
    if output_path and os.path.exists(output_path):
        print("[BAŞARILI] İŞLEM TAMAMLANDI!")
        print(f"📁 Oluşan 3D Hareket Dosyası: {output_path}")
        print(f"🔗 Sabit Takip Dosyası: outputs/latest_motion.bvh")
        print("=" * 60)
        return True
    else:
        print("[HATA] 3D Hareket Dosyası Oluşturulamadı!")
        print("=" * 60)
        return False


if __name__ == "__main__":
    override_dur = None
    args = sys.argv[1:]
    
    # CLI argümanlarını ayrıştır
    cleaned_args = []
    i = 0
    while i < len(args):
        if args[i] == "--duration" and i + 1 < len(args):
            override_dur = float(args[i + 1])
            i += 2
        elif args[i].startswith("--duration="):
            override_dur = float(args[i].split("=")[1])
            i += 1
        else:
            cleaned_args.append(args[i])
            i += 1

    if cleaned_args:
        command = " ".join(cleaned_args)
    else:
        command = "Robot ileri doğru 3 adım yürüsün, dursun ve sağ elini kaldırsın."
        
    try:
        success = run_pipeline(command, override_duration=override_dur)
        sys.exit(0 if success else 1)
    except BaseException as e:
        print(f"\n[CRITICAL ERROR]: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
