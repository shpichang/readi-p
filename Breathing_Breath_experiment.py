
# ---------------- MISC -----------------
# ---------------------------------------
from __future__ import division
from psychopy import core, visual, sound, event, gui, monitors  # parallel
from math import sin, cos, radians, sqrt
from numpy import average
from random import shuffle, randint, uniform
from psychopy.visual import MovieStim
import numpy as np
import pyxid2 # import pyxid2 for Stimtracker to send the trigger signal
import time
import os
import csv
import glob
import datetime
import serial

# --------get a list of all attached XID devices------
devices = pyxid2.get_xid_devices()
if devices:
    print(devices)
else:
    print("No XID devices detected")
#    exit()

try:
    dev = devices[0]
    dev.reset_base_timer()
    dev.reset_rt_timer()
except IndexError:
    pass

# ---------------- VARS -----------------
# -----------------------------------------
# Trial and data options
# Keys to identify what type of block to run
condition_keys = ['Normal_breath', 'Breath_hold', 'Breath_in', 'Breath_out']

# Number of times each block will occur
blockRepetitions = 2
# Keys to identify what type of block to run in training
trainingCondition_keys = ['Normal_breath',
                          'Breath_hold', 'Breath_in', 'Breath_out']
# Number of times each block will occur in training
trainingBlockRepetitions = 1

# Number of initial training-trials per block
trainingTrials = 3 # Number of trials per block
BlockTrials = 25  # Number of trials per block
counter = 0 # Counter for number of trials. Always starts at 0

# Time control options
# [earliest, latest] duration of dot, after last event (in frames)/ How long the green dot will disappear
dotDelay = [0, 0]
holdtime = 4
# interval break between blocks
blockbreak = 5
# Interstimulus Interval (4 to 8 seconds)
interstim = [4, 8]

# Display options
monDistance = 70            # Distance from subject eyes to monitor (in cm)
monWidth = 30               # Width of monitor display (in cm)
textSize = 0.85              # Size of text in degrees
circleRadius = 2            # Radius of circle (in degrees)
fixationSize = sqrt(circleRadius)*0.5  # size of fixation point "+"
dotSize = circleRadius/5   # Size of dot (in degrees)
libetTime = 10.24            # Rotation speed of dot
# Degrees shift per monitor-frame: 360/LibetTime/framerate
tics = 12                   # Number of tics on circle
stics = 60                  # Number of small tics on circle

# Approximations
msScale = 1000
degScale = 10

# Questions, responses and primes
conditionTypes = {
    'Normal_breath': {
        "ansKey": ["left"],
        "trialstart": 10,
        "eegLine": 11,
        "instruction": "Wait for the dot to rotate a quarter of a cycle.\n\nPress the left key while breathing normally anytime before the dot makes a full rotation.\n\nPress the left key to start.",
        "instru_img": "Normal_breath.png",
        "question": 'Where was the green dot when you first experienced the intention to press the key? \n Use the arrow keys to move the dot and press the "spacebar" to select.',
    },
    'Breath_hold': {
        "ansKey": ["left"],
        "trialstart": 20,
        "eegLine": 21,
        "instruction": "Wait for the dot to rotate a quarter of a cycle.\n\nPress the left key according to the pictures anytime before the dot makes a full rotation.\n\nPress the left key to start.",
        "instru_img": "Hold_instructions_01.mp4",
        "question": 'Where was the green dot when you first experienced the intention to press the key? \n Use the arrow keys to move the dot and press the "spacebar" to select.',
        "preparation": {
            "get ready": {
                "text": "●",
                "color": "black",
                "duration": 3,
            },
        }
    },
    'Breath_out': {
        "ansKey": ["left"],
        "trialstart": 30,
        "eegLine": 31,
        "instruction": "Wait for the dot to rotate a quarter of a cycle.\n\nPress the left key according to the pictures anytime before the dot makes a full rotation.\n\nPress the left key to start.",
        "instru_img": "Breathe_out_01.mp4",
        "question": 'Where was the green dot when you first experienced the intention to press the key? \n Use the arrow keys to move the dot and press the "spacebar" to select.'
    },
    'Breath_in': {
        "ansKey": ["left"],
        "trialstart": 40,
        "eegLine": 41,
        "instruction": "Wait for the dot to rotate a quarter of a cycle.\n\nPress the left key according to the pictures anytime before the dot makes a full rotation.\n\nPress the left key to start.",
        "instru_img": "Breathe-in_01.mp4",
        "question": 'Where was the green dot when you first experienced the intention to press the key? \n Use the arrow keys to move the dot and press the "spacebar" to select.',
    },
}

