FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV CONDA_DIR=/opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    openssh-server \
    sudo \
    bzip2 \
    && rm -rf /var/lib/apt/lists/*

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && \
    bash miniconda.sh -b -p $CONDA_DIR && \
    rm miniconda.sh && \
    $CONDA_DIR/bin/conda clean -afy

# Create a non-root user
RUN useradd -ms /bin/bash devuser && echo "devuser:devpassword" | chpasswd && adduser devuser sudo

# SSH setup
RUN mkdir /var/run/sshd
EXPOSE 22

# Switch to user home and clone repo
USER devuser
WORKDIR /home/devuser
RUN git clone https://github.com/nova-tis/DiffusionLight.git
WORKDIR /home/devuser/DiffusionLight
# Create the Conda environment
RUN /bin/bash -c "source $CONDA_DIR/etc/profile.d/conda.sh && \
    conda env create -f environment.yml && \
    conda activate diffusionlight && \
    pip install -r requirements.txt"
RUN pip install --no-cache-dir runpod
# Activate the conda environment and set up default shell
RUN echo "source /opt/conda/etc/profile.d/conda.sh && conda activate diffusionlight" >> ~/.bashrc

COPY rp_handler.py /home/devuser

# # Switch back to root for SSH service
# # USER root
# # Start SSH daemon
# # CMD ["/usr/sbin/sshd", "-D"]
# USER devuser
CMD ["python3", "-u", "rp_handler.py"]

# docker buildx build --platform linux/amd64 -t diffusionlight-gpu .
#