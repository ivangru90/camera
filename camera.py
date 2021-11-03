import cv2
import sys
import os
import time
import json
from PyQt5.QtWidgets import  QWidget, QLabel, QApplication, QPushButton, QGridLayout, QComboBox
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtMultimedia import QCameraInfo


class Config():
  # Video Encoding, might require additional installs
  # Types of Codes: http://www.fourcc.org/codecs.php
  VIDEO_TYPE = {
    'avi': cv2.VideoWriter_fourcc(*'DIVX'),
    'mp4': cv2.VideoWriter_fourcc(*'H264'),
  }

  # Standard Video Dimensions Sizes (depends on camera)
  STD_DIMENSIONS = {}
  with open('resolutions.json') as json_file:
    data = json.load(json_file)
    for d in data['resolutions']:
      (w,h) = (d['width'],d['height'])
      STD_DIMENSIONS[str(d['width'])+'x'+str(d['height'])] = (int(w),int(h))

  # camera parameteres
  frames_per_second = 25
  camera_id = 0

  # change resolution
  def change_res(self, cap, width, height):
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

  # grab resolution dimensions and set video capture to it
  def get_dimension(self, cap, res):
    if res in self.STD_DIMENSIONS:
      width,height = self.STD_DIMENSIONS[res]
    self.change_res(cap, width, height) # change the current caputre device to the resulting resolution
    return width, height

  # get video type
  def get_video_type(self, video_type_name):
    if video_type_name in self.VIDEO_TYPE:
      return  self.VIDEO_TYPE[video_type_name]
    return self.VIDEO_TYPE['avi']

  def get_all_dimensions(self):
    return list(self.STD_DIMENSIONS.keys())

  def get_all_video_types(self):
    return list(self.VIDEO_TYPE.keys())

class Camera(QThread):
  changePixmap = pyqtSignal(QImage)

  config = Config()
  video_type_name = config.get_all_video_types()[0]
  dimension_name = config.get_all_dimensions()[0]
  take_a_photo = False
  save = False
  writer_created = False

  def run(self):
    cap = cv2.VideoCapture(self.config.camera_id, cv2.CAP_DSHOW)
    while True:
      ret, frame = cap.read()
      if ret:
        # https://stackoverflow.com/a/55468544/6622587
        rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgbImage.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
        p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
        self.changePixmap.emit(p)
        if self.take_a_photo:
          cv2.imwrite(self.set_image_filename(),frame)#TODO: check resolution
          self.take_a_photo = False
        if self.save:
          if not self.writer_created:
            out = cv2.VideoWriter(self.set_video_filename(self.video_type_name, self.dimension_name), self.config.get_video_type(self.video_type_name), 
                                  self.config.frames_per_second, self.config.get_dimension(cap, self.dimension_name))
            self.writer_created = True
          out.write(frame)
        else:
          out = None

  # create filename for video
  def set_video_filename(self, video_type_name, dimension_name):
    filename = os.path.join('data', 'videos', 'video_' + dimension_name + '_'+ time.strftime("%d-%b-%Y-%H_%M_%S") + '.' + video_type_name)
    return filename

  # create filename for image
  def set_image_filename(self):
    filename = os.path.join('data', 'images', 'image_' + time.strftime("%d-%b-%Y-%H_%M_%S") + '.JPG')
    return filename

  # update flag to take a photo
  def set_photo(self):
    self.take_a_photo = True

  # update save flag and writer flag when recording started/stopped
  def set_recording(self):
    if self.save:
      self.save = False
      self.writer_created = False
    else:
      self.save = True

  # update camera when it is changed in combobox
  def select_camera(self, i):
    self.config.camera_id = i

  # update video type when it is changed in combobox
  def select_video_type(self, i):
    self.video_type_name = self.config.get_all_video_types()[i]

  # update dimension when it is changed in combobox
  def select_dimension(self, i):
    self.dimension_name = self.config.get_all_dimensions()[i]