moveKeys = {
    'a': -3,
    'w': 1,
    's': -1,
    'd': 3,
    'left': -3,
    'up': 1,
    'down': -1,
    'right': 3
}

leftKeys = ['d']
rightKeys = ['k']
# ansKeys = ['left']
selectKey = ['space']
timeOutKey = ['space']
quitKeys = ['esc', 'escape']

# Data containers for each trial
dataCategories = ['id', 'condition', 'no', 'dotDelay', 'holdTime', 'pressOnset', 'pressAngle', 'ansAngle', 'ansTime', 'ISI',
                  'timeOut', 'timeOutOnset', 'timeOutQuestion', 'stopCharacter', 'samplesToLastIdenticalCharacter', 'userError', 'response']
dataDict = dict(zip(dataCategories, ['' for i in dataCategories]))

# Set monitor variables
myMon = monitors.Monitor('testMonitor')
myMon.setDistance(monDistance)
myMon.setWidth(monWidth)

# Intro dialogue
dialogue = gui.Dlg()
dialogue.addField('subjectID')
dialogue.show()
if dialogue.OK:
    if dialogue.data[0].isdigit():
        subjectID = dialogue.data[0]
    else:
        print('SUBJECT SHOULD BE DIGIT')
        core.quit()
else:
    core.quit()

# Make folder for data
saveFolder = 'data'
if not os.path.isdir(saveFolder):
    os.makedirs(saveFolder)

# Clocks
trialClock = core.Clock()
# letterClock = core.Clock()
soundClock = core.Clock()
TimeOutClock = core.Clock()


# -------------- STIMULI ----------------
# ---------------------------------------
win = visual.Window(monitor=myMon, size=(1980, 1080 ) , fullscr=False, allowGUI=True, color='white',
                    units='deg')
#size=myMon.getSizePix()
mainText = visual.TextStim(win=win, height=textSize, color='black')
questionText = visual.TextStim(win=win, pos=(
    0, circleRadius*4), height=textSize, color='black', wrapWidth=50)
clockDot = visual.PatchStim(win=win, mask="circle",
                            color='green', tex=None, size=dotSize)
clockDot2 = visual.PatchStim(
    win=win, mask="circle", color='green', tex=None, size=dotSize)
instru_text = mainText = visual.TextStim(
    win=win, height=textSize, color='black', pos=(0, 6.0), wrapWidth=50)

# Make complex figure: circle + tics + fixation cross. Render and save as single stimulus "circle"
visual.Circle(win, radius=circleRadius, edges=512,
              lineWidth=3, lineColor='none').draw()
for angleDeg in range(0, 360, int(360/tics)):
    angleRad = radians(angleDeg)
    begin = [circleRadius*sin(angleRad), circleRadius*cos(angleRad)]
    end = [begin[0]*1.2, begin[1]*1.2]
    visual.Line(win, start=(begin[0], begin[1]), end=(
        end[0], end[1]), lineColor='black', lineWidth=2.4).draw()

for angleDeg in range(0, 360, int(360/stics)):
    angleRad = radians(angleDeg)
    begin = [circleRadius*1.08*sin(angleRad), circleRadius*1.08*cos(angleRad)]
    end = [begin[0]*1.1, begin[1]*1.1]
    visual.Line(win, start=(begin[0], begin[1]), end=(
        end[0], end[1]), lineColor='black', lineWidth=1).draw()

# Buffer it all in "circle" object
circle = visual.BufferImageStim(win)
win.clearBuffer()

# interstimulus interval
cross_ISI = visual.TextStim(win=win, name='cross_ISI',
                            text='+',
                            font='Arial',
                            pos=(0, 0), height=2, wrapWidth=None, ori=0.0,
                            color='black', colorSpace='rgb', opacity=None,
                            languageStyle='LTR',
                            depth=-1.0)

# ------------- FUNCTIONS ---------------


def getActualFrameRate():
    # get the actual frame rate
    frameDur = []
    for frameN in range(100):
        frameDur.append(win.monitorFramePeriod)
    actualFrameRate = 1.0/average(frameDur)
    return actualFrameRate


actual_frame_rate = getActualFrameRate()
dotStep = 360/libetTime/actual_frame_rate


