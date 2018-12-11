import time
import os
import numpy as np
from PIL import Image
from tqdm import tqdm
import ntpath
import torch
import torch.nn as nn
import argparse
import cv2

from data.data_loader import CreateDataLoader
from data.double_dataset import DoubleDatasetLoaderPath
from models.models import create_model
from util.util import save_image


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scoring script for finding deblur score.")
    parser.add_argument("--in-gt", type=str, default="folder_gt",
                        help="Path to folder containing sharp ground truth images.")
    parser.add_argument("--in-fake", type=str, default="folder_fake",
                        help="Path to folder containing deblurred images.")
    parser.add_argument("--size-reference", type=str,
                        default="folder_size_reference")
    parser.add_argument("--dataset-mode", type=str, default="double",
                        help="Type of dataset used.")

    # Load configuration
    args = parser.parse_args()

    # GT data loading
    data_loader = DoubleDatasetLoaderPath()
    data_loader.initialize(args)
    dataset = data_loader.load_data()

    # things that accumulate
    iters = 0
    dataset_loss = 0

    with torch.no_grad():
        for i, data in enumerate(tqdm(dataset)):
            gt_path = data['gt_path']
            fake_path = data['fake_path']
            size_path = data['size_path']

            # load the images
            gt_img = cv2.imread(gt_path[0], 0)
            fake_img = cv2.imread(fake_path[0], 0)
            size_img = cv2.imread(size_path[0], 0)

            # resize the images
            gt_img = cv2.resize(gt_img, size_img.shape)
            fake_img = cv2.resize(fake_img, size_img.shape)

            # get the fft, maybe shift?
            gt_fft = np.fft.fft2(gt_img)
            gt_shift_fft = np.fft.fftshift(gt_fft)
            gt_mag_spec = 20 * np.log(np.abs(gt_shift_fft))

            fake_fft = np.fft.fft2(fake_img)
            fake_shift_fft = np.fft.fftshift(fake_fft)
            fake_mag_spec = 20 * np.log(np.abs(fake_shift_fft))

            # keep count of the norm
            # dataset_loss += np.linalg.norm(gt_fft - fake_fft)
            dataset_loss += np.linalg.norm(gt_mag_spec - fake_mag_spec)
            iters += 1

    # find the dataset loss
    print("<TEST> Dataset: {}, Average Dataset Loss: {}".format(
        args.in_fake, dataset_loss / iters))
