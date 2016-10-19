SmallSelfSteeringSuperCar
=========================

This was small project aimed at applying machine learning to a fun practical real life demo. The system uses a toy RC supercar (Lamborghini Veneno) with basic inputs (forward, reverse, left, right), a Raspberry Pi 3 Model B, a Raspberry Pi Camera, and a computer (MacBook Pro) to process images and to train the auto-driving model. 

Here's a video:

[![SmallSelfSteeringSuperCar](http://i3.ytimg.com/vi/c7R_Kfbgi4E/hqdefault.jpg)](https://www.youtube.com/watch?v=c7R_Kfbgi4E)

If you would like to view the details behind this project, feel free to click on the "Details" section in the table of contents. There you will find a concise breakdown of how the car manages to drive itself and how amazing it actually is.

## Table of Contents

- [Installation](#installation)
    - [Dependencies](#dependencies)
- [Setting up Pi-rc](#pi-rc)
- [Setting up local computer](#local-computer)
    - [Training](#training)
    - [Testing](#testing)
- [Details](#details)
    - [Motivation](#motivation)
    - [Breakdown](#breakdown)
    - [Neural Networks](#neuralnetworks)
- [License](#license)
- [Future Updates](#updates)
- [Special Thanks](#thanks)

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
  
### pi-rc

Pi-rc is used in this project as the way to control the RC car without the use of the supplied remote control. It allows me to be able to drive the car on my computer, both for fun and to store keyboard directions, which I will get to later. 

You can install pi-rc [here](https://github.com/bskari/pi-rc). From the pi-rc repo follow the instructions to set it up as the configuration JSON file varies depending on what model RC car you have (mostly operating frequencies.)

Pi-rc will be required on **both** the Raspberry Pi and local computer, as the Raspberry Pi will be running as the server in which the local computer will send commands to move the car. 

### local computer

The local computer is responsible for issuing RC commands to the Raspberry Pi, collecting the training image data from a TCP stream, storing it, training the model using Keras with the images, and testing the actual auto-driving model. 

Make sure you have [Keras](https://keras.io/) installed as this is the main framework for building our machine learning model. Once you have verified that the RC car is working (you can control it through your local computer following the guide on the pi-rc repository), continue onto the training section.

### Training

Before beginning to train the car, ensure that the pi-rc server is running on the Raspberry Pi. ```cd``` into wherever you've placed the pi-rc folder and run pi_pcm by typing: 

```sudo ./pi_pcm```

dfdf

The model used is a feed forward neural network, sometimes called an "artificial neural network (ANN)" or "multi-layer perceptron (MLP)" to train a remote-controlled car to navigate a track laid out with sheets of paper (for now.) 


