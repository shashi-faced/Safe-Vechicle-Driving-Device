
from scipy.spatial import distance as dist
from imutils.video import FileVideoStream
from imutils.video import VideoStream
from imutils import face_utils
import numpy as np
import argparse
import imutils
import time
import dlib
import cv2
import pyrebase

config = {
    'apiKey': "AIzaSyD_GyCmrARLpt2HMzEfBKq1WgY6vWZxLw4 ",
    'authDomain': "svdd-80416.firebaseapp.com",
    'databaseURL': "https://svdd-80416.firebaseio.com",
    'projectId': "svdd-80416",
    'storageBucket': "svdd-80416.appspot.com",
    'messagingSenderId': "463172115578"
  }
firebase = pyrebase.initialize_app(config)


db = firebase.database()

def eye_aspect_ratio(eye):
	
	A = dist.euclidean(eye[1], eye[5])
	B = dist.euclidean(eye[2], eye[4])
	C = dist.euclidean(eye[0], eye[3])

	ear = (A + B) / (2.0 * C)

	
	return ear
 

EYE_AR_THRESH = 0.3
EYE_AR_CONSEC_FRAMES = 3


COUNTER = 0
TOTAL = 0


print("[INFO] loading facial landmark predictor...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')


(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]


print("[INFO] starting video stream thread...")

vs = FileVideoStream(0).start()

fileStream = True

time.sleep(1.0)



count2 = 0
while True:
	
	if fileStream and not vs.more():
		break

	
	frame = vs.read()
	frame = imutils.resize(frame, width=450)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	
	rects = detector(gray, 0)

	
	for rect in rects:
		
		shape = predictor(gray, rect)
		shape = face_utils.shape_to_np(shape)

		
		leftEye = shape[lStart:lEnd]
		rightEye = shape[rStart:rEnd]
		leftEAR = eye_aspect_ratio(leftEye)
		rightEAR = eye_aspect_ratio(rightEye)

		
		ear = (leftEAR + rightEAR) / 2.0

		
		leftEyeHull = cv2.convexHull(leftEye)
		rightEyeHull = cv2.convexHull(rightEye)
		cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
		cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

		
		
		
		if ear < EYE_AR_THRESH:
			COUNTER += 1
			
			db.child('driver_status/status').set('present')
		
                                

		
		else:
			
			if COUNTER >= EYE_AR_CONSEC_FRAMES:
				TOTAL += 1
				count2 = 0
				db.child('driver_status/status').set('absent')

			
			COUNTER = 0

		
		cv2.putText(frame, "Blinks: {}".format(TOTAL), (10, 30),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
		cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
	
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF
 
	
	if key == ord("q"):
		break


cv2.destroyAllWindows()
vs.stop()
