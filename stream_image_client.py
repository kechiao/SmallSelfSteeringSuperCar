# Name:         stream_image_client.py
# Description:  Allows the Raspberry Pi to act as streaming client, sending
#               jpegs to an ip destination, where the server will collect JPEGs
#               off the network.

# Reference:    PiCamera documentation
#               https://picamera.readthedocs.org/en/release-1.10/recipes2.html

import io
import socket
import struct
import time
import picamera


# Creating a socket and streams to ip address
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.1.101', 8000))
connection = client_socket.makefile('wb') 

try:
    with picamera.PiCamera() as camera:
        camera.resolution = (320, 240)  # Using QVGA as resolution; smaller size
        camera.framerate = 10           # Attempt 10 frames per second, can increase
        #camera.start_preview()
        time.sleep(3)                   # Give camera three seconds to warm up. 
        start = time.time()     
        stream = io.BytesIO()
        
        # Sending JPEGs in video stream
        for foo in camera.capture_continuous(stream, 'jpeg', use_video_port = True):
            connection.write(struct.pack('<L', stream.tell()))
            connection.flush()
            stream.seek(0)
            connection.write(stream.read())
            if time.time() - start > 600:  # Turn off connection after 10 minutes
                break
            stream.seek(0)
            stream.truncate()
    connection.write(struct.pack('<L', 0))
finally:
    connection.close()
    client_socket.close()