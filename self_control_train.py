# Name:         self_control_train.py
# Description:  Allows user to collect training images for training of the 
#               neural network used to autonomously drive.
# Instructions: First make sure Raspberry Pi is turned on and is running 
#               'stream_image_client.py' and 'pi_pcm'. Use arrow keys to maneuver the
#               car and images will be saved to current directory along with direction.
# References:   Most of the PyGame control and server information is taken
#               directly from https://github.com/bskari/pi-rc/blob/master/interactive_control.py
# Notes:        I have made modifications to the code obtained from above in order
#               to streamline the training process to work with pi-rc and Keras.

import pygame
import pygame.font
import numpy as np
import socket
import argparse
import json
import cStringIO
import io

from pygame.locals import *
from common import dead_frequency
from common import server_up
from PIL import Image, ImageFile
from matplotlib import pyplot as plt 
from numpy import ma
from scipy import ndimage


UP = LEFT = DOWN = RIGHT = False
QUIT = False
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Name:        load_configuration(configuration_file)
# Description: Generates a dict of JSON command messages for each movement.
def load_configuration(configuration_file):
    configuration = json.loads(configuration_file.read())
    dead = dead_frequency(configuration['frequency'])
    sync_command = {
        'frequency': configuration['frequency'],
        'dead_frequency': dead,
        'burst_us': configuration['synchronization_burst_us'],
        'spacing_us': configuration['synchronization_spacing_us'],
        'repeats': configuration['total_synchronizations'],
    }
    base_command = {
        'frequency': configuration['frequency'],
        'dead_frequency': dead,
        'burst_us': configuration['signal_burst_us'],
        'spacing_us': configuration['signal_spacing_us'],
    }
    movement_to_command = {}
    for key in (
        'forward',
        'forward_left',
        'forward_right',
        'left',
        'reverse',
        'reverse_left',
        'reverse_right',
        'right',
    ):
        command_dict = base_command.copy()
        command_dict['repeats'] = configuration[key]
        movement_to_command[key] = command_dict

    direct_commands = {
        key: json.dumps([sync_command, movement_to_command[key]])
        for key in movement_to_command
    }

    # We also need to add an idle command; just broadcast at the dead frequency
    command_dict = [base_command.copy()]
    command_dict[0]['frequency'] = dead
    command_dict[0]['repeats'] = 20  # Doesn't matter
    direct_commands['idle'] = json.dumps(command_dict)

    return direct_commands

# Name:        get_keys()
# Description: Returns a tuple of (UP, DOWN, LEFT, RIGHT, changed) representing which
#              keys are UP or DOWN and whether or not the key states changed.
def get_keys():
    change = False
    key_to_global_name = {
        pygame.K_LEFT: 'LEFT',
        pygame.K_RIGHT: 'RIGHT',
        pygame.K_UP: 'UP',
        pygame.K_DOWN: 'DOWN',
        pygame.K_ESCAPE: 'QUIT',
        pygame.K_q: 'QUIT',
    }
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            global QUIT
            QUIT = True
            global send_inst
            send_inst = False
        elif event.type in {pygame.KEYDOWN, pygame.KEYUP}:
            down = (event.type == pygame.KEYDOWN)
            change = (event.key in key_to_global_name)

            if event.key in key_to_global_name:
                globals()[key_to_global_name[event.key]] = down

    return (UP, DOWN, LEFT, RIGHT, change)

