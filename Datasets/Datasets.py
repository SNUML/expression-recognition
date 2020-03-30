from torch.utils.data import Dataset
from PIL import Image
import torch
import os

class HandWrittenDataset(Dataset):
    def read_dataset(self):
        img_files = []
        img_label = []
        for filename in os.listdir(self.root):
            if not filename.endswith('png'):
                continue
            print(filename)
            img = Image.open(self.root + filename)
            if img is not None:
                img_files.append(self.root + filename)
                img_label.append(filename.split()[1].split('.')[0])
        return img_files, img_label, len(img_files)


    def __init__(self, root, train=True, transform=None):
        self.root = root
        self.train = train
        self.transform = transform
        self.img_files_path, self.img_label_path, self.length = self.read_dataset()


    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        img_path = self.img_files_path[idx]
        img = Image.open(img_path)
        if self.transform is not None:
            img = self.transform(img)
        img.show()
        print(self.img_label_path[idx])
        return {'image':img, 'label':self.img_label_path[idx]}

if __name__ == '__main__':
    dataset = HandWrittenDataset(root='../data/train/', train=True)
    dataset.read_dataset()
    dataset.__getitem__(2)
