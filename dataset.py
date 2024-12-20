# dataset.py

import os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
import nibabel as nib
import torch.nn.functional as F

class MRIDataset(Dataset):
    def __init__(self, root_dir, labels_files, phase='train', view='coronal', transform=None, target_size=(32, 128, 128)):
        """
        Args:
            root_dir (str): Directory with all the MRI images.
            labels_file (str): Path to the CSV file with labels.
            phase (str): One of 'train', 'val', or 'test'.
            transform (callable, optional): Optional transform to be applied on a sample.
            target_size (tuple): Desired output size (C, D, H, W).
        """
        self.root_dir = os.path.join(root_dir, phase, view)
        self.phase = phase
        self.transform = transform
        self.target_size = target_size

        if phase == 'train':
            self.labels_abnormal = pd.read_csv(labels_files['abnormal'], usecols=['Label'], header=0)
        else:
            self.labels_abnormal = pd.read_csv(labels_files['abnormal'], usecols=[1], header=None)

        self.labels_acl = pd.read_csv(labels_files['acl'], usecols=[1], header=None)
        self.labels_meniscus = pd.read_csv(labels_files['meniscus'], usecols=[1], header=None)

        #self.max_samples = 10

    def __len__(self):
        return len(self.labels_abnormal)

    def __getitem__(self, idx):
       
        image_name = f"CORO_000_{idx:04d}.nii.gz"
        image_path = os.path.join(self.root_dir, image_name)

        if not os.path.exists(image_path):
            print(f"Image {image_path} not found!")
            return torch.zeros(1, 1, 1), torch.zeros(3)  
        # Normalize intensity values
        try:
            
            image = nib.load(image_path).get_fdata()
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return torch.zeros(1, 1, 1), torch.zeros(3) 

        # Resize or crop to target size
        image = torch.tensor(image).unsqueeze(0).float() 
        image = F.interpolate(image.unsqueeze(0), size=self.target_size, mode='trilinear', align_corners=False).squeeze(0)

        label_abnormal = float(self.labels_abnormal.iloc[idx, 0])
        label_acl = float(self.labels_acl.iloc[idx, 0])
        label_meniscus = float(self.labels_meniscus.iloc[idx, 0])

        labels = torch.tensor([label_abnormal, label_acl, label_meniscus], dtype=torch.float32)

        return image, labels
