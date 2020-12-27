from PyQt5.QtWidgets import QApplication, QComboBox, QLineEdit, QMessageBox, QTableWidget, QWidget, QPushButton, QHBoxLayout, QVBoxLayout,\
    QSlider, QStyle, QFileDialog, QTableWidget,QTableWidgetItem
import sys, os
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtCore import Qt, QUrl
import cv2
import dlib
import random
import string
from shutil import copyfile
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

class VideoSubtitleWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Video Subtitles Tagging Tool")
        self.setGeometry(350, 100, 700, 700)
        self.setWindowIcon(QIcon('./icons/playerIcon.jpg'))

        #init parameters
        self.recordingWord = False
        self.wordsCounter = 0
        self.currentCaptureStartTime = 0
        self.currentCaptureEndTime = 0
        self.tmpLipsIsolatedVideo = "./isolatedLips.avi"
        self.rootOfTaggedDataDir = "./tagged data"

        p =self.palette()
        p.setColor(QPalette.Window, Qt.black)
        self.setPalette(p)

        self.init_ui()

        self.show()


    def init_ui(self):
        #create media player object (none stands for parent - this object has no parent)
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        #create videowidget object
        videowidget = QVideoWidget()

        #create open button
        self.openBtn = QPushButton('Open Video')
        self.openBtn.clicked.connect(self.open_file)

        #create button for playing
        self.playBtn = QPushButton()
        self.playBtn.setEnabled(False) #Make this button disabled by default (before user selects a video)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playBtn.clicked.connect(self.play_video)

        #create button to start and finish specific word capture
        self.wordCaptureBtn = QPushButton('Record Word')
        self.wordCaptureBtn.setEnabled(False) #Make this button disabled by default (before user selects a video)
        self.wordCaptureBtn.clicked.connect(self.capture_word)
        
        #create button to indicate user finished all captures for this session
        self.finishAllCapturesFromVideo = QPushButton("Finish Words Capture For This Video (you have tagged {} words so far)".format(self.wordsCounter))
        self.finishAllCapturesFromVideo.setEnabled(False) #Make this button disabled by default (before user selects a video)
        self.finishAllCapturesFromVideo.clicked.connect(self.confirmation_before_processing)

        #create slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0,0)
        self.slider.sliderMoved.connect(self.set_position)

        #create dropbox to select video playing rate
        self.videoRateComboBox = QComboBox(self)
        self.videoRateComboBox.addItems(("1", "0.15", "0.25", "0.5", "0.75", "1.25", "1.5"))

        #create hbox (horizontal box) layout for video control bar
        videoControlBar = QHBoxLayout()
        videoControlBar.setContentsMargins(0,0,0,0)

        #set widgets to the hbox videoControlBar layout
        videoControlBar.addWidget(self.openBtn)
        videoControlBar.addWidget(self.playBtn)
        videoControlBar.addWidget(self.slider)
        videoControlBar.addWidget(self.videoRateComboBox)
        
        #create textbox for user to describe each word text
        self.wordText = QLineEdit(self)
        self.wordText.setDisabled(True)
        self.wordText.setStyleSheet("QLineEdit{background: grey;}")

        #create button to save captured word's text
        self.saveTextBtn = QPushButton('Save Word')
        self.saveTextBtn.setEnabled(False) #Make this button disabled by default (before user selects a video)
        self.saveTextBtn.clicked.connect(self.save_word)

        #create hbox (horizontal box) layout for transcript control bar
        wordsTranscriptControlBar = QHBoxLayout()
        wordsTranscriptControlBar.setContentsMargins(0,0,0,0)

        #create hbox for words transcript control bar
        wordsTranscriptControlBar.addWidget(self.wordCaptureBtn)
        wordsTranscriptControlBar.addWidget(self.wordText)
        wordsTranscriptControlBar.addWidget(self.saveTextBtn)

        self.create_table()

        #create vbox (vertical box) layout - vbox layout will include all horizontal boxes layouts
        vboxLayout = QVBoxLayout()
        vboxLayout.addWidget(videowidget)
        vboxLayout.addLayout(videoControlBar)
        vboxLayout.addLayout(wordsTranscriptControlBar)
        vboxLayout.addWidget(self.finishAllCapturesFromVideo)
        vboxLayout.addWidget(self.capturedWordsTable)

        self.setLayout(vboxLayout)

        self.mediaPlayer.setVideoOutput(videowidget)

        #media player signals
        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)
        self.videoRateComboBox.activated[str].connect(self.rate_changed)

        #textbox signal
        self.wordText.textChanged.connect(self.validate_textbox)

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Video")

        if filename != '':
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
            self.playBtn.setEnabled(True)
            self.wordCaptureBtn.setEnabled(True)
            self.finishAllCapturesFromVideo.setEnabled(True)
            self.videoFullPath = filename


    def play_video(self):
        self.openBtn.setDisabled(True) #Do not allow user to change a video on this session anymore 
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()

        else:
            self.mediaPlayer.play()

    def mediastate_changed(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)
            )

        else:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay)
            )

    def position_changed(self, position):
        self.slider.setValue(position)

    def duration_changed(self, duration):
        self.slider.setRange(0, duration)

    def set_position(self, position):
        self.mediaPlayer.setPosition(position)

    def handle_errors(self):
        self.playBtn.setEnabled(False)
        self.label.setText("Error: " + self.mediaPlayer.errorString())

    def rate_changed(self, text):
        self.mediaPlayer.setPlaybackRate(float(text))
    
    #Saving time with ms (miliseconds since video first begin)
    def capture_word(self):
        if self.recordingWord:
            #stop video and save position to dict (only if video is playing when user press this button)
            if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
                self.play_video()

            self.currentCaptureEndTime = self.mediaPlayer.position()
            
            self.wordCaptureBtn.setDisabled(True) #when user will give a valid text input to textbox, this btn will be enabled again
            self.playBtn.setDisabled(True) #when user will give a valid text input to textbox, this btn will be enabled again
            
            self.wordText.setStyleSheet("QLineEdit{background: white;}")
            self.wordText.setDisabled(False) #enable user type into textbox

        else:
            self.currentCaptureStartTime = self.mediaPlayer.position()
            self.wordCaptureBtn.setText('Finish Word Capture')
            self.recordingWord = True

    #validate text is not empty
    def validate_textbox(self, text):
        #clear whitespaces from begin and end of word
        text = text.lstrip()
        text = text.rstrip()
        
        if text != "":
            self.saveTextBtn.setEnabled(True) #allow user save this text
        else:
            self.saveTextBtn.setEnabled(False) #do allow user save empty text

    def save_word(self):
        self.wordsCounter += 1
        #save word text and times value to dict
        currentNumOfRows =  self.capturedWordsTable.rowCount()
        self.capturedWordsTable.setRowCount(currentNumOfRows + 1)
        self.capturedWordsTable.setItem(currentNumOfRows, 0, QTableWidgetItem(self.wordText.text()))
        self.capturedWordsTable.setItem(currentNumOfRows, 1, QTableWidgetItem(str(self.currentCaptureStartTime)))
        self.capturedWordsTable.setItem(currentNumOfRows, 2, QTableWidgetItem(str(self.currentCaptureEndTime)))

        #Set text of this row to horizontal and vertical center of each cell
        self.capturedWordsTable.item(currentNumOfRows, 0).setTextAlignment(Qt.AlignCenter)
        self.capturedWordsTable.item(currentNumOfRows, 1).setTextAlignment(Qt.AlignCenter)
        self.capturedWordsTable.item(currentNumOfRows, 2).setTextAlignment(Qt.AlignCenter)
        
        #make textbox ready for next capture
        self.wordText.setText("") #clear textbox
        self.wordText.setStyleSheet("QLineEdit{background: grey;}")
        self.wordText.setDisabled(True)
        
        #make capture button ready for next capture
        self.recordingWord = False
        self.wordCaptureBtn.setText('Record Word')

        #make video playable again
        self.playBtn.setDisabled(False)

        #let user start a new word capture
        self.wordCaptureBtn.setDisabled(False)

        #update finish session button text
        self.finishAllCapturesFromVideo.setText("Finish Words Capture For This Video (you have tagged {} words so far)".format(self.wordsCounter))

        #reset flag
        self.recordingWord = False
    
    def create_table(self):
        self.capturedWordsTable = QTableWidget()
        self.capturedWordsTable.setColumnCount(3)
        self.capturedWordsTable.setHorizontalHeaderLabels(['Text', 'Start Time [ms]', 'End Time [ms]'])
        
        self.capturedWordsTable.setRowCount(0)

        self.capturedWordsTable.horizontalHeader().setStretchLastSection(True)
        self.capturedWordsTable.setMaximumHeight(200)

    def confirmation_before_processing(self):
        confirmAlert = QMessageBox()
        confirmAlert.setWindowTitle("Confirmation Alert")
        confirmAlert.setWindowIcon(QIcon('icons/playerIcon.jpg'))
        confirmAlert.setIcon(QMessageBox.Question)
        confirmAlert.setText("Are you sure all times and texts you have tagged are correct?")
        confirmAlert.setInformativeText("If you want to delete one or more rows, just clear one of it's cells.")
        confirmAlert.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        confirmAlert.buttonClicked.connect(self.handle_user_confirmation)
        confirmAlert.exec_()

    def handle_user_confirmation(self, clickedBtn):
        if clickedBtn.text() == 'OK':
            if isolateLipsFromVideo(self.videoFullPath, self.tmpLipsIsolatedVideo) == 0:
                self.create_tagged_data_for_each_word()
                
                #remove isolated video with full length, not clipped
                os.remove(self.tmpLipsIsolatedVideo)

                finishedJobAlert = QMessageBox()
                finishedJobAlert.setWindowTitle("Finished Job")
                finishedJobAlert.setWindowIcon(QIcon('./icons/playerIcon.jpg'))
                finishedJobAlert.setText("Finished")
                finishedJobAlert.setStandardButtons(QMessageBox.Ok)
                finishedJobAlert.buttonClicked.connect(self.close_window)
                finishedJobAlert.exec_()
        #Else - do nothing

    def close_window(self):
        sys.exit()

    def create_tagged_data_for_each_word(self):
        #check if there is tagged data directory alreay
        if not os.path.isdir(self.rootOfTaggedDataDir):
            os.mkdir(self.rootOfTaggedDataDir)
        
        for rowIndex in range (self.capturedWordsTable.rowCount()):
            textItem = self.capturedWordsTable.item(rowIndex, 0).text()
            startTimeItem = self.capturedWordsTable.item(rowIndex, 1).text()
            endTimeItem = self.capturedWordsTable.item(rowIndex, 2).text()
            
            if textItem != "" and startTimeItem != "" and endTimeItem != "":
                create_sub_clip_and_audio(textItem, self.rootOfTaggedDataDir, self.videoFullPath, self.tmpLipsIsolatedVideo, int(startTimeItem)/1000, int(endTimeItem)/1000)        

