import os
from huggingface_hub import snapshot_download

def modelprep():
    hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
    if hf_token is None:
        raise RuntimeError("HUGGINGFACE_HUB_TOKEN environment variable not set")

    print("download snapshot Start")
    snapshot_download('stabilityai/stable-diffusion-xl-base-1.0',
                      local_dir='/workspace/stable-diffusion-xl-base-1.0',
                      token=hf_token,
                      resume_download=True)

    snapshot_download('madebyollin/sdxl-vae-fp16-fix',
                      local_dir='/workspace/sdxl-vae-fp16-fix',
                      token=hf_token,
                      resume_download=True)

    snapshot_download('diffusers/controlnet-depth-sdxl-1.0',
                      local_dir='/workspace/controlnet-depth-sdxl-1.0',
                      token=hf_token,
                      resume_download=True)

    print("download snapshot done")

if __name__ == '__main__':
    print("Worker Start")
    modelprep()
    
