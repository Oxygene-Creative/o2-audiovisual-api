import ctranslate2
import torch

if torch.cuda.is_available():
    print("CUDA Version (PyTorch):", torch.version.cuda)
else:
    print("CUDA is not available.")
    
print(ctranslate2.__version__)