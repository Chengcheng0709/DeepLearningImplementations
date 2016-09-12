

from __future__ import print_function
from keras.datasets import cifar10
from keras.optimizers import SGD
from keras.utils import np_utils, generic_utils
import time
import os
import numpy as np
import densenet
import json

batch_size = 64
nb_classes = 10
nb_epoch = 300

# input image dimensions
img_rows, img_cols = 32, 32
# the CIFAR10 images are RGB
img_channels = 3

# the data, shuffled and split between train and test sets
(X_train, y_train), (X_test, y_test) = cifar10.load_data()

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)

img_dim = (img_channels, img_rows, img_cols)
depth = 40
nb_dense_block = 3
growth_rate = 12
nb_filter = 16
dropout_rate = 0.2
learning_rate = 0.1
decay = 1E-4

model = densenet.DenseNet(nb_classes,
                          img_dim,
                          depth,
                          nb_dense_block,
                          growth_rate,
                          nb_filter,
                          dropout_rate=dropout_rate)

# Model output
model.summary()

# Build optimizer
opt = SGD(lr=learning_rate, decay=0, momentum=0.9, nesterov=True)

model.compile(loss='categorical_crossentropy', optimizer=opt, metrics=["accuracy"])

try:
    from keras.utils.visualize_util import plot
    plot(model, to_file='model.png', show_shapes=True)
except ImportError:
    pass

X_train = X_train.astype('float32')
X_test = X_test.astype('float32')

# Normalisation
X = np.vstack((X_train, X_test))
for i in range(img_channels):
    mean = np.mean(X[:, i, :, :])
    std = np.std(X[:, i, :, :])
    X_train[:, i, :, :] = (X_train[:, i, :, :] - mean) / std
    X_test[:, i, :, :] = (X_test[:, i, :, :] - mean) / std


print("Training")

list_train_loss = []
list_test_loss = []
list_learning_rate = []

for e in range(nb_epoch):

    model.optimizer.lr.set_value(np.float32(model.optimizer.lr.get_value() / np.float32(1. + decay * e)))

    if e == int(0.5 * nb_epoch):
        model.optimizer.lr.set_value(np.float32(model.optimizer.lr.get_value() / np.float32(10.)))

    if e == int(0.75 * nb_epoch):
        model.optimizer.lr.set_value(np.float32(model.optimizer.lr.get_value() / np.float32(100.)))

    split_size = batch_size
    num_splits = X_train.shape[0] / split_size
    arr_splits = np.array_split(np.arange(X_train.shape[0]), num_splits)

    progbar = generic_utils.Progbar(len(arr_splits))
    l_train_loss = []
    start = time.time()

    for batch_idx in arr_splits:

        X_batch, Y_batch = X_train[batch_idx], Y_train[batch_idx]
        train_logloss, train_acc = model.train_on_batch(X_batch, Y_batch)

        l_train_loss.append([train_logloss, train_acc])

    test_loss = model.evaluate(X_test, Y_test, verbose=0, batch_size=256)
    list_train_loss.append(np.mean(np.array(l_train_loss), 0).tolist())
    list_test_loss.append(test_loss)
    list_learning_rate.append(model.optimizer.lr.get_value())
    print("")
    print('Epoch %s/%s, Time: %s' % (e + 1, nb_epoch, time.time() - start))

    d_log = {}
    d_log["batch_size"] = batch_size
    d_log["nb_epoch"] = nb_epoch
    d_log["optimizer"] = opt.get_config()
    d_log["train_loss"] = list_train_loss
    d_log["test_loss"] = list_test_loss
    d_log["learning_rate"] = list_learning_rate

    json_file = os.path.join('./log/experiment_log_cifar10.json')
    with open(json_file, 'w') as fp:
        json.dump(d_log, fp, indent=4, sort_keys=True)