FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    CONDA_DIR=/opt/conda \
    PATH=/opt/conda/bin:$PATH \
    PYTHONUNBUFFERED=1

ARG CACHE_BUST=1

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
    curl \
    wget \
    git \
    openssh-server \
    sudo \
    bzip2 \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p $CONDA_DIR && \
    rm /tmp/miniconda.sh && \
    $CONDA_DIR/bin/conda clean -afy


# Create non-root user
RUN useradd -ms /bin/bash devuser && \
    echo "devuser:devpassword" | chpasswd && \
    adduser devuser sudo

RUN mkdir -p /models && chown devuser:devuser /models
# SSH setup
RUN mkdir /var/run/sshd
EXPOSE 22

# Switch to non-root user
USER devuser
WORKDIR /home/devuser

# Clone repository
RUN git clone https://github.com/nova-tis/DiffusionLight.git && echo $CACHE_BUST
WORKDIR /home/devuser/DiffusionLight

# Install Python environment using conda
RUN /bin/bash -c "source $CONDA_DIR/etc/profile.d/conda.sh && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r && \
    conda env create -f environment.yml --yes --verbose && \
    conda run -n diffusionlight pip install -r requirements.txt"

# Set Conda to activate on shell start
RUN echo 'source $CONDA_DIR/etc/profile.d/conda.sh && conda activate diffusionlight' >> ~/.bashrc

# Copy handler script
COPY data_crunch_api.py /home/devuser
COPY podmodel.py /home/devuser

# Download models using huggingface_hub
# RUN conda run -n diffusionlight python -c "from huggingface_hub import snapshot_download; snapshot_download('stabilityai/stable-diffusion-xl-base-1.0', local_dir='/models/stable-diffusion-xl-base-1.0'); snapshot_download('madebyollin/sdxl-vae-fp16-fix', local_dir='/models/sdxl-vae-fp16-fix'); snapshot_download('diffusers/controlnet-depth-sdxl-1.0', local_dir='/models/controlnet-depth-sdxl-1.0')"

# Default command to run the app
CMD ["/bin/bash", "-c", "source $CONDA_DIR/etc/profile.d/conda.sh && conda activate diffusionlight && git pull && python -u podmodel.py &&  uvicorn data_crunch_api:app --host 0.0.0.0 --port 80"]
# CMD ["tail", "-f", "/dev/null"]
