import os
import sys
import torch
import json
from dotenv import load_dotenv
from huggingface_hub import login

load_dotenv()
token = os.getenv("HF_TOKEN")
if token:
    login(token)

from llm_planner import generate_motion_plan_with_llama70b
from kimodo import load_model
from kimodo.exports.bvh import save_motion_bvh
from kimodo.skeleton import global_rots_to_local_rots

def main():
    user_prompt = "Karakter masaya yürüsün ve bardağı alsın"
    print(f"[1] Kullanıcı Komutu: {user_prompt}")
    
    # 1. Llama 3.3 70B ile komutu İngilizceye çevir
    plan = generate_motion_plan_with_llama70b(user_prompt)
    print(f"[2] Llama 3.3 70B Planı: {plan}")
    
    english_prompt = plan.get("english_prompt", "The character walks to the table and picks up the glass")
    duration = float(plan.get("duration_seconds", 3.5))
    
    # 2. NVIDIA Kimodo Modelini Yükle ve 3D Hareket Üret
    print(f"[3] NVIDIA Kimodo Modeli Yükleniyor ve 3D Animasyon Üretiliyor...")
    model, resolved = load_model("Kimodo-SOMA-RP-v1", return_resolved_name=True)
    device = torch.device("cpu")
    
    output = model(english_prompt, duration=duration, num_samples=1)
    
    from datetime import datetime
    import shutil
    
    # 3. .bvh 3D Animasyon Dosyası Olarak Kaydet
    output_dir = os.path.abspath("outputs")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bvh_file = os.path.join(output_dir, f"motion_direct_{timestamp}.bvh")
    
    skeleton = model.skeleton
    if hasattr(skeleton, "somaskel77"):
        skeleton = skeleton.somaskel77.to(device)
        
    joints_pos = torch.from_numpy(output["posed_joints"][0]).to(device)
    joints_rot = torch.from_numpy(output["global_rot_mats"][0]).to(device)
    local_rot_mats = global_rots_to_local_rots(joints_rot, skeleton)
    root_positions = joints_pos[:, skeleton.root_idx, :]
    
    save_motion_bvh(
        bvh_file,
        local_rot_mats,
        root_positions,
        skeleton=skeleton,
        fps=model.fps,
        standard_tpose=True
    )
    
    print("=" * 60)
    print(f"[BAŞARILI] GERÇEK 3D BVH ANİMASYON DOSYASI ÜRETİLDİ!")
    print(f"📁 BVH Dosya Yolu: {bvh_file}")
    print(f"📊 Dosya Boyutu: {os.path.getsize(bvh_file)} bytes")
    print("=" * 60)

if __name__ == "__main__":
    main()
