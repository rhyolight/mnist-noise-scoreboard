import os
import numpy as np
from skimage import io, transform
import torch

from skimage import data

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class RandomNoise(object):
  """
  An image transform that adds noise to random pixels in the image.
  """

  def __init__(self,
               noiselevel=0.0,
               whiteValue=0.1307 + 2*0.3081,
               logDir=None, logProbability=0.01):
    """
    :param noiselevel:
      From 0 to 1. For each pixel, set its value to whiteValue with this
      probability. Suggested whiteVolue is 'mean + 2*stdev'

    :param logDir:
      If set to a directory name, then will save a random sample of the images
      to this directory.

    :param logProbability:
      The percentage of samples to save to the log directory.

    """
    self.noiseLevel = noiselevel
    self.whiteValue = whiteValue
    self.iteration = 0
    self.logDir = logDir
    self.logProbability = logProbability


  def __call__(self, image):
    self.iteration += 1
    a = image.view(-1)
    numNoiseBits = int(a.shape[0] * self.noiseLevel)
    noise = np.random.permutation(a.shape[0])[0:numNoiseBits]
    a[noise] = self.whiteValue

    # Save a subset of the images for debugging
    if self.logDir is not None:
      if np.random.random() <= self.logProbability:
        outfile = os.path.join(self.logDir,
                               "im_noise_" + str(int(self.noiseLevel*100)) + "_"
                               + str(self.iteration).rjust(6,'0') + ".png")
        skimage.io.imsave(outfile,image.view(28,28))

    return image


class Grid(object):
  """
  An image transform that adds stripes in the image.
  """
  def __init__(self,
               size=2,
               whiteValue=0.1307 + 2*0.3081):
    """
    """
    self.size = size
    self.whiteValue = whiteValue


  def __call__(self, image):
    for x in range(image.shape[1]):
      for y in range(image.shape[2]):
        if (x%self.size-1)==0 or (y%self.size-1)==0:
          image.data[0][x][y] = self.whiteValue
    return image


class Wipe(object):
  """
  An image transform that adds stripes in the image.
  """
  def __init__(self,
               percent=.5,
               whiteValue=0.1307 + 2*0.3081):
    """
    """
    self.percent = percent
    self.whiteValue = whiteValue


  def __call__(self, image):
    for x in range(image.shape[1]):
      for y in range(image.shape[2]):
        if (float(x) / float(image.shape[1])) < self.percent:
          image.data[0][x][y] = self.whiteValue
    return image
