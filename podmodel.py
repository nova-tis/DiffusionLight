import os
from huggingface_hub import snapshot_download

def modelprep():
    hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
    if hf_token is None:
        raise RuntimeError("HUGGINGFACE_HUB_TOKEN environment variable not set")

    print("download snapshot Start")
    snapshot_download('stabilityai/stable-diffusion-xl-base-1.0',
                      local_dir='/data/models/stable-diffusion-xl-base-1.0',
                      token=hf_token,
                      force_download=False,
                      resume_download=True)
    print("download snapshot 1 done")
    snapshot_download('madebyollin/sdxl-vae-fp16-fix',
                      local_dir='/data/models/sdxl-vae-fp16-fix',
                      token=hf_token,
                      force_download=False,
                      resume_download=True)
    print("download snapshot 2 done")
    snapshot_download('diffusers/controlnet-depth-sdxl-1.0',
                      local_dir='/data/models/controlnet-depth-sdxl-1.0',
                      token=hf_token,
                      force_download=False,
                      resume_download=True)

    print("download snapshot 3 done")

if __name__ == '__main__':
    print("Worker Start")
    modelprep()
    