def makeBlock(condition, training):
    if training == True:
        # Set number of training repetitions?
        conditionRep = trainingTrials
    else:
        # Set number of repetitions?
        conditionRep = BlockTrials

    # Make a trialList with trialsPerPrime of each prime
    tmpTrials = [dict(dataDict.items()) for rep in range(conditionRep)]
    shuffle(tmpTrials)

    # Update every trial with trial-specific info
    trialList = ['']*conditionRep
    for trialNo in range(len(tmpTrials)):
        trialList[trialNo] = dict(tmpTrials[trialNo].items())
        trialList[trialNo]['no'] = trialNo+1
        trialList[trialNo]['id'] = subjectID
        trialList[trialNo]['condition'] = condition
        trialList[trialNo]['dotDelay'] = randint(dotDelay[0], dotDelay[1])

    return trialList


# Draws a dot on the circle, given an angle
def drawDot(angleDeg, timeOut):
    if timeOut == False:
        angleRad = radians(angleDeg)
        x = circleRadius*sin(angleRad)
        y = circleRadius*cos(angleRad)
        clockDot.setPos([x, y])
        clockDot.draw()
    else:
        angleRad = radians(angleDeg)
        x = circleRadius*sin(angleRad)
        y = circleRadius*cos(angleRad)
        clockDot2.setPos([x, y])
        clockDot2.draw()


def drawDot2(angleDeg, timeOut):
    if timeOut == False:
        angleRad = radians(angleDeg)
        x = circleRadius*sin(angleRad)
        y = circleRadius*cos(angleRad)
        clockDot2.setPos([x, y])
        clockDot2.draw()


# Run a block of trials and save results


