#!/usr/bin/env python3
"""

Usage::
    ./server.py [<port>]
"""
# from __future__ import (absolute_import, division,
#                         print_function, unicode_literals)

from flask import Flask
from flask_restful import Api, Resource, reqparse
from flask import Flask, request, send_from_directory

import numpy as np
import torch
import torch.nn.functional as F
from torchvision import datasets, transforms

from image_transforms import RandomNoise, Grid, Wipe, Invert, Washout

# ML models
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
models = {}
models['denseCNN1'] = torch.load('models/denseCNN1.pt', map_location=device)
models['sparseCNN1'] = torch.load('models/sparseCNN1.pt', map_location=device)

def getClassificationResults(data, target):
    result = {}
    with torch.no_grad():
        for name in models:
            model = models[name]
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss = F.nll_loss(output, target, reduction='sum').item()
            pred = output.max(1, keepdim=True)[1]
            correct = pred.eq(target.view_as(pred)).sum().item()
            result[name] = {}
            result[name]["accuracy"] = float(correct) / len(data)
            result[name]["classifications"] = pred.cpu().numpy().tolist()
    return result

# Web App:
app = Flask(__name__)
api = Api(app)
parser = reqparse.RequestParser()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/css/styles.css')
def styles():
    return send_from_directory('static/css', 'styles.css')

class Mnist(Resource):

    def post(self):
        args = parser.parse_args()

    def get(self, batch, xform, xformStrength):
        if xform == "noise":
            imageTransform = RandomNoise(xformStrength / 100.)
        elif xform == "grid":
            imageTransform = Grid(size=xformStrength)
        elif xform == "wipe":
            imageTransform = Wipe(percent=xformStrength / 100.)
        elif xform == "invert":
            imageTransform = Invert()
        elif xform == "washout":
            imageTransform = Washout(level=xformStrength / 100.)
        else:
            imageTransform = transforms.ToTensor

        dataset = datasets.MNIST("mnist",
            train=False,
            download=True,
            transform=transforms.Compose(
                [
                    transforms.ToTensor(),
                    imageTransform,
                    transforms.Normalize((0.1307,), (0.3081,))
                ]
            ),
        )
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch, shuffle=True)
        batch_idx, (example_data, example_targets) = next(enumerate(dataloader))

        response = {
            "data": example_data.data.cpu().numpy().tolist(),
            "targets": example_targets.data.cpu().numpy().tolist(),
            "classifications": getClassificationResults(example_data, example_targets),
        }
        return response, 200

api.add_resource(Mnist, "/_mnist/<int:batch>/<string:xform>/<int:xformStrength>")
app.run(debug=True)
