import os
import sys
import re
import shutil
import numpy as np
import torch
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv(override=True)
os.environ["LOCAL_CACHE"] = "true"
os.environ["TEXT_ENCODER_MODE"] = "local"


class KimodoMotionGenerator:
    def __init__(self, model_name: str = "kimodo-soma-rp-v1"):
        print("[Kimodo] Yerel NVIDIA Kimodo Üretici Modülü Başlatıldı.")
        self.model_name = model_name.lower()
        self._model = None

    def _get_model(self):
        if self._model is None:
            print("[Kimodo] NVIDIA Kimodo Modeli Bellek Yükleniyor...")
            try:
                from kimodo import load_model
                device = "cuda" if torch.cuda.is_available() else "cpu"
                use_fp32 = False
                self._model, _ = load_model(
                    self.model_name.lower(), 
                    device=device, 
                    text_encoder_fp32=use_fp32, 
                    return_resolved_name=True
                )


            except BaseException as e:
                print(f"[Kimodo Model Yükleme Hatası]: {type(e)} - {e}")
                import traceback
                traceback.print_exc()
                raise e

        return self._model


    def generate_3d_motion(self, prompt: str, duration: float = 4.0, output_dir: str = "outputs", filename_prefix: str = None):
        """
        Llama 3.3 70B'den gelen İngilizce açıklamayı alır ve Kimodo Python API'si 
        ile gerçek 3D BVH hareket animasyonu üretir.
        Her çalıştırmada benzersiz zaman damgalı dosya üretir.
        """
        abs_output_dir = os.path.abspath(output_dir)
        os.makedirs(abs_output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Prompt'tan temiz bir dosya adı etiketi (slug) oluşturalım
        slug = re.sub(r'[^a-zA-Z0-9]', '_', prompt.lower())
        slug = re.sub(r'_+', '_', slug).strip('_')[:30]
        
        if filename_prefix:
            stem_name = f"{filename_prefix}_{timestamp}"
        else:
            stem_name = f"motion_{timestamp}_{slug}" if slug else f"motion_{timestamp}"
            
        bvh_file = os.path.join(abs_output_dir, f"{stem_name}.bvh")
        npz_file = os.path.join(abs_output_dir, f"{stem_name}.npz")
        latest_bvh = os.path.join(abs_output_dir, "latest_motion.bvh")
        
        print(f"\n[Kimodo Gerçek Model İnfazı Başlatılıyor...]")
        print(f" ➔ İstek Metni: '{prompt}'")
        print(f" ➔ Süre: {duration} saniye")
        print(f" ➔ Çıktı Dosyaları: outputs/{stem_name}.bvh & outputs/{stem_name}.npz")
        
        try:
            model = self._get_model()
            from kimodo.exports.bvh import save_motion_bvh
            from kimodo.skeleton import global_rots_to_local_rots

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            fps = getattr(model, "fps", 30)
            num_frames = int(duration * fps)
            output = model(prompt, num_frames=num_frames, num_denoising_steps=25, post_processing=False, return_numpy=True, progress_bar=lambda x: x)




            
            skeleton = model.skeleton
            if hasattr(skeleton, "somaskel77"):
                skeleton = skeleton.somaskel77.to(device)

            joints_rot = torch.as_tensor(output["global_rot_mats"]).to(device)
            if joints_rot.ndim == 5:
                joints_rot = joints_rot[0]

            root_positions = torch.as_tensor(output["root_positions"]).to(device)
            if root_positions.ndim == 3:
                root_positions = root_positions[0]

            local_rot_mats = global_rots_to_local_rots(joints_rot, skeleton)

            
            save_motion_bvh(
                bvh_file,
                local_rot_mats,
                root_positions,
                skeleton=skeleton,
                fps=model.fps,
                standard_tpose=True
            )

            # Kinematik npz verisini kaydet
            np.savez(npz_file, **output)

            # En son üretilen animasyonu kolay erişim için latest_motion.bvh olarak kopyala
            shutil.copy2(bvh_file, latest_bvh)
            
            print(f"[Kimodo SUCCESS] Gerçek 3D Animasyon ({stem_name}.bvh) başarıyla üretildi!")
            print(f"📌 En son çıktı ayrıca kolay erişim için outputs/latest_motion.bvh olarak güncellendi.")
            return bvh_file
        except Exception as e:
            print(f"[Kimodo Çalışma Hatası]: {e}")
            import traceback
            traceback.print_exc()
            return None


