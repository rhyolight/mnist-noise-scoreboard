#!/usr/bin/env python3
"""

Usage::
    ./server.py [<port>]
"""
# from __future__ import (absolute_import, division,
#                         print_function, unicode_literals)

from flask_restful import Api, Resource, reqparse
from flask import Flask, send_from_directory

import torch.nn.functional as F
from torchvision import datasets, transforms
from image_transforms import *

from pytorch.speech_commands_dataset import (
    SpeechCommandsDataset, BackgroundNoiseDataset
)
from pytorch.audio_transforms import (ToMelSpectrogramFromSTFT,
                                      ToSTFT,
                                      DeleteSTFT,
                                      LoadAudio,
                                      FixAudioLength,
                                      )
from pytorch.audio_transforms import ToTensor as ToAudioTensor

# ML models
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
models = {}
models['mnist'] = {}
print('Loading MNIST models...')
models['mnist']['denseCNN1'] = torch.load('models/mnist/denseCNN1.pt', map_location=device)
models['mnist']['sparseCNN1'] = torch.load('models/mnist/sparseCNN1.pt', map_location=device)
print('Loading Speech models...')
models['speech'] = {}
models['speech']['denseCNN1'] = torch.load('models/speech/denseCNN2_c1_out_channels64_64k1000n1000.pt',
                                           map_location=device)
models['speech']['sparseCNN1'] = torch.load('models/speech/sparseCNN2_n1000.pt', map_location=device)


def getClassificationResults(data, type, target):
    result = {}
    with torch.no_grad():
        for name in models[type]:
            model = models[type][name]
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


@app.route('/mnist.html')
def mnist_static():
    return send_from_directory('static', 'mnist.html')


@app.route('/speech.html')
def speech_static():
    return send_from_directory('static', 'speech.html')


@app.route('/css/styles.css')
def styles():
    return send_from_directory('static/css', 'styles.css')


@app.route('/data/speech/speech_commands/test/<classification>/<filename>')
def wav_static(classification, filename):
    return send_from_directory(os.path.join('data/speech/speech_commands/test/', classification), filename)


class Mnist(Resource):
    NAME = "mnist"

    def get(self, batch, xform, xformStrength):
        if xform == "noise":
            imageTransform = RandomNoise(xformStrength / 100.)
        elif xform == "grid":
            imageTransform = Grid(size=xformStrength)
        elif xform == "wipe":
            imageTransform = Wipe(percent=xformStrength / 100.)
        elif xform == "invert":
            imageTransform = Invert()
        elif xform == "swirl":
            imageTransform = Swirl(level=xformStrength / 100.)
        elif xform == "washout":
            imageTransform = Washout(level=xformStrength / 100.)
        elif xform == "rotate":
            imageTransform = Rotate(degrees=xformStrength)
        else:
            imageTransform = transforms.ToTensor

        # Only doing one xform at a time, but could apply many.

        dataset = datasets.MNIST('data/' + self.NAME,
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
            "classifications": getClassificationResults(example_data, self.NAME, example_targets),
        }
        return response, 200


api.add_resource(Mnist, "/_mnist/<int:batch>/<string:xform>/<int:xformStrength>")


class Speech(Resource):
    NAME = "speech"

    def post(self):
        args = parser.parse_args()

    def get(self, batch, xform, xformStrength):
        dataDir = os.path.join("data", self.NAME, "speech_commands", "test")

        # Create transforms
        # if xform == "noise":
        #     imageTransform = RandomNoise(xformStrength / 100.)
        # elif xform == "grid":
        #     imageTransform = Grid(size=xformStrength)
        # elif xform == "wipe":
        #     imageTransform = Wipe(percent=xformStrength / 100.)
        # elif xform == "invert":
        #     imageTransform = Invert()
        # elif xform == "swirl":
        #     imageTransform = Swirl(level=xformStrength / 100.)
        # elif xform == "washout":
        #     imageTransform = Washout(level=xformStrength / 100.)
        # elif xform == "rotate":
        #     imageTransform = Rotate(degrees=xformStrength)
        # else:
        #     imageTransform = transforms.ToTensor

        # dataAugmentationTransform = transforms.Compose([
        #     ChangeAmplitude(),
        #     ChangeSpeedAndPitchAudio(),
        #     FixAudioLength(),
        #     ToSTFT(),
        #     StretchAudioOnSTFT(),
        #     TimeshiftAudioOnSTFT(),
        #     FixSTFTDimension(),
        # ])

        n_mels = 32
        melTransform = transforms.Compose(
            [
                ToSTFT(),
                ToMelSpectrogramFromSTFT(n_mels=n_mels),
                DeleteSTFT(),
                # ToAudioTensor('mel_spectrogram', 'input'),
            ])

        dataset = SpeechCommandsDataset(
            dataDir,
            transforms.Compose([
                LoadAudio(),
                FixAudioLength(),
                melTransform
            ]))

        dataloader = torch.utils.data.DataLoader(dataset,
                                                 batch_size=batch,
                                                 sampler=None,
                                                 shuffle=True,
                                                 )

        # self.test_loader = DataLoader(testDataset,
        #                               batch_size=params["batch_size"],
        #                               sampler=None,
        #                               shuffle=False,
        #                               pin_memory=self.use_cuda,
        #                               )

        # Create dataset and loader
        # dataset = datasets.MNIST(self.NAME,
        #     train=False,
        #     download=True,
        #     transform=transforms.Compose(
        #         [
        #             transforms.ToTensor(),
        #             imageTransform,
        #             transforms.Normalize((0.1307,), (0.3081,))
        #         ]
        #     ),
        # )
        # dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch, shuffle=True)

        # Run One Batch
        # batch_idx, (example_data, example_targets) = next(enumerate(dataloader))

        batch_idx, result = next(enumerate(dataloader))

        # Construct and emit response
        response = {
            "data": result['mel_spectrogram'].data.cpu().numpy().tolist(),
            "targets": result['target'].data.cpu().numpy().tolist(),
            "paths": result['path'],
            # "classifications": getClassificationResults(example_data, self.NAME, example_targets),
        }
        return response, 200


api.add_resource(Speech, "/_speech/<int:batch>/<string:xform>/<int:xformStrength>")

app.run(debug=True)
