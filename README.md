SmallSelfSteeringSuperCar
=========================

This was small project aimed at applying machine learning to a fun practical real life demo. The system uses a toy RC supercar (Lamborghini Veneno :-)) with basic inputs (forward, reverse, left, right), a Raspberry Pi 3 Model B, a Raspberry Pi Camera, and a computer (MacBook Pro) to process images and to train the auto-driving model. 

Here's a video:

[![SmallSelfSteeringSuperCar](http://i3.ytimg.com/vi/c7R_Kfbgi4E/hqdefault.jpg)](https://www.youtube.com/watch?v=c7R_Kfbgi4E)

And a picture of the sleek Veneno modified with a stylish cardboard roof rack and state of the art processing unit :-)

[![Veneno](http://i.imgur.com/EDU4Le5l.jpg)](http://i.imgur.com/EDU4Le5l.jpg)

If you would like to view the details behind this project, feel free to click on the "Details" section in the table of contents. There you will find a concise breakdown of how the car manages to drive itself and how amazing it actually is.

## Table of Contents

- [Installation](#installation)
    - [Dependencies](#dependencies)
- [Setting up Pi-rc](#pi-rc)
- [Setting up local computer](#local-computer)
    - [Capturing Data](#capturing-data)
    - [Training](#training)
    - [Testing](#testing)
- [Details](#details)
    - [Motivation](#motivation)
    - [Overview](#overview)
    - [In Depth](#in-depth)
    - [Results](#results)
    - [Problems](#problems)
- [Future Updates](#future-updates)
- [Special Thanks](#special-thanks)

## Installation

### Dependencies

The following dependencies are required in order to for this project to function:
* Raspberry Pi
  - Pi Camera
  - pi-rc
* Computer
  - Numpy
  - [PyGame](http://www.pygame.org/download.shtml)
  - [Keras](https://keras.io/)
  - pi-rc

### Pi-rc

Pi-rc is used in this project as the way to control the RC car without the use of the supplied remote control. It allows me to be able to drive the car on my computer, both for fun and to store keyboard directions, which I will get to later. 

You can install pi-rc [here](https://github.com/bskari/pi-rc). From the pi-rc repo follow the instructions to set it up as the configuration JSON file varies depending on what model RC car you have (mostly operating frequencies.)

Pi-rc will be required on **both** the Raspberry Pi and local computer, as the Raspberry Pi will be running as the server in which the local computer will send commands to move the car. 

### Local computer

The local computer is responsible for issuing RC commands to the Raspberry Pi, collecting the training image data from a TCP stream, storing it, training the model using Keras with the images, and testing the actual auto-driving model. 

Make sure you have [Keras](https://keras.io/) installed as this is the main framework for building our machine learning model. Once you have verified that the RC car is working (you can control it through your local computer following the guide on the pi-rc repository), continue onto the training section.

### Capturing Data

Before beginning to capture training images, ensure that the pi-rc server is running on the Raspberry Pi. ```cd``` into wherever you've placed the pi-rc folder and run pi_pcm by typing: 

```
sudo ./pi_pcm
```

Once the server is running, on your local computer run:

```
python self_control_train.py
```
Finally, on the Raspberry Pi run:

```
python stream_image_client.py
```

This will open up a PyGame window where you can view what the car is seeing (must use VNC) while controlling the car. All keyboard arrow keystrokes will be saved along with the current image frame to the ```training_data``` folder under an ```.npz``` file extension. 

Currently the filename will **not** update, so you have to manually update the filename if you wish to capture multiple runs. 

### Training

Once you have image and direction capture, the network must be trained. The neural network is trained using:

```
python train.py
```

All filenames under the ```.npz``` extension will be loaded, and from there will be segregated into a numpy array representation of the image along with the corresponding direction. The model will begin training using neural network parameters and hyperparamters listed inside ```train.py```. 

The trained model is stored to the ```models``` directory as ```model.h5```, but you can change this to your liking. 

### Testing

Now that the trained model is complete, you can test your auto-driving car by:

```
python auto-driver.py
```

Again make sure ```pi-pcm``` is running on the Raspberry Pi and you run ```stream_image_client.py``` after running ```auto-driver.py```.

For more details and an in-depth explanation, continue reading! 

### Details

### Motivation

I wanted to do this project because I wanted to be able to apply some of the machine learning methods I've learned in school and online directly to a real world scaled down application. While the idea of a neural network being able to *learn* feature hierachies itself and apply this to new inputs is amazing, *seeing* it work blew my mind away. 

Therefore, I decided to try to apply a neural network to modify an RC car to drive itself, because this not only allows me to familiarize myself with applied software and hardware integration, machine learning, and patience, but also because I love the feeling of seeing a tangible creation come to fruition. Also because self driving cars are *cool as heck*. 

### Overview

So how does it all work? Is it magic? No! It's machine learning! (Ok sometimes it may be magical, especially when training it, but that's not the point :-))
This is the system:

[![RC Car System](http://i.imgur.com/YZ6vtTz.jpg)](http://i.imgur.com/YZ6vtTz.jpg)

The entire system used in the car consists of three major parts: the Raspberry Pi processing unit, the local computer processing unit, and the RC car unit. These units work together to create an "intelligent agent" which observes the world through the camera and acts upon an environment (a paper track) using actuators (servors to steer, motor to drive) to direct itself towards achieving a goal (correctly navigating a paper track without driving off the lines or careening itself into a wall)

The Raspberry Pi processing unit contains the Raspberry Pi computer and the Pi Camera. These two work together to obtain real-time images in front of the car and streams these images over a to a local server on the local computer. This unit also is responsible for starting the server used to accept RC commands and drive the car, as the Raspberry Pi essentially acts as the radio controller for the car. 

The local computer processing unit contains the MacBook Pro and it handles multiple tasks: receiving the streamed images from the Raspbbery  Pi, trains the neural network, and runs the auto-driving program, all while sending instructions to the Raspberry Pi pi-rc server. 

Finally, the RC car unit is responsible for driving and being fun to play with. Since this is a simple toy RC car, it has binary valued inputs (on/off). When you press forward on the car, the resistance between the relevant motor controller chip pin number and ground is zero, which allows current to flow and drives the motor forward. Since this is done with the remote control, exact functions can be done with the Raspberry Pi as it can act like a radio transmitter.

It must be noted that while the car looks amazing with a giant cardboard roof rack and goodies attached to it, *significant* efforts of engineering went into making sure components were fastened sturdily. Here string was used to fasten the Pi Camera to the cardboard camera stand and careful drilling was done with the shown screwdriver. 

[![String](http://i.imgur.com/9XMgNmyl.jpg)](http://i.imgur.com/9XMgNmyl.jpg)

All jokes aside, building this contraption was very rewarding because I had to utilize household materials and a little bit of creativity (making the camera stand not wiggle and bounce while the car is driving) to making sure all components were logically placed and securely fastened. While assembling and setting everything up, I felt like a real engineer, even if these are just small scale toys, as I can realistically see myself devoting the time to applying this to actual production vehicles/technology. 

### In Depth

Here comes the fun part: understanding how it works. 

You and I both see the world, and in this case, the paper track, as a three dimensional object with contrasting colors  marking the edges of where the track begins and ends. However, as advanced as the computer and camera are, they cannot see such magical things. Grayscale images that the camera sees actually a matrix of real valued integers in the range [0, 255] where 0 is pure black and 255 is pure white. While this image may be obvious to us that we are about to drive off the track

[![Track](http://i.imgur.com/zFCNGGQm.png)](http://i.imgur.com/zFCNGGQm.png)

the computer actually can only see this (an example and cropped portion):

[![WhatComputerSees](http://i.imgur.com/JKdO2W8l.jpg)](http://i.imgur.com/JKdO2W8l.jpg)

While this may look like a mess, this actually serves a purpose: computers like numbers and do calculations quickly. However, we need to make sure we preprocess the images so the model has an easier time to train. 

The Pi Camera streamed images at a QVGA (240x320) resolution, and while cranking down the resolutions helps with speed and overall size, there were still portions of the image we don't really care about, such as the upper half. Actually, the above half has already been cropped to 120x320. The original image was twice the height and this extra portion contained useless information such as the door to the room and the wall.

In order to logically store the images into a neat matrix of [N x D], where N is the number of images and D is the dimensionality (in this case, total pixels where D = 120x320 = 38400), I flatten or reshape each image from 120x320 to 1x38400. This way I can neatly stack the images on top of each other in another matrix where I keep every single recorded image instance along with its corresponding direction label. 

The direction label is a one hot encoded vector of binary values corresponding to the direction I pressed. Since there are 4 classes to pick from (left, right, up, down), the vector is 4-dimensional. Depending on which direction I pressed, that index in the vector is assigned the value "1" while the rest of the indices are assigned "0" e.g ```left = [1,0,0,0]```. I do this because direction is a categorical value that cannot be compared to mathematically. If I were to assign (0, 1, 2, 3) to (left, right, up down), it would not make sense to compare the numbers because while ```0 < 1```, how can "left" be "less than" or "not as important" as "right?" After the image and paired direction is stored into the ```.npz``` file (pipeline pictured below for easy visualization), it's time to train the model. 

Pipeline:

[![pipeline](https://zhengludwig.files.wordpress.com/2015/07/collect_train_data.jpg?w=1016&h=406)](https://zhengludwig.files.wordpress.com/2015/07/collect_train_data.jpg?w=1016&h=406)

The model used is a feed forward neural network, sometimes called an "artificial neural network (ANN)" or "multi-layer perceptron (MLP)." The neural net is especially good at learning patterns and feature hierachies (in our case, the features are the pixel data) and also because once the neural network is trained, the parameters need only be saved and loaded, making predictions quick enough for real time usage. 

After loading the ```.npz``` files and sorting them to their appropriate matrices (one of training images and one for training labels), we can start to train the network.

Here is an example of what our network looks like. I used a 3 layer feed forward neural network (3 not counting the input layer, so 2 hidden layers and 1 output layer):

[![neural](https://docs.google.com/drawings/d/1QZwp3L4NPYOlnlLubwiXchQCTk4TGUhHqQCw6H5JK6k/pub?w=819&h=452)](https://docs.google.com/drawings/d/1QZwp3L4NPYOlnlLubwiXchQCTk4TGUhHqQCw6H5JK6k/pub?w=819&h=452)

The way the network learns is by the method of backpropagation. You can think of it like this: you have a bunch of people with knobs and valves that control how influencial a certain node is. Image data is input into the input layer one by one, and the people begin furiously turning knobs (weights of the nodes), trying to achieve the desired output at the output layer. Once the last person gives their output, this is known as the forward pass. Now, we need to backpropagate the errors. The last layer will get feedback based on how well they did and how much they need to be punished (this is determined by the loss function, which tells you how "off" you were from your desired target.) They report this feedback, also known as the gradient, recursively backwards until it goes to the front, where another forward pass will then commence, this time with updated information for knob turning (weights). This continues until differences in weight updates are miniscule (I've used 1e-3 in the past but this can be changed.)

Eventually the model will converge and will have finished training, hopefully with a reasonable training accuracy. The parameters are then saved locally and the next time we load from this model, we will have the weights ready to go and can accept streamed images real time and use them for prediction. 

### Results

With the current code, I can achieve roughly 96% validation accuracy which is pretty good. Validation accuracy is important because it allows us to infer how well the model can generalize to new situations. There are many ways to perform model validation. I use a validation split of 2.5%, where 2.5% of the shuffled training data is held out and not used to train the model. The model then attempts to predict, using the validation data, and the accuracy is reported. 

There are more results located in a comment block at the bottom of ```train.py```. 
### Problems

To be continued...

### Future Updates

In the future I hopefully plan to implement the following things:
* Model Architecture change
  - use a convolutional neural network
* Proper working thresholding
  - driving on the blue tape track
* Changes in motor speed
  - can drive in complex track layouts
* Object detection
  - recognize stop signs and traffic lights

### Special Thanks

Special thanks to [Multunus](http://www.multunus.com/?utm_source=github) for the project idea and implmentation help. Check out their self driving car [here](https://github.com/multunus/autonomous-rc-car). Also thanks to Zheng Wang and his version of the car as well. Details can be found at his [wordpress](https://zhengludwig.wordpress.com/projects/self-driving-rc-car/). 