class App(QWidget):
    def __init__(self):
      super().__init__()
      self.title = 'Camera App'
      self.left = 100
      self.top = 100
      self.width = 640
      self.height = 480
      self.config = Config()
      self.initUI()

    @pyqtSlot(QImage)
    def setImage(self, image):
      self.label.setPixmap(QPixmap.fromImage(image))

    def initUI(self):
      self.setWindowTitle(self.title)
      self.setGeometry(self.left, self.top, self.width, self.height)
      self.recording_started = False
      
      # set layout
      self.grid_layout = QGridLayout()
      self.setLayout(self.grid_layout)

      # check available cameras
      available_cameras = QCameraInfo.availableCameras()
      if not available_cameras:
        sys.exit()

      # create text label
      self.text_label = QLabel('')

      # create a label for showing video
      self.label = QLabel(self)
      self.label.resize(640, 480)
      camera = Camera(self)
      camera.changePixmap.connect(self.setImage)
      camera.start()
      self.grid_layout.addWidget(self.label)

      # take a photo button
      self.btn_photo = QPushButton('Take a photo')
      self.btn_photo.clicked.connect(camera.set_photo)
      self.grid_layout.addWidget(self.btn_photo)

      # start recording button
      self.btn_record_start = QPushButton('Start recording')
      self.btn_record_start.clicked.connect(camera.set_recording)
      self.btn_record_start.clicked.connect(self.update_ui)
      self.grid_layout.addWidget(self.btn_record_start)

      # end recording button
      self.btn_record_stop = QPushButton('End recording')
      self.btn_record_stop.clicked.connect(camera.set_recording)
      self.btn_record_stop.clicked.connect(self.update_ui)
      self.btn_record_stop.setEnabled(False)
      self.grid_layout.addWidget(self.btn_record_stop)

      # creating a combo box for selecting camera
      self.camera_selector = QComboBox()
      self.camera_selector.setToolTip("Select camera")
      self.camera_selector.setToolTipDuration(2500)
      self.camera_selector.addItems([camera.description() for camera in available_cameras])
      self.camera_selector.currentIndexChanged.connect(camera.select_camera)
      self.grid_layout.addWidget(self.camera_selector)

      # creating a combo box for selecting video type
      self.video_type_selector = QComboBox()
      self.video_type_selector.setToolTip("Select video type")
      self.video_type_selector.setToolTipDuration(2500)
      self.video_type_selector.addItems(self.config.get_all_video_types())
      self.video_type_selector.currentIndexChanged.connect(camera.select_video_type)
      self.grid_layout.addWidget(self.video_type_selector)

      # creating a combo box for selecting dimension
      self.dimension_selector = QComboBox()
      self.dimension_selector.setToolTip("Select dimension")
      self.dimension_selector.setToolTipDuration(2500)
      self.dimension_selector.addItems(self.config.get_all_dimensions())
      self.dimension_selector.currentIndexChanged.connect(camera.select_dimension)
      self.grid_layout.addWidget(self.dimension_selector)

      # add text label at the end of grid
      self.grid_layout.addWidget(self.text_label)

      self.show()

    # update buttons enabled/disabled when corresponding action is taken
    def update_ui(self):
      if self.recording_started:
        self.recording_started = False
        self.btn_record_start.setEnabled(True)
        self.btn_record_stop.setEnabled(False)
        self.camera_selector.setEnabled(True)
        self.video_type_selector.setEnabled(True)
        self.dimension_selector.setEnabled(True)
        self.text_label.setText('')
      else:
        self.recording_started = True
        self.btn_record_start.setEnabled(False)
        self.btn_record_stop.setEnabled(True)
        self.camera_selector.setEnabled(False)
        self.video_type_selector.setEnabled(False)
        self.dimension_selector.setEnabled(False)
        self.text_label.setText('Recording started, in progress...')

if __name__=="__main__":
  app=QApplication(sys.argv)
  ex = App()
  ex.show()
  sys.exit(app.exec_())