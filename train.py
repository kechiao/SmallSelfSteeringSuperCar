# Name:       train.py 
#

#############################TO DO ##############################
#PREPROCESS IMAGES BY MEAN CENTER, STANDARDIZE BY STDS
#GET MORE DATA (Such is the life of a  data engineer/machine learner...:-))

import numpy as np 
import glob 
import random

from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout, advanced_activations
from matplotlib import pyplot as plt 
from sklearn import utils

#temporary placeholders
trainingImages = np.zeros((1,38400))
trainingLabels = np.zeros((1,4))

training_data = glob.glob('*.npz')

#loading data using glob
for training_set in training_data:
  data = np.load(training_set)
  trainingImages = np.vstack((data['train'],trainingImages))
  #trainingLabels = np.vstack((data['train_labels'],trainingLabels))
  trainingLabels = np.vstack((data['train_labels'],trainingLabels))

#shuffling,rescaling 
trainingImages, trainingLabels = utils.shuffle(trainingImages[1:,:],trainingLabels[1:,:])
trainingImages = trainingImages / 255.0

#want to use logistic regression to restrict output to [0,1]
#want to use prelu instead of relu for saturation of gradients
#use cross-entropy loss instead of euclidian distance (use softmax)
#b/c for probabilities, distances dont' make sense vs. maximum likelihood
print 'Starting Training...'

model = Sequential()
prelu = advanced_activations.PReLU(init='zero', weights=None)
model.add(Dense(128, input_dim = 38400, init='lecun_uniform'))
model.add(prelu)
#model.add(Activation('relu'))
#model.add(Dense(32, init='lecun_uniform'))
#model.add(Activation('relu'))
model.add(Dense(4, init='lecun_uniform'))
model.add(Activation('softmax'))

model.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])

model.fit(trainingImages, trainingLabels, nb_epoch=10, batch_size=100, validation_split=0.025)
print model.predict_classes(trainingImages[4,:].reshape(1,38400))
testImage = trainingImages[4,:].reshape(120,320)
plt.imshow(testImage, cmap='Greys_r')
plt.show()
model.save('autopilot.h5')


