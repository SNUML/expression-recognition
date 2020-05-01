from torch.utils.data import Dataset
from PIL import Image
import torch
import os


class HandWrittenDataset(Dataset):
    classes = []

    def read_dataset(self):
        img_files = []
        img_label = []
        for filename in os.listdir(self.root):
            if not filename.endswith('png'):
                continue
            img = Image.open(self.root + filename)
            if img is not None:
                img_files.append(self.root + filename)
                img_label.append(filename.split()[1].split('.')[0])
                if img_label[-1] not in self.classes:
                    self.classes.append(img_label[-1])
        return img_files, img_label, len(img_files)

    def __init__(self, root, train=True, transform=None):
        self.root = root
        self.transform = transform
        self.img_files_path, self.img_label_path, self.length = self.read_dataset()
        self.dict = {v: k for k, v in enumerate(self.classes)}

    def __len__(self):
        return self.length

    def getDictLen(self):
        return len(self.dict)

    def __getitem__(self, idx):
        img_path = self.img_files_path[idx]
        img = Image.open(img_path)
        target = int(self.dict[self.img_label_path[idx]])
        if self.transform is not None:
            img = self.transform(img)
        return img, target


if __name__ == "__main__":
    data = HandWrittenDataset('../data/train/')
