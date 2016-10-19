# Name:         train.py
# Description:  Trains an artificial neural network (ANN) or multi-layer perceptron (MLP)
#               model using images obtained from self_control_train.py
# Instructions: Make sure training numpy arrays (.npz) files are in current directory. 
# Notes:        For more information, please check out the main github repo
#               https://github.com/kechiao/SmallSelfSteeringSuperCar

################################TO DO ####################################
#GET MORE DATA (Such is the life of a data engineer/machine learner...:-))

import numpy as np 
import glob 
import random

from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout, advanced_activations
from matplotlib import pyplot as plt 
from sklearn import utils

# Containers used to concatenate image and label vectors
trainingImages = np.zeros((1,38400))
trainingLabels = np.zeros((1,4))

# Returns a list of all .npz extension files to import training data
training_data = glob.glob('*.npz')

# Loading data, interating through all .npz files and extracting contents
for training_set in training_data:
  data = np.load(training_set)
  trainingImages = np.vstack((data['train'],trainingImages))
  trainingLabels = np.vstack((data['train_labels'],trainingLabels))

# We want to shuffle the data so the network will not accidentally learn a whole class
# when we input batches of data. That would be bad. 
# Also, we are scaling the inputs from original pixel intensity values [0,255] to [0,1]
trainingImages, trainingLabels = utils.shuffle(trainingImages[1:,:],trainingLabels[1:,:])
trainingImages = trainingImages / 255.0


print 'Starting Training...'

# Using Parametric ReLU to prevent saturation of gradients
# We also use logistic regression activation because we want a probability
# that output belongs in one of 4 classes. Therefore, we also use cross-entropy
# loss instead of euclidian distances because distances in probabilities don't make sense. 

model = Sequential()
prelu = advanced_activations.PReLU(init='zero', weights=None)
model.add(Dense(64, input_dim = 38400, init='lecun_uniform'))
model.add(prelu)
model.add(Dense(64, init='lecun_uniform'))
model.add(prelu)
model.add(Dense(4, init='lecun_uniform'))
model.add(Activation('softmax'))

model.compile(optimizer='sgd', loss='categorical_crossentropy', metrics=['accuracy'])

# Batch size here is a hyperparameter that requires tuning for best performance. 
model.fit(trainingImages, trainingLabels, nb_epoch=50, batch_size=256, validation_split=0.025)

# Print out an example of an image and predicted output
print model.predict_classes(trainingImages[4,:].reshape(1,38400))
testImage = trainingImages[4,:].reshape(120,320)
plt.imshow(testImage, cmap='Greys_r')
plt.show()

# Save the model
model.save('autopilot.h5')

# Some performance statistics:
# Note: These will likely differ depending on shuffling and batch gradients.

# Batch size: 256 , 20 epochs
# 2 layers @ 256 neurons per layer obtains 93.9% validation accuracy.
# 2 layers @ 512 neurons per layer obtains 95.1% validation accuracy50
# Batch size: 512, 20 epochs
# 2 layers @ 32 neurons per layer obtains 90.8% validation accuracy. 
# 2 layers @ 64 neurons per layer obtains 93% validation accuracy.
# 2 layers @ 128 neurons per layer obtains 90.18% validation accuracy.
# Batch size: 256 , 50 epochs
# 2 layers @ 32 neurons per layer obtains 96.32% validation accuracy.

