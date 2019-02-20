#!/usr/bin/env python2
"""

Usage::
    ./server.py [<port>]
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from flask_restful import Api, Resource, reqparse
from flask import Flask, send_from_directory, send_file

import torch.nn.functional as F
from torchvision import datasets, transforms
from image_transforms import *

from pytorch.speech_commands_dataset import (
    SpeechCommandsDataset, BackgroundNoiseDataset
)
from pytorch.audio_transforms import (ToMelSpectrogramFromSTFT,
                                      ToSTFT,
                                      ChangeAmplitude,
                                      ChangeSpeedAndPitchAudio,
                                      DeleteSTFT,
                                      LoadAudio,
                                      FixAudioLength,
                                      StretchAudioOnSTFT,
                                      TimeshiftAudioOnSTFT,
                                      FixSTFTDimension,
                                      AddNoise,
                                      ToWavFile,
                                      )
from pytorch.audio_transforms import ToTensor as ToAudioTensor

SPEECH_DATA = os.path.join("data", "speech", "speech_commands", "valid")
SPEECH_TMP = os.path.join("data", "speech", "tmp")

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


def getMnistClassificationResults(data, target):
    result = {}
    with torch.no_grad():
        for name in models['mnist']:
            model = models['mnist'][name]
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss = F.nll_loss(output, target, reduction='sum').item()
            pred = output.max(1, keepdim=True)[1]
            correct = pred.eq(target.view_as(pred)).sum().item()
            result[name] = {}
            result[name]["accuracy"] = float(correct) / len(data)
            result[name]["classifications"] = pred.cpu().numpy().tolist()
    return result


def getSpeechClassificationResults(data, target):
    result = {}
    with torch.no_grad():
        for name in models['speech']:
            model = models['speech'][name]
            model.eval()
            test_loss = 0
            correct = 0
            data = torch.unsqueeze(data, 1)
            data, target = data.to(device), target.to(device)
            print(data.dtype)
            output = model(data)
            test_loss += F.nll_loss(output, target, reduction='sum').item()
            pred = output.max(1, keepdim=True)[1]
            correct += pred.eq(target.view_as(pred)).sum().item()

            result[name] = {}
            result[name]["accuracy"] = float(correct) / len(data)
            result[name]["classifications"] = pred.cpu().numpy().tolist()
    return result


def createAudioXform(xform, xformStrength):

    myXforms = [
        FixAudioLength(),
    ]
    if xform == "noise":
        myXforms.append(AddNoise(alpha=xformStrength / 100.))

    # ChangeAmplitude(),
    # ChangeSpeedAndPitchAudio(),
    # StretchAudioOnSTFT(),
    # TimeshiftAudioOnSTFT(),
    # FixSTFTDimension(),

    myXforms.append(ToSTFT())
    return transforms.Compose(myXforms)


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


@app.route('/_wavs/original/<word>/<filename>')
def wav_static(word, filename):
    path = os.path.join('data/speech/speech_commands/valid/', word)
    return send_from_directory(
        path, filename
    )


@app.route('/_wavs/augmented/<word>/<filename>')
def wav_static_augmented(word, filename):
    path = SPEECH_TMP
    file = "{}_{}".format(word, filename)
    print("Loading WAV from {}/{}".format(path, file))
    return send_from_directory(path, file)


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
            "classifications": getMnistClassificationResults(example_data, example_targets),
        }
        return response, 200


api.add_resource(Mnist, "/_mnist/<int:batch>/<string:xform>/<int:xformStrength>")


class Speech(Resource):
    NAME = "speech"

    def post(self):
        args = parser.parse_args()

    def get(self, batch, xform, xformStrength):
        tempPath = SPEECH_TMP
        dataAugmentationTransform = createAudioXform(xform, xformStrength)

        n_mels = 32
        melTransform = transforms.Compose(
            [
                ToMelSpectrogramFromSTFT(n_mels=n_mels),
                DeleteSTFT(),
                ToAudioTensor('mel_spectrogram', 'input'),
            ])

        dataset = SpeechCommandsDataset(
            SPEECH_DATA,
            transforms.Compose([
                LoadAudio(),
                dataAugmentationTransform,
                ToWavFile(tempPath),
                melTransform,
            ]))

        dataloader = torch.utils.data.DataLoader(dataset,
                                                 batch_size=batch,
                                                 sampler=None,
                                                 shuffle=True,
                                                 )

        # Run One Batch
        batch_idx, result = next(enumerate(dataloader))
        data = result['mel_spectrogram']
        targets = result['target']

        # Construct and emit response
        response = {
            "data": data.data.cpu().numpy().tolist(),
            "targets": targets.data.cpu().numpy().tolist(),
            "paths": result['path'],
            # FIXME: this doesn't work yet
            # "classifications": getSpeechClassificationResults(data, targets),
        }
        return response, 200


api.add_resource(Speech, "/_speech/<int:batch>/<string:xform>/<int:xformStrength>")

app.run(debug=True)
