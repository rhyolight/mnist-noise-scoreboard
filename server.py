#!/usr/bin/env python3
"""

Usage::
    ./server.py [<port>]
"""
from flask import Flask
from flask_restful import Api, Resource, reqparse
from flask import Flask, request, send_from_directory

import numpy as np
import torch
from torchvision import datasets, transforms

dataset = datasets.MNIST("mnist",
    train=False,
    download=True,
    transform=transforms.Compose(
        [transforms.ToTensor()]
    ),
)

# Web App:
app = Flask(__name__)
api = Api(app)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/css/styles.css')
def styles():
    return send_from_directory('static/css', 'styles.css')

class Mnist(Resource):
    def get(self, batch, noise):
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch, shuffle=True)
        batch_idx, (example_data, example_targets) = next(enumerate(dataloader))

        response = {
            "data": example_data.data.cpu().numpy().tolist(),
            "targets": example_targets.data.cpu().numpy().tolist(),
        }
        return response, 200

api.add_resource(Mnist, "/_mnist/<int:batch>/<int:noise>")
app.run(debug=False)
