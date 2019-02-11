import os
import numpy as np
from skimage import io, transform
import PIL

import torch
from torchvision.transforms import ToPILImage, ToTensor

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class RandomNoise(object):
  """
  An image transform that adds noise to random pixels in the image.
  """

  def __init__(self,
               noiselevel=0.0,
               whiteValue=0.1307 + 2*0.3081):
    """
    :param noiselevel:
      From 0 to 1. For each pixel, set its value to whiteValue with this
      probability. Suggested whiteVolue is 'mean + 2*stdev'

    """
    self.noiseLevel = noiselevel
    self.whiteValue = whiteValue


  def __call__(self, image):
    a = image.view(-1)
    numNoiseBits = int(a.shape[0] * self.noiseLevel)
    noise = np.random.permutation(a.shape[0])[0:numNoiseBits]
    a[noise] = self.whiteValue
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
  def __init__(self,
               percent=.5,
               whiteValue=0.1307 + 2*0.3081):
    self.percent = percent
    self.whiteValue = whiteValue


  def __call__(self, image):
    for x in range(image.shape[1]):
      for y in range(image.shape[2]):
        if (float(y) / float(image.shape[2])) < self.percent:
          image.data[0][x][y] = self.whiteValue
    return image


class Invert(object):
  def __init__(self, offset=1.0):
    self.offset = offset

  def __call__(self, image):
    for x in range(image.shape[1]):
      for y in range(image.shape[2]):
        image.data[0][x][y] = self.offset - image.data[0][x][y]
    return image


class Washout(object):
  def __init__(self, level=0.5):
    self.level = level

  def __call__(self, image):
    if self.level == 0: return image
    for x in range(image.shape[1]):
      for y in range(image.shape[2]):
        image.data[0][x][y] = image.data[0][x][y] - self.level
    return image


class Swirl(object):
  def __init__(self, level=0.5):
    self.level = level

  def __call__(self, image):
    if self.level == 0: return image
    pil = ToPILImage()(image)
    swirled = transform.swirl(
        np.array(pil),
        center=(14,14),
        strength=10.0 * self.level,
        radius=28,
        rotation=0.0,
    )
    return ToTensor()(PIL.Image.fromarray(swirled))
