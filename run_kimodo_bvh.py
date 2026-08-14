import os
import sys
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

from llm_planner import generate_motion_plan_with_llama70b
from motion_generator import KimodoMotionGenerator


def main():
    user_prompt = "Karakter masaya yürüsün ve bardağı alsın"
    print(f"[1] Kullanıcı Komutu: {user_prompt}")
    
    # 1. NVIDIA Kimodo Modelini Yükle (Pipeline v2 Pre-loading)
    print("\n[2] NVIDIA Kimodo Modeli Hazırlanıyor...")
    generator = KimodoMotionGenerator()
    generator._get_model()
    
    # 2. Llama 3.3 70B ile komutu analiz et
    print("\n[3] Meta Llama 3.3 70B ile Hareket Planı Çıkarılıyor...")
    plan = generate_motion_plan_with_llama70b(user_prompt)
    print(f" -> Plan: {plan}")
    
    english_prompt = plan.get("english_prompt", "The character walks to the table and picks up the glass")
    duration = float(plan.get("duration_seconds", 3.5))
    
    # 3. 3D Animasyon Üret
    print("\n[4] 3D Animasyon Üretiliyor...")
    bvh_file = generator.generate_3d_motion(
        prompt=english_prompt,
        duration=duration,
        output_dir="outputs",
        filename_prefix="motion_direct"
    )
    
    print("=" * 60)
    if bvh_file and os.path.exists(bvh_file):
        print(f"[BAŞARILI] GERÇEK 3D BVH ANİMASYON DOSYASI ÜRETİLDİ!")
        print(f"📁 BVH Dosya Yolu: {bvh_file}")
        print(f"📊 Dosya Boyutu: {os.path.getsize(bvh_file)} bytes")
    else:
        print("[HATA] Animasyon dosyası üretilemedi!")
    print("=" * 60)


if __name__ == "__main__":
    main()