def create_sub_clip_and_audio(wantedlabel, taggedDataRootDirPath, srcVideoPath, isolatedLipsVideoPath, msStartTime, msEndTime):
    if not os.path.isdir(taggedDataRootDirPath):
        return
    
    wantedDirPath = os.path.join(taggedDataRootDirPath, wantedlabel)
    
    #Because moviepy can't handle UTF-8  
    tmpDirpath = os.path.join(taggedDataRootDirPath, 'tmp')
    os.mkdir(tmpDirpath)

    while (True):
        randomFileName = get_random_string(10)
        videoFullPath = os.path.join(tmpDirpath, randomFileName + '.avi')
        audioFullPath = os.path.join(tmpDirpath, randomFileName + '.wav')
        if (not os.path.isfile(videoFullPath)) and (not os.path.isfile(audioFullPath)):
            break
    #Create video clip
    ffmpeg_extract_subclip(isolatedLipsVideoPath, msStartTime, msEndTime, os.path.join(tmpDirpath, randomFileName + '.avi'))
    
    #create audio clip
    clipWithAudio = VideoFileClip(srcVideoPath).subclip(msStartTime, msEndTime)
    audioOnly = clipWithAudio.audio
    audioOnly.write_audiofile(os.path.join(tmpDirpath, randomFileName + '.wav'))

    if os.path.isdir(wantedDirPath): #if wantedDirPath already exist - copy files into it
        copyfile(os.path.join(tmpDirpath, randomFileName + '.avi'), os.path.join(wantedDirPath, randomFileName + '.avi'))
        copyfile(os.path.join(tmpDirpath, randomFileName + '.wav'), os.path.join(wantedDirPath, randomFileName + '.wav'))
        
        #remove temp files
        os.remove(os.path.join(tmpDirpath, randomFileName + '.avi'))
        os.remove(os.path.join(tmpDirpath, randomFileName + '.wav'))
        os.rmdir(tmpDirpath)
    else: #create wantedDirPath with video and audio files
        os.rename(tmpDirpath, wantedDirPath)

