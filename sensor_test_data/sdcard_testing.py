"""
sdcard_testing.py 

credit: 
# Rui Santos & Sara Santos - Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-microsd-card-micropython/

Code to test writing files to sd card

"""

 
from machine import SPI, Pin
import sdcard, os

# Constants, we followed this pinout too maybe?  
SPI_BUS = 0
SCK_PIN = 2
MOSI_PIN = 3
MISO_PIN = 4
CS_PIN = 5
SD_MOUNT_PATH = '/sd'
FILE_PATH = 'sd/sd_test_file2.txt'

file_list = ['sd/sd_test_2.txt', 'sd/sd_test_3.txt']

try:
    # Init SPI communication
    spi = SPI(SPI_BUS,sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(MISO_PIN))
    cs = Pin(CS_PIN)
    sd = sdcard.SDCard(spi, cs)
    # Mount microSD card
    os.mount(sd, SD_MOUNT_PATH)
    # List files on the microSD card
    print(os.listdir(SD_MOUNT_PATH))
    
    for file_path in file_list:
        
        with open(file_path, "w") as file:
            file.write("Testing microSD Card writing in loop \n")
        
        with open(file_path, "a") as file:
            file.write("testing appending a line :) \n")
    
    # Create new file on the microSD card
    #with open(FILE_PATH, "w") as file:
        # Write to the file
     #   file.write("Testing microSD Card \n")
        
    #with open(FILE_PATH, "a") as file:
     #   file.write("I still love squirtle :) \n")
        
    # Check that the file was created:
        print(os.listdir(SD_MOUNT_PATH))
    
    # Open the file in reading mode
    #with open(FILE_PATH, "r") as file:
        # read the file content
     #   content = file.read()
      #  print("File content:", content)  
    
    os.umount(SD_MOUNT_PATH)
except Exception as e:
    print('An error occurred:', e)
