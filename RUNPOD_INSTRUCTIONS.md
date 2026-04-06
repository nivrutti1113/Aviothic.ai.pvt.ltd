# 🚀 Aviothic.ai - RunPod H100 Training Guide

Welcome to your **High-Performance Training Environment**. This guide will help you train your Breast Cancer AI model on your **H100 SXM** pod with maximum efficiency.

---

## 🛠️ Phase 1: Environment Setup

Once you are logged into your RunPod Terminal, run these commands sequentially.

### 1. Clone the Repository
```bash
git clone https://github.com/nivrutti1113/Aviothic.ai.pvt.ltd.git
cd Aviothic.ai.pvt.ltd
```

### 2. Install High-Performace Dependencies
We use `timm` for the model ensemble and `tqdm` for tracking.
```bash
pip install -r requirements.txt
pip install timm tqdm flash-attn --no-build-isolation
```

---

## ⚡ Phase 2: Start the Training Engine

### 🏃 Use the Master Training Script
**DO NOT RUN THE NOTEBOOKS.** We have consolidated the logic from your research notebooks into a professional Python script (`train_runpod_full.py`). 

**Why?** 
- It uses **TF32** and **Torch Compile** (H100 exclusive speed boosts).
- It handles training in the background (no browser required).

```bash
# Basic Run
python train_runpod_full.py --data_dir /workspace/data --batch_size 64

# Recommended: Run in "Set-and-Forget" mode (keeps training if you disconnect)
screen -S aviothic_train
python train_runpod_full.py --data_dir /workspace/data --batch_size 64 --workers 16
# Press Ctrl+A, then D to detach. 
# Re-attach later with: screen -r aviothic_train
```

---

## 📂 Understanding Your Files

| File / Folder | Purpose | Action |
| :--- | :--- | :--- |
| **`train_runpod_full.py`** | **Master Training Script** | **USE THIS** |
| `training/` | Research notebooks & iterations | Ignore during training |
| `backend/` / `frontend/` | The full application code | Ignore during training |
| `models/` | Where your trained weights are saved | **DOWNLOAD FROM HERE** |

---

## 🏎️ H100 SXM Optimization Check
The script is pre-patched for your H100 hardware. It includes:
- ✅ **TF32 (TensorFloat-32)** enabled for Hopper matmuls.
- ✅ **Torch Compile** for graph-level optimization.
- ✅ **Flash Attention 2** support for your Vision Transformer (ViT).
- ✅ **80GB VRAM** scaling (Batch size 64+).

---

## 📤 After Training (Saving Your Model)
Once training finishes, your best model will be saved automatically to:
`./models/aviothic_final_AIMS.pt`

**To download it to your local machine:**
Use RunPod's built-in File Manager or run this from your local PC:
```bash
# Replace <pod-id> with your RunPod ID
scp -P <port> root@<dns-address>:/workspace/Aviothic.ai.pvt.ltd/models/aviothic_final_AIMS.pt ./
```

---

*Need help during the training? Just ask!*