def runBlock(condition, training, letterMode):

    if condition == '-':
        global counter
        counter += 1
        # 2-min break screen
        visual.TextStim(win, text='You have completed {} block, {} more to go! \n\nTake a break'.format(counter, len(conditions)-counter), color='black',
                        height=fixationSize, antialias=False).draw()
        win.flip()
        time.sleep(blockbreak)  # number of seconds
        visual.TextStim(win, text='Break is over. Press the "spacebar" if you are ready to begin the new block.', color='black',
                        height=fixationSize, antialias=False).draw()
        win.flip()
        event.waitKeys(keyList=selectKey)
    else:
        trialList = makeBlock(condition, training)

        # assign conid
        for item in condition_keys:
            if item in condition:
                conid = item
                break

        # Add more if needed...
        # Time out
        timeOutLogic = False
        timeOutCounter = 0
        timeOutListCounter = 0
        timeOutMeanListAverage = 1
        trialCounter = 0
        timeOutScale = 1

        # Remove unwanted categories from final CSV file
        unwanted_categories = ['timeOut', 'timeOutOnset', 'timeOutQuestion', 'stopCharacter',
                               'samplesToLastIdenticalCharacter', 'userError', 'response']
        dataCategories_filtered = [category for category in dataCategories if category not in unwanted_categories]

        # Set up .csv save function
        if not training:
            saveFile = saveFolder+'/slowlibet_' + \
                str(subjectID)+'_'+condition + \
                '.csv'          # Filename for save-data
            # The writer function to csv
            csvWriter = csv.writer(
                open(saveFile, 'w', newline=''), delimiter=',').writerow
            # Writes title-row in csv
            csvWriter(dataCategories_filtered)

        if conditionTypes[conid]["instru_img"] == "Normal_breath.png":
            instru_img = visual.ImageStim(win=win, pos=(0, -150), size=[
                 700, 400], units="pix") #1283, 493
        else:
            video_stim = visual.MovieStim3(win, conditionTypes[conid]["instru_img"], pos=(0, -160),
                                           size=(700, 493), flipVert=False, flipHoriz=False, loop=True)
            # instru_img = visual.ImageStim(win=win, pos=(0, -150), size=[
            #     700, 400], units="pix")

        # Show instruction
        if conditionTypes[conid]["instru_img"] == "Normal_breath.png":
            instru_img.setImage(conditionTypes[conid]["instru_img"])
            instru_img.draw()
            instru_text.setText(conditionTypes[conid]["instruction"])
            instru_text.draw()
            win.flip()
            event.waitKeys(keyList=conditionTypes[conid]["ansKey"])
        else:
            instru_text.setText(conditionTypes[conid]["instruction"])
            instru_text.draw()
            video_stim.play()
            win.flip()
            # Start loop to continuously update video frames
            while video_stim.status != visual.FINISHED:
                instru_text.draw()
                video_stim.draw()
                win.flip()
                # check for response and exit loop if ansKey is pressed
                if event.getKeys(keyList=conditionTypes[conid]["ansKey"]):
                    break
            video_stim.stop()
            video_stim.seek(0.0)

        # Interstimulus interval (4 to 8 seconds)

        # Loop through trials
        for trial in trialList:
            # Prepare each trial
            if training:
                # Show "TRAINING" instead of prime in training condition
                mainText.setText('TRAINING')
            # ISI (0.5 to 1.5 seconds)
            cross_ISI.draw()
            win.flip()
            interstimTime = randint(interstim[0], interstim[1])
            time.sleep(interstimTime)

            if 'Breath_hold' in condition:
                # Show the preparation instruction
                prepare_instruction1 = visual.TextStim(win, height= 2,
                                                       font='Arial',
                                                       pos=(0, 0), wrapWidth=None, ori=0.0,
                                                       colorSpace='rgb', opacity=None,
                                                       languageStyle='LTR',
                                                       depth=-1.0,
                                                       text=conditionTypes[conid]["preparation"]["get ready"]["text"],
                                                       color=conditionTypes[conid]["preparation"]["get ready"]["color"])
                prepare_instruction1.draw()
                win.flip()
                core.wait(conditionTypes[conid]["preparation"]["get ready"]["duration"])

            # Set text of question
            questionText.setText(conditionTypes[conid]["question"])
            # Angle of dot in degrees
            initAngle = dotAngle = uniform(0, 360)
            accumDotStep = 0
            # marking starting line
            angleRadM = radians(initAngle)
            beginM = [0, 0]
            endM = [circleRadius*1.08 *
                    sin(angleRadM), circleRadius*1.08*cos(angleRadM)]
            # marking second starting line
            angleRadM2 = radians(initAngle + 90)
            endM2 = [circleRadius * 1.08 * sin(angleRadM2), circleRadius * 1.08 * cos(angleRadM2)]
            # marking second starting line for drawDot2

            # When not 0, indicates that the last event has occurred and the number of frames since that event
            dotDelayFrames = 0

            # Show rotating dot and handle events
            event.clearEvents()
            trialClock.reset()
    #        letterClock.reset()
            TimeOutClock.reset()
            timeOutLogic = False
            trialCounter = trialCounter + 1

            try:
                dev.activate_line(
                    bitmask=conditionTypes[conid]["trialstart"])
            except NameError:
                pass
            isStop = False
            isExperimentDone = False
            while not isExperimentDone:
                while True:
                    if dotAngle >= initAngle and isStop:
                        visual.TextStim(win, text='YOU MISSED! \n\n Press the button before the end of a full rotation. \n\n Press "space" to redo the trial', color='black',
                                        height=fixationSize, antialias=False).draw()
                        win.flip()
                        event.waitKeys(keyList=selectKey)
                        isStop = False
                        accumDotStep = 0
                        # if restarting the trail also re-randomize dot starting location
                        # initAngle = dotAngle = uniform(0, 360)
                        break
                    else:
                        dotAngle += dotStep
                        accumDotStep += dotStep
                        if dotAngle > 360:
                            dotAngle -= 360
                            isStop = True

