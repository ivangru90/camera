import pandas as pd
import cv2
import json


url = "https://en.wikipedia.org/wiki/List_of_common_resolutions"
table = pd.read_html(url)[0]
table.columns = table.columns.droplevel()


#TODO: add camara_id in json object, do this for all cameras
cap = cv2.VideoCapture(0)
resolutions = set()
result = {}

for index, row in table[["W", "H"]].iterrows():
  cap.set(cv2.CAP_PROP_FRAME_WIDTH, row["W"])
  cap.set(cv2.CAP_PROP_FRAME_HEIGHT, row["H"])
  width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
  height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
  resolutions.add((width, height))

result['resolutions'] = []
for r in resolutions:
  resolution = {}
  resolution['width'] = r[0]
  resolution['height'] = r[1]
  result['resolutions'].append(resolution)

with open('resolutions.json','w+') as f:
  json.dump(result, f)
