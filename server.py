#!/usr/bin/env python3
"""

Usage::
    ./server.py [<port>]
"""
from flask import Flask
from flask_restful import Api, Resource, reqparse

import numpy as np
import torch
from torchvision import datasets, transforms


def createValidationDataSampler(dataset, ratio):
  """
  Create `torch.utils.data.Sampler`s used to split the dataset into 2 ramdom
  sampled subsets. The first should used for training and the second for
  validation.

  :param dataset: A valid torch.utils.data.Dataset (i.e. torchvision.datasets.MNIST)
  :param ratio: The percentage of the dataset to be used for training. The
                remaining (1-ratio)% will be used for validation
  :return: tuple with 2 torch.utils.data.Sampler. (train, validate)
  """
  indices = np.random.permutation(len(dataset))
  training_count = int(len(indices) * ratio)
  train = torch.utils.data.SubsetRandomSampler(indices=indices[:training_count])
  validate = torch.utils.data.SubsetRandomSampler(indices=indices[training_count:])
  return (train, validate)


dataset = datasets.MNIST("mnist",
    train=False,
    download=True,
    transform=transforms.Compose(
        [transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))]
    ),
)


# Web App:
app = Flask(__name__)
api = Api(app)

class Mnist(Resource):
    def get(self, batch, noise):
        print("batch: {} noise: {}".format(batch, noise))
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch, shuffle=True)
        examples = enumerate(dataloader)
        batch_idx, (example_data, example_targets) = next(examples)
        print(example_data.shape)
        print(example_targets)
        response = {
            "data": example_data.data.cpu().numpy().tolist(),
            "targets": example_targets.data.cpu().numpy().tolist(),
        }
        return response, 200

api.add_resource(Mnist, "/_mnist/<int:batch>/<int:noise>")
app.run(debug=True)
