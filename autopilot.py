import pygame
import pygame.font
import numpy as np
import socket
import argparse
import json
import cStringIO
import io
import time

from keras.models import load_model
from pygame.locals import *
from common import dead_frequency
from common import server_up
from PIL import Image, ImageFile
from autopy import key


UP = LEFT = DOWN = RIGHT = False
QUIT = False
ImageFile.LOAD_TRUNCATED_IMAGES = True
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

def interactive_control(host, port, configuration):
  # Setting up server
  server_socket = socket.socket()
  server_socket.bind(('192.168.1.186', 8000))
  server_socket.listen(0)

  # accept Raspberry Pi connection
  connection = server_socket.accept()[0].makefile('rb')
  pygame.init()

  # Creating labels using one hot encoding method. There are 4 commands: 
  # up, down, left, right, and therefore labels are 4 dimensional
  # vectors. 
  labels = np.zeros((4,4), 'float')
  for i in range(4):
    labels[i,i] = 1
  # The actual assignment of keypress to label
  temp_label = np.zeros((1,4), 'float')

  model = load_model('autopilot.h5')

  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  # Assign send_inst to True initially; stream condition
  global send_inst
  send_inst = True

  # Image is 320x120 that is reshaped into one row vector
  image_array = np.zeros((1, 38400))
  image_label = np.zeros((1,4), 'float')
  saved_frame = 0
  total_frames = 0

  print 'Collecting images...'
  

  # Stream the image frame by frame
  while not QUIT:
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
          image = image.convert(mode='L')
          image = np.asarray(image)
          image = np.array(np.asarray(image))
          image_crop = image[120:240,:]
          temp_array = image_crop.reshape(1, 38400).astype(np.float32)

          up, down, left, right, change = get_keys()
          prediction = model.predict(temp_array)
          print prediction
          predict = np.argmax(prediction)

          if predict == 0:
            key.toggle(long(key.K_LEFT), True)
            time.sleep(0.10)
            key.toggle(long(key.K_LEFT), False)
          if predict == 1:
            key.toggle(long(key.K_RIGHT), True)
            time.sleep(0.10)
            key.toggle(long(key.K_RIGHT), False)
          if predict == 2:
            key.toggle(long(key.K_UP), True)
            time.sleep(0.10)
            key.toggle(long(key.K_UP), False)
          if predict == 3:
            key.toggle(long(key.K_DOWN), True)
            time.sleep(0.10)
            key.toggle(long(key.K_DOWN), False)


          if change:
              # Something changed, so send a new command
            command = 'idle'
            if up:
                command = 'forward'
                
            elif down:
                command = 'reverse'
                
            append = lambda x: command + '_' + x if command != 'idle' else x

            if left:
                command = append('left')
                
            elif right:
                command = append('right')

            print(command)
            try:
                sock.sendto(configuration[command], (host, port))
            except TypeError:
                # Windows + Python 3 workaround?
              sock.sendto(bytes(configuration[command], 'utf-8'), (host, port))

    finally: 
      connection.close()
      server_socket.close()

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
if __name__ == '__main__':
  main()