# Name:        interactive_control(host, port, configuration)
# Description: Runs the interactive control.
def interactive_control(host, port, configuration):
  # Setting up server
  server_socket = socket.socket()
  server_socket.bind(('192.168.1.186', 8000))
  server_socket.listen(0)
  
  # accept Raspberry Pi connection
  connection = server_socket.accept()[0].makefile('rb')
  
  # Creating labels using one hot encoding method. There are 4 commands: 
  # up, down, left, right, and therefore labels are 4 dimensional
  # vectors. E.g. [1 0 0 0] is label for 'Left'
  labels = np.zeros((4,4), 'float')
  for i in range(4):
    labels[i,i] = 1
  
  # The actual assignment of keypress to label
  temp_label = np.zeros((1,4), 'float')

  # Starting PyGame window to control RC Car
  # Making it look pretty :-)
  pygame.init()
  size = (300, 400)
  screen = pygame.display.set_mode(size)
  # pylint: disable=too-many-function-args
  background = pygame.Surface(screen.get_size())
  clock = pygame.time.Clock()
  black = (0, 0, 0)
  white = (255, 255, 255)
  big_font = pygame.font.Font(None, 40)
  little_font = pygame.font.Font(None, 24)
  pygame.display.set_caption('rc-pi interactive')
  text = big_font.render('Use arrows to move', 1, white)
  text_position = text.get_rect(centerx=size[0] / 2)
  background.blit(text, text_position)
  screen.blit(background, (0, 0))
  pygame.display.flip()

  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  
  # Assign send_inst to True initially; stream condition
  global send_inst
  send_inst = True

  # Image is 320x120 that is reshaped into one row vector
  # These are just empty containers so we can concatenate the images
  # that we are using later.
  image_array = np.zeros((1, 38400))
  image_label = np.zeros((1,4), 'float')
  saved_frame = 0
  total_frames = 0

  while not QUIT:
      # Starting to collect images for training
      print 'Collecting images...'
      # Image is 320x120 that is reshaped into one row vector
      # image_array = np.zeros((1, 38400))
      # image_label = np.zeros((1,4), 'float')

      # Stream the image frame by frame
      try: 
        stream_bytes = ' '
        frame = 1
        while send_inst:
          stream_bytes += connection.read(1024)
          # JPEG image files begin with FF D8 and end with FF D9
          first = stream_bytes.find('\xff\xd8')
          last = stream_bytes.find('\xff\xd9')
          if first != -1 and last != -1:
            jpg = stream_bytes[first:last + 2]
            stream_bytes = stream_bytes[last + 2:]
            # I use cStringIO to read the bytes wired in and use PIL to import this
            # imformation into a jpg picture. 
            image = Image.open(cStringIO.StringIO(jpg))
            # Convert the jpg image to greyscale
            image = image.convert(mode='L')
            # Convert the jpg to numpy operable format 
            image = np.array(np.asarray(image))
            image_crop = image[120:240,:]
            
            # This thresholding algorithm works but not at our implemenentation stage. So,
            # I am using just simple greyscaling. The below threshold attempts to segment the 
            # the color blue from any other colors.

            # image = image[120:240, :, :]
            # R = [(30,60),(30,60),(90,140)]
            # red_range = np.logical_and(R[0][0] < image[:,:,0], image[:,:,0] < R[0][1])
            # green_range = np.logical_and(R[1][0] < image[:,:,0], image[:,:,0] < R[1][1])
            # blue_range = np.logical_and(R[2][0] < image[:,:,0], image[:,:,0] < R[2][1])
            # valid_range = np.logical_and(red_range, green_range, blue_range)
            # image.flags.writeable = True
            # image[valid_range] = 200
            # image[np.logical_not(valid_range)] = 0
            # image_crop = image[:,:,2]

            temp_array = image_crop.reshape(1, 38400).astype(np.float32)

            frame += 1
            total_frames += 1

            # After
            up, down, left, right, change = get_keys()

            if change:
                # Something changed, so send a new command
                command = 'idle'
                
                if up:
                    command = 'forward'
                    saved_frame += 1
                    # Vertically concatenate this flattened image into the container made 
                    # earlier. Do the same to the label. 
                    image_array = np.vstack((image_array, temp_array))
                    image_label = np.vstack((image_label, labels[2]))
                    
                elif down:
                    command = 'reverse'
                    saved_frame += 1
                    image_array = np.vstack((image_array, temp_array))
                    image_label = np.vstack((image_label, labels[3]))

                append = lambda x: command + '_' + x if command != 'idle' else x

                if left:
                    command = append('left')
                    saved_frame += 1
                    image_array = np.vstack((image_array, temp_array))
                    image_label = np.vstack((image_label, labels[0]))
                elif right:
                    command = append('right')
                    saved_frame += 1
                    image_array = np.vstack((image_array, temp_array))
                    image_label = np.vstack((image_label, labels[1]))

                print(command)
                try:
                    sock.sendto(configuration[command], (host, port))
                except TypeError:
                    # Windows + Python 3 workaround?
                    sock.sendto(bytes(configuration[command], 'utf-8'), (host, port))

                # Show the command and JSON
                background.fill(black)
                text = big_font.render(command, 1, white)
                text_position = text.get_rect(centerx=size[0] / 2)
                background.blit(text, text_position)

                pretty = json.dumps(json.loads(configuration[command]), indent=4)
                pretty_y_position = big_font.size(command)[1] + 10
                for line in pretty.split('\n'):
                    text = little_font.render(line, 1, white)
                    text_position = text.get_rect(x=0, y=pretty_y_position)
                    pretty_y_position += little_font.size(line)[1]
                    background.blit(text, text_position)

                screen.blit(background, (0, 0))
                pygame.display.flip()
            
            # Limit to 20 frames per second
            clock.tick(60)

        # Since both containers' first entry are zeros, don't use that. 
        train = image_array[1:,:]
        training_labels = image_label[1:,:]

        # Saving images and labels to disk
        print 'Saving data...'
        np.savez('training_data/test.npz', train=train, train_labels = training_labels)

        print 'Total Frames:', total_frames
        print 'Saved Frames:', saved_frame
        print 'Dropped Frames:', total_frames - saved_frame

      finally: 
        connection.close()
        server_socket.close()

  pygame.quit()

# Name:         make_parser()
# Description:  Builds and returns an argument parser.
def make_parser():
    parser = argparse.ArgumentParser(
        description='Interactive controller for the Raspberry Pi RC.'
    )
    parser.add_argument(
        dest='control_file',
        help='JSON control file for the RC car.'
    )
    parser.add_argument(
        '-p',
        '--port',
        dest='port',
        help='The port to send control commands to.',
        default=12345,
        type=int
    )
    parser.add_argument(
        '-s',
        '--server',
        dest='server',
        help='The server to send control commands to.',
        default='127.1'
    )
    return parser

# Name:         main()
# Description:  Main function used to start the collection of training images.
def main():
    parser = make_parser()
    args = parser.parse_args()

    with open(args.control_file) as configuration_file:
        configuration = load_configuration(configuration_file)

    print('Sending commands to ' + args.server + ':' + str(args.port))

    frequency = json.loads(configuration['idle'])[0]['frequency']

    if not server_up(args.server, args.port, frequency):
        print('Server does not appear to be listening for messages, aborting')
        return

    interactive_control(args.server, args.port, configuration)

# This is a standard boilerplate function
if __name__ == '__main__':
    main() # Go to main function
