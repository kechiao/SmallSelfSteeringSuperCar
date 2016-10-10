# Name:         self_control_train.py
# Description:  Allows user to collect training images for training of the 
#               neural network used to autonomously drive.
# Instructions: First make sure Raspberry Pi is turned on and is running 
#               'stream_image_client.py'. Use arrow keys to maneuver the 
#               car and images will be saved along with direction.
# References:   Most of the PyGame control and server information is taken
#               directly from https://github.com/bskari/pi-rc/blob/master/interactive_control.py
# Notes:        I have made modifications to the code obtained from above in order
#               to streamline the training process.

import pygame
import pygame.font
import numpy as np
import socket
import argparse
import json
import cStringIO
import io
import time

from pygame.locals import *
from common import dead_frequency
from common import server_up
from PIL import Image


UP = LEFT = DOWN = RIGHT = False
QUIT = False

# Name:      load_configuration(configuration_file)
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

# Name:      interactive_control(host, port, configuration)
# Description: Runs the interactive control.
def interactive_control(host, port, configuration):
  # Setting up server
  server_socket = socket.socket()
  server_socket.bind(('192.168.1.185', 8000))
  server_socket.listen(0)

  # accept Raspberry Pi connection
  connection = server_socket.accept()[0].makefile('rb')

  # Creating labels using one hot encoding method. There are 4 commands: 
  # up, down, left, right and therefore labels are 4 dimensional
  # vectors. 
  labels = np.zeros((4,4), 'float')
  for i in range(4):
    labels[i,i] = 1
  # The actual assignment of keypress to label
  temp_label = np.zeros((1,4), 'float')

  # Starting PyGame window to control RC Car
  pygame.init()

  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  # Assign send_inst to True initially; stream condition
  global send_inst
  send_inst = True
  global command 
  command = 'idle'
  # Image is 320x120 that is reshaped into one row vector
  image_array = np.zeros((1, 38400))
  image_label = np.zeros((1,4), 'float')
  saved_frame = 0
  total_frames = 0
  
  print 'Collecting images...'
    
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
        image = Image.open(cStringIO.StringIO(jpg))
        start = time.clock()
        image = image.convert(mode='L')
        image = np.asarray(image)
        # Cropping the interesting portions
        image_crop = image[120:240, :]
        temp_array = image_crop.reshape(1, 38400).astype(np.float32)

        frame += 1
        total_frames += 1
       
        for event in pygame.event.get():
          if event.type == KEYDOWN:
            key_input = pygame.key.get_pressed()

            if key_input[pygame.K_w]:
              print 'Forward'
              command = 'forward'
              saved_frame += 1
              image_array = np.vstack((image_array, temp_array))
              image_label = np.vstack((image_label, labels[2]))

            elif key_input[pygame.K_w] and key_input[pygame.K_d]:
              print 'Forward and Right'
              command = 'forward_right'
              saved_frame += 1
              image_array = np.vstack((image_array, temp_array))
              image_label = np.vstack((image_label, labels[1]))

            elif key_input[pygame.K_w] and key_input[pygame.K_a]:
              print 'Forward and Left'
              command = 'forward_left'
              saved_frame += 1
              image_array = np.vstack((image_array, temp_array))
              image_label = np.vstack((image_label, labels[0]))

            elif key_input[pygame.K_s] and key_input[pygame.K_a]:
              print 'Reverse and Left'
              command = 'reverse_left'

            elif key_input[pygame.K_w] and key_input[pygame.K_d]:
              print 'Reverse and Right'
              command = 'reverse_right'

            elif key_input[pygame.K_s]:
              print 'Reverse'
              command = 'reverse'
              saved_frame += 1
              image_array = np.vstack((image_array, temp_array))
              image_label = np.vstack((image_label, labels[3]))

            elif key_input[pygame.K_a]:
              print 'Left'
              command = 'left'
              saved_frame += 1
              image_array = np.vstack((image_array, temp_array))
              image_label = np.vstack((image_label, labels[0]))

            elif key_input[pygame.K_d]:
              print 'Right'
              command = 'right'
              saved_frame += 1
              image_array = np.vstack((image_array, temp_array))
              image_label = np.vstack((image_label, labels[1]))

            elif key_input[pygame.K_q]:
              print 'Quitting'
              send_inst = False
              break

          elif event.type == pygame.KEYUP:
            print 'Idle'
            command = 'idle'

      
          try:
              sock.sendto(configuration[command], (host, port))
          except TypeError:
              # Windows + Python 3 workaround?
              sock.sendto(bytes(configuration[command], 'utf-8'), (host, port))


    train = image_array[1:,:]
    end = time.clock()
    training_labels = image_label[1:,:]
    # Saving images and labels to disk
    print 'Saving data...'
    np.savez('test.npz', train=train, train_labels = training_labels)

    print 'Total Frames:', total_frames
    print 'Saved Frames:', saved_frame
    print 'Dropped Frames:', total_frames - saved_frame
    print 'FPS: %.2f' % (frame / (start - end))

  finally: 
    connection.close()
    server_socket.close()
    pygame.quit()

# Name:     make_parser()
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

# Name:     main()
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