#                        if dotAngle < initAngle + 90 and dotAngle >= initAngle:
                        if accumDotStep <= 90:
                            circle.draw()
                            visual.TextStim(win, text='+', color='black',
                                            height=fixationSize, antialias=False).draw()

                            # marking starting line
                            visual.Line(win, start=(beginM[0], beginM[1]), end=(
                                endM[0], endM[1]), lineColor=(0, 0, 0, 0.5), lineWidth=2).draw()
                            # marking starting line of second dot or 1/4 of rotation
                            visual.Line(win, start=(beginM[0], beginM[1]), end=(endM2[0], endM2[1]),
                                        lineColor=(0, 0, 0, 0.5), lineWidth=2).draw()

                            drawDot(dotAngle, timeOutLogic)
                            win.flip()
                            event.clearEvents()
                        else:
                            circle.draw()
                            visual.TextStim(win, text='+', color='black',
                                            height=fixationSize, antialias=False).draw()
                            # marking starting line

                            visual.Line(win, start=(beginM[0], beginM[1]), end=(
                                endM[0], endM[1]), lineColor=(0, 0, 0, 0.5), lineWidth=2).draw()
                            visual.Line(win, start=(beginM[0], beginM[1]), end=(endM2[0], endM2[1]),
                                        lineColor=(0, 0, 0, 0.5), lineWidth=2).draw()

                            drawDot2(dotAngle, timeOutLogic)
                            win.flip()

                            # Record press
                            # condition in [']:
                            if conid in condition_keys:

                                # Log event
                                response = event.getKeys(
                                    keyList=conditionTypes[conid]["ansKey"]+quitKeys, timeStamped=trialClock)
                                # Only react on first response to this trial
                                if len(response) and not trial['pressOnset']:
                                    if response[-1][0] in quitKeys:
                                        core.quit()
                                    try:
                                        if response[-1][0] in conditionTypes[conid]["ansKey"]:
                                            try:
                                                dev.activate_line(
                                                    bitmask=conditionTypes[conid]["eegLine"])
                                            except NameError:
                                                pass
                                    except NameError:
                                        pass
                                    trial['pressOnset'] = int(
                                        (response[-1][1])*msScale)/msScale
                                    trial['pressAngle'] = int(
                                        (dotAngle)*degScale)/degScale
                                    trial['holdTime'] = int(holdtime)


                                    # or 'singlePressTimeOut':
                                    if conid in condition_keys:
                                        dotDelayFrames = 1   # Mark as last event
                                        isExperimentDone = True

                            # The little time after last event, where the dot keeps rotating.
                            if dotDelayFrames:
                                TimeOutClock.reset()

                                if dotDelayFrames > trial['dotDelay']:
                                    break
                                dotDelayFrames += 1

            # Subjects selects location of target event
            # dotAngle = uniform(0, 360)                #if you dont want dot to reappear at a random place, comment this line out
            # trialClock.reset()                        # move this to after time.sleep(holdtime) to keep the ansTime from adding sleeptime

            # draws a blank clcok face to cover the location for the rotating clock dot briefly.
            circle.draw()
            visual.TextStim(win, text='+', color='black',
                            height=fixationSize, antialias=False).draw()
            win.flip()
            time.sleep(holdtime)
            trialClock.reset()

            while True:
                circle.draw()
                questionText.draw()
                visual.TextStim(win, text='+', color='black',
                                height=fixationSize, antialias=False).draw()

                if trial['timeOut'] == 'yes':
                    drawDot2(dotAngle, True)
                else:
                    drawDot2(dotAngle, False)
                win.flip()

                # Handle responses: quit, move or answer
                # response = event.waitKeys(moveKeys.keys()+ansKeys+quitKeys)
                response = event.waitKeys(keyList=list(
                    moveKeys.keys())+selectKey+quitKeys)
                if response[-1] in quitKeys:
                    core.quit()

                if response[-1] in moveKeys:
                    dotAngle += moveKeys[response[-1]]
                    if dotAngle > 360:
                        dotAngle = dotAngle-360
                    if dotAngle < 0:
                        dotAngle = 360+dotAngle
                if response[-1] in selectKey:
                    trial['ansTime'] = int(
                        (trialClock.getTime())*msScale)/msScale
                    trial['ansAngle'] = int((dotAngle)*degScale)/degScale
                    trial['ISI'] = int(interstimTime)
                    break


    # End of trial: save by appending data to csv. If training: stop after trainingTrials trials
            if not training:
                csvWriter([trial[category] for category in dataCategories_filtered])
            else:
                if trial['no'] >= trainingTrials:
                    return


def trainingIsOver():
    # !!!!!! Set text
    questionText.setText(
        'Training is over \n\nPlease press your index finger when you are ready...')
    questionText.draw()
    win.flip()
    event.waitKeys()


def ThankYou():
    # !!!!!! Set text
    questionText.setText(
        'This part of the experiment is over now \n\nThank You... :)')
    questionText.draw()
    win.flip()
    event.waitKeys()  # event.waitKeys(ansKeys)


# ---------- RUN EXPERIMENT -------------
# ---------------------------------------
# Make random order of conditions and run experiment
conditions = [x + str(y+1)
              for x in condition_keys for y in range(blockRepetitions)]
shuffle(conditions)
conditions_new = []
for i in conditions:
    conditions_new.append(i)
    conditions_new.append('-')
conditions_new.pop()
print(conditions)
print(conditions_new)
conditionsT = [
    x + str(y+1) for x in trainingCondition_keys for y in range(trainingBlockRepetitions)]
print(conditionsT)
# Run the experiment
for condition in conditionsT:
    runBlock(condition, training=True, letterMode=False)
trainingIsOver()
for condition in conditions_new:
    runBlock(condition, training=False, letterMode=False)

ThankYou()
core.quit()
