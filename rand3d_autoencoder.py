# -*- coding: utf-8 -*-
"""rand3d_autoencoder.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1KIkVNZScbdoIIMygDo50zDtPB3QMUQtc
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from scipy import stats
from glob import glob
from PIL import Image
from sklearn.decomposition import PCA
from tqdm.auto import tqdm as tqdm
import os, sys, pickle
from plotnine import *
sys.path.append('..')
np.random.seed(3)
import cv2

def make_df(assets):
  dictlist = []
  label_counts = {}
  for asset in assets:
      imgstr = asset.split('/')[4]
      shape = int(imgstr[7:9])
      alpha = float(imgstr[12:15])
      if imgstr[16:18] == 't1':
        theta = -float(imgstr[19:22]) / 2
      elif imgstr[16:18] == 't2':
        theta = float(imgstr[19:22]) / 2
      else:
        theta = 0
      if imgstr[16:18] == 'p1':
        phi = -float(imgstr[19:22]) / 2
      elif imgstr[16:18] == 'p2':
        phi = float(imgstr[19:22]) / 2
      else:
        phi = 0
      row = {'image_name': imgstr, 'image_shape': shape, 'theta': theta, 'phi': phi}
      dictlist.append(row)
  df = pd.DataFrame(dictlist)
  return df

# Commented out IPython magic to ensure Python compatibility.
 # upload both training and test data
# %cd /content
from google.colab import files
uploaded = files.upload()

# Commented out IPython magic to ensure Python compatibility.
# %cd /content
!unzip Train64.zip -d /content/Train64
!unzip Test64.zip -d /content/Test64

!rm -rf /content/__MACOSX/

# visualize training images
images = [cv2.imread(file) for file in glob('/content/Train64/Train64/*.png')]
fig, axes = plt.subplots(2, 3, sharex=True, sharey=True) 
for img, ax in zip(images[:6], axes.flat):
    ax.imshow(img)
    ax.axis('off')

assets = glob('/content/Train64/Train64/*.png')
df = make_df(assets)
shapes = np.unique(df.image_shape)
thetas = np.unique(abs(df.theta))[1:]
phis = np.unique(abs(df.phi))[1:]
nshapes, nthetas, nphis = np.size(shapes), np.size(thetas), np.size(phis)

# Commented out IPython magic to ensure Python compatibility.
# remove stray files before calling dataloader
# %ls /content/Train64 -a
!rm -rf /content/Train64/.ipynb_checkpoints/

### load training data

from torch.utils.data import DataLoader
from torchvision import datasets, transforms

num_epochs = 100
batch_size = 128
learning_rate = 1e-3

img_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Grayscale(num_output_channels=1),
    transforms.Normalize((0.5), (0.5))
])

data_dir = '/content/Train64'
dataset = datasets.ImageFolder(data_dir, transform=img_transform)
dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

### define model
import os
import sys
import torch
import torchvision
from torch import nn
from torch.autograd import Variable
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.utils import save_image

def to_img(x):
    x = 0.5 * (x + 1)
    x = x.clamp(0, 1)
    x = x.view(x.size(0), 1, 64, 64)
    return x

num_epochs = 200
batch_size = 128
learning_rate = 1e-3

img_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Grayscale(num_output_channels=1),
    transforms.Normalize((0.5), (0.5))
])

data_dir = '/content/Test64'
dataset = datasets.ImageFolder(data_dir, transform=img_transform)
dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

class autoencoder(nn.Module):
    def __init__(self):
        super(autoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(64 * 64, 128),
            nn.ReLU(True),
            nn.Linear(128, 64),
            nn.ReLU(True), nn.Linear(64, 12), 
            nn.ReLU(True), nn.Linear(12, 3))
        self.decoder = nn.Sequential(
            nn.Linear(3, 12),
            nn.ReLU(True),
            nn.Linear(12, 64),
            nn.ReLU(True),
            nn.Linear(64, 128),
            nn.ReLU(True), nn.Linear(128, 64 * 64), nn.Tanh())

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x

### train model
model = autoencoder().cuda()
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(
    model.parameters(), lr=learning_rate, weight_decay=1e-5)
losslist = []

for epoch in range(num_epochs):
    for data in dataloader:
        img, _ = data
        img = img.view(img.size(0), -1)
        img = Variable(img).cuda()
        # forward
        output = model(img)
        loss = criterion(output, img)
        losslist.append(loss.item())
        # backward
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    # print
    print('epoch [{}/{}], loss:{:.4f}'
          .format(epoch + 1, num_epochs, loss.item()))
    if epoch % 10 == 0:
      pic = to_img(img.cpu().data)
      save_image(pic, '/content/Test64/true_{}.png'.format(epoch))
      pic = to_img(output.cpu().data)
      save_image(pic, '/content/Test64/recon_{}.png'.format(epoch))

torch.save(model.state_dict(), './sim_autoencoder.pth')

### plot training loss
loss = plt.figure()
plt.plot(losslist, color='k')
plt.xscale('log')
plt.yscale('log')
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
plt.xlabel('Epoch', fontsize=18)
plt.ylabel('Reconstruction Loss', fontsize=18)
plt.tight_layout()
loss.show()

loss.savefig('autoencoderloss.png', dpi=200)

dataloader.dataset[0][0].size()

# visualize test images
images = [cv2.imread(file) for file in glob('/content/Test64/Test64/*.png')]
fig, axes = plt.subplots(2, 3, sharex=True, sharey=True) 
for img, ax in zip(images[:6], axes.flat):
    ax.imshow(img)
    ax.axis('off')

### load test data

batch_size = 1

img_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Grayscale(num_output_channels=1),
    transforms.Normalize((0.5), (0.5))
])

data_dir = '/content/Test64'
dataset = datasets.ImageFolder(data_dir, transform=img_transform)
dataloader = torch.utils.data.DataLoader(dataset, batch_size=1, shuffle=True)

### get latent embeddings
output, latent = [], []
for data in dataloader:
  img, _ = data
  img = img.view(img.size(0), -1)
  img = Variable(img).cuda()
  # forward
  output.append(model(img).detach().cpu().numpy())
  # encoder
  latent.append(model.encoder(img).detach().cpu().numpy())

### get stimulus attributes
assets = glob('/content/Test64/Test64/*.png')
df = make_df(assets)
shapes = np.unique(df.image_shape)
thetas = np.unique(abs(df.theta))[1:]
phis = np.unique(abs(df.phi))[1:]
nshapes, nthetas, nphis = np.size(shapes), np.size(thetas), np.size(phis)