#extractLipsFromVideo returns 0 if worked as expected, otherwise - 1.
#It create the file 'extractedLips.avi'
def isolateLipsFromVideo(srcFilePath, dstFilePath):
    #Init face detector
    detector = dlib.get_frontal_face_detector()

    #Init face's landmark predicator
    predictor = dlib.shape_predictor("./videoProcessing/shape_predictor_68_face_landmarks.dat")

    #Get video file as input
    videoSrc = cv2.VideoCapture(srcFilePath)
    if (videoSrc.isOpened() == False): #Could not open video source file
        return 1

    minX, minY = 100000, 100000
    maxX, maxY = -100000, -100000
    lipsMargin = 15 #pixels
    srcVideoFPS = 0

    while videoSrc.isOpened():
        #Read next frame
        _, frame = videoSrc.read()

        #Save source video frame rate
        srcVideoFPS = videoSrc.get(cv2.CAP_PROP_FPS)

        #Grayscale original image
        grayImg = cv2.cvtColor(src=frame, code=cv2.COLOR_BGR2GRAY)

        #Run face detector on grayscaled image in order to get an array of found faces in that image
        faces = detector(grayImg)

        #Although it's supported, should handle only one face in each frame for now
        for face in faces:
            #Find landmarks of this face
            landmarks = predictor(image=grayImg, box=face)

            xList, yList = [], []

            #Iterate over lips's landmarks only and draw each one of them on current frame
            for n in range(48, 60):
                x = landmarks.part(n).x
                y = landmarks.part(n).y

                xList.append(x)
                yList.append(y)

            #get face current frame vertical and horizontal edges 
            if min(yList) < minY:
                minY = min(yList)
            if max(yList) > maxY:
                maxY = max(yList)
            if min(xList) < minX:
                minX = min(xList)
            if max(xList) > maxX:
                maxX = max(xList)

        #Release video input object
        videoSrc.release()
    
    #Now, we'll write the new video with extracted lips into an 'AVI' video format file
    frameWidth = maxX - minX + (2*lipsMargin)
    frameHeight = maxY - minY + (2*lipsMargin)
    outputVideo = cv2.VideoWriter(dstFilePath, cv2.VideoWriter_fourcc('M','J','P','G'), srcVideoFPS, (frameWidth,frameHeight))

    #reopen video source file
    videoSrc = cv2.VideoCapture(srcFilePath)
    if (videoSrc.isOpened() == False): #Could not open video source file
        return 1

    while(True):
        ret, frame = videoSrc.read()

        if ret == True:
            #Grayscale original image
            grayImg = cv2.cvtColor(src=frame, code=cv2.COLOR_BGR2GRAY)

            #Run face detector on grayscaled image in order to get an array of found faces in that image
            faces = detector(grayImg)

            #Although it's supported, should handle only one face in each frame for now
            for face in faces:
                #Find landmarks of this face
                landmarks = predictor(image=grayImg, box=face)

                minX, minY = 10000, 10000 

                #Iterate over lips's landmarks only and draw each one of them on current frame
                for n in range(48, 60):
                    x = landmarks.part(n).x
                    y = landmarks.part(n).y

                    if x < minX:
                        minX = x
                    if y < minY:
                        minY = y

                #extracting region of interest from original frame
                roiFrame = frame[minY-lipsMargin:minY+frameHeight-lipsMargin, minX-lipsMargin:minX+frameWidth-lipsMargin]
                outputVideo.write(roiFrame)
        else:
            #Release video input and output files
            videoSrc.release()
            outputVideo.release()
            break

    #iterate over tagged words table and create clips for each one
    return 0 #valid exit

def get_random_string(length):
    letters = string.ascii_lowercase
    return (''.join(random.choice(letters) for i in range(length)))

######## Main ########
app = QApplication(sys.argv)
window = VideoSubtitleWindow()
sys.exit(app.exec_())