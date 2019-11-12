
import cv2
import numpy as np

def createAVI(fp,gd,arrs):
     # Define the codec and create VideoWriter object (from: https://stackoverflow.com/questions/51914683/how-to-make-video-from-an-updating-numpy-array-in-python)
    fourcc = cv2.VideoWriter_fourcc(*'PIM1')
    out = cv2.VideoWriter(fp,fourcc, 20.0, (gd.ncol, gd.nrow))
    for a in arrs:
        h = cv2.normalize(a, None, 255, 0, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        hsv = cv2.merge([h, h, h])
        out.write(hsv)
    out.release()

#     writer = cv2.VideoWriter(fp, cv2.VideoWriter_fourcc(*'PIM1'), 25, (gd.ncol, gd.nrow), False)
#     for a in arrs:
#         print(type(a))
#         writer.write(a)