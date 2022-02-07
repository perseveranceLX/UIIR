import os
import os.path
import torchvision.transforms.functional as tf
from data.base_dataset import BaseDataset, get_transform
from data.image_folder import make_dataset
from PIL import Image
import random
import torchvision.transforms as transforms
from util import util
import numpy as np

class UnalignedDataset(BaseDataset):
    """
    This dataset class can load unaligned/unpaired datasets.

    It requires two directories to host training images from domain A '/path/to/data/trainA'
    and from domain B '/path/to/data/trainB' respectively.
    You can train the model with the dataset flag '--dataroot /path/to/data'.
    Similarly, you need to prepare two directories:
    '/path/to/data/testA' and '/path/to/data/testB' during test time.
    """

    def __init__(self, opt):
        """Initialize this dataset class.

        Parameters:
            opt (Option class) -- stores all the experiment flags; needs to be a subclass of BaseOptions
        """
        BaseDataset.__init__(self, opt)
        self.image_size = opt.crop_size
        self.isTrain = opt.isTrain
        self.dir_A = os.path.join(opt.dataset_root, opt.phase + 'A')  # create a path '/path/to/data/trainA'
        if opt.unaligned_dataset == 'euvp':
            self.dir_B = os.path.join(opt.dataset_root, opt.phase + 'B')  # create a path '/path/to/data/trainB'
        elif opt.unaligned_dataset == 'adobe5k':
            self.dir_B = os.path.join(opt.dataset_root, 'adobe5k')  # create a path '/path/to/data/trainB'

        self.A_paths = sorted(make_dataset(self.dir_A, opt.max_dataset_size))   # load images from '/path/to/data/trainA'
        self.B_paths = sorted(make_dataset(self.dir_B, opt.max_dataset_size))    # load images from '/path/to/data/trainB'
        self.A_size = len(self.A_paths)  # get the size of dataset A
        self.B_size = len(self.B_paths)  # get the size of dataset B
        transform_list = [
            transforms.ToTensor(),
            transforms.Normalize((0, 0, 0), (1, 1, 1))
        ]
        self.transforms = transforms.Compose(transform_list)

    def __getitem__(self, index):
        """Return a data point and its metadata information.

        Parameters:
            index (int)      -- a random integer for data indexing

        Returns a dictionary that contains A, B, A_paths and B_paths
            A (tensor)       -- an image in the input domain
            B (tensor)       -- its corresponding image in the target domain
            A_paths (str)    -- image paths
            B_paths (str)    -- image paths
        """
        A_path = self.A_paths[index % self.A_size]  # make sure index is within then range
        if self.opt.serial_batches:   # make sure index is within then range
            index_B = index % self.B_size
        else:   # randomize the index for domain B to avoid fixed pairs.
            index_B = random.randint(0, self.B_size - 1)
        B_path = self.B_paths[index_B]
        comp = Image.open(A_path).convert('RGB')
        real = Image.open(B_path).convert('RGB')
        # apply image transformation
        if np.random.rand() > 0.5 and self.isTrain:
            comp, real = tf.hflip(comp), tf.hflip(real)
       
        comp = tf.resize(comp, [self.image_size, self.image_size])
        real = tf.resize(real, [self.image_size,self.image_size])
        comp = self.transforms(comp)
        real = self.transforms(real)
        return {'fake': comp, 'real': real,'img_path':A_path}

    def __len__(self):
        """Return the total number of images in the dataset.

        As we have two datasets with potentially different number of images,
        we take a maximum of
        """
        return max(self.A_size, self.B_size)
