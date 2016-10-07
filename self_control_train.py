# Name:         self_control_train.py
# Description:  Allows user to collect training images for training of the 
#				neural network used to autonomously drive.
# Instructions: First make sure Raspberry Pi is turned on and is running 
#               'stream_image_client.py'. Use arrow keys to maneuver the 
#				car and images will be saved along with direction.

import pygame
from pygame.locals import *
import numpy as np
import socket




# Name: 		main()
# Description:  Main function used to start the collection of training images.
def main():
	collectImages()

# This is a standard boilerplate function
if __name__ == '__main__':
	main() # Go to main function
	