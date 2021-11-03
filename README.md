# fashion_segmentation

Application allow you to create images and videos from all available cameras. Images/videos will be saved in /data/images, ie. for /data/videos for videos.

## Camera application

Requirements:
* python 3.9
* have openh264-1.8.0-win64.dll in application folder for mp4 video format

## Installation

Steps:
* run first find_resolution.py - This is important because this will find all available resolutions for all available cameras on computer. This will create resolutions.json file with this information, it will be used in the application to fullfil combobox for resolutions.
* run camera.py - This will start the app.