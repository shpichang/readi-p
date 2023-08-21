# ---------------- MISC -----------------
# ---------------------------------------
from __future__ import division
from psychopy import core, visual, sound, event, gui, monitors  # parallel
from math import sin, cos, radians, sqrt
from numpy import average
from random import shuffle, randint, uniform

import pyxid2 # for Stimtracker to send the trigger signal
import time
import os
import csv
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
# Keys to identify what block condition to run
condition_keys = ["Finger_press", "Finger_lift", "Palm_press", "Palm_lift"]

# Number of times each block will occur
blockRepetitions = 3
# Keys to identify what block condition to run in training
trainingCondition_keys = ["Finger_press", "Finger_lift", "Palm_press", "Palm_lift"]
# Number of times each block will run in training
trainingBlockRepetitions = 1


trainingTrials = 3 # Number of training-trials per condition
BlockTrials = 25  # Number of trials per block condition
counter = 0  # Keep track of experiment progress

# Time control options
# [earliest, latest] duration of dot, after last event (in frames)/ How long the red dot will disappear
dotDelay = [0, 0]
holdtime = 4 # seconds
# mandatory interval break between blocks. units in seconds. 60 = 1 minute interval break between blocks
blockbreak = 60
# Interstimulus Interval (units in seconds. [min, max] )
interstim = [4, 8]


# Display options
monDistance = 60  # Distance from subject eyes to monitor (in cm)
monWidth = 30  # Width of monitor display (in cm)
textSize = 0.85  # Size of text in degrees
circleRadius = 2  # Radius of circle (in degrees)
fixationSize = sqrt(circleRadius) * 0.5  # size of fixation point "+"
dotSize = circleRadius / 5  # Size of dot (in degrees)
libetTime = 2.56  # Rotation speed of dot
tics = 12  # Number of tics on circle
stics = 60  # Number of small tics on circle

# Approximations
msScale = 1000
degScale = 10

# Questions, responses and primes
conditionTypes = {
    "Finger_press": {
        "ansKey": ["left"],
        "eegLine": 11,
        "trialstart": 10,
        "instruction": "Wait for the dot to make one full cycle\n\nThen press the button according to the image.\nPress the button to start.",
        "instru_img": "Finger_press.png",
        "question": 'Where was the dot when you first experienced the intention to press the keypad? \n Use the "A" and "D" keys to move the dot and press the "space bar" from the keyboard to select.',
    },
    "Finger_lift": {
        "ansKey": ["up"],
        "eegLine": 21,
        "trialstart": 20,
        "instruction": "Wait for the dot to make one full cycle\n\nThen press the button according to the image.\nPress the button to start.",
        "instru_img": "Finger_lift.png",
        "question": 'Where was the dot when you first experienced the intention to press the keypad? \n Use the "A" and "D" keys to move the dot and press the "space bar" from the keyboard to select.',
    },
    "Palm_press": {
        "ansKey": ["down"],
        "eegLine": 31,
        "trialstart": 30,
        "instruction": "Wait for the dot to make one full cycle\n\nThen press the button according to the image.\nPress the button to start.",
        "instru_img": "Palm_press.png",
        "question": 'Where was the dot when you first experienced the intention to press the keypad? \n Use the "A" and "D" keys to move the dot and press the "space bar" from the keyboard to select.',
    },
    "Palm_lift": {
        "ansKey": ["right"],
        "eegLine": 41,
        "trialstart": 40,
        "instruction": "Wait for the dot to make one full cycle\n\nThen press the button according to the image.\nPress the button to start.",
        "instru_img": "Palm_lift.png",
        "question": 'Where was the dot when you first experienced the intention to press the keypad? \n Use the "A" and "D" keys to move the dot and press the "space bar" from the keyboard to select.',
    },
}

moveKeys = {
    "a": -3,
    "w": 1,
    "s": -1,
    "d": 3,
    "left": -3,
    "up": 1,
    "down": -1,
    "right": 3,
}

selectKey = ["space"]
timeOutKey = ["space"]
quitKeys = ["esc", "escape"]

# Data containers for each trial
dataCategories = [
    "id",
    "condition",
    "no",
    "dotDelay",
    "holdTime",
    "pressOnset",
    "pressAngle",
    "ansAngle",
    "wTime",
    "ansTime",
    "ISI",
    "timeOut",
    "timeOutOnset",
    "timeOutQuestion",
    "stopCharacter",
    "samplesToLastIdenticalCharacter",
    "userError",
    "response",
]
dataDict = dict(zip(dataCategories, ["" for i in dataCategories]))

# Set monitor variables
myMon = monitors.Monitor("testMonitor")
myMon.setDistance(monDistance)
myMon.setWidth(monWidth)

# Intro dialogue
dialogue = gui.Dlg()
dialogue.addField("subjectID")
dialogue.show()
if dialogue.OK:
    if dialogue.data[0].isdigit():
        subjectID = dialogue.data[0]
    else:
        print("SUBJECT ID SHOULD BE A DIGIT")
        core.quit()
else:
    core.quit()

# Make folder for data
saveFolder = "data"
if not os.path.isdir(saveFolder):
    os.makedirs(saveFolder)

# Clocks
trialClock = core.Clock()
soundClock = core.Clock()
TimeOutClock = core.Clock()


# -------------- STIMULI ----------------
# ---------------------------------------
win = visual.Window(
    monitor=myMon,
    size=myMon.getSizePix(),
    fullscr=False,
    allowGUI=False,
    color="white",
    units="deg",
)  # Change fullscreen here: " fullscr=True/False "
mainText = visual.TextStim(win=win, height=textSize, color="black")
questionText = visual.TextStim(
    win=win, pos=(0, circleRadius * 4), height=textSize, color="black", wrapWidth=50
)
clockDot = visual.PatchStim(win=win, mask="circle", color="red", tex=None, size=dotSize)
clockDotTimeOut = visual.PatchStim(
    win=win, mask="circle", color="#FF0000", tex=None, size=dotSize
)
instru_text = mainText = visual.TextStim(
    win=win, height=textSize, color="black", pos=(0, 4.0), wrapWidth=50
)
instru_img = visual.ImageStim(win=win, pos=(0, -150), size=[688, 322], units="pix")


# get actual frame rate to ensure smooth rotation.
def getActualFrameRate():
    # get the actual frame rate
    frameDur = []
    for frameN in range(100):
        frameDur.append(win.monitorFramePeriod)
    actualFrameRate = 1.0 / average(frameDur)
    return actualFrameRate


actual_frame_rate = getActualFrameRate()
# Degrees shift per monitor-frame: 360/LibetTime/framerate
dotStep = 360 / libetTime / actual_frame_rate

# Make complex figure: circle + tics + fixation cross. Render and save as single stimulus "circle"
visual.Circle(win, radius=circleRadius, edges=512, lineWidth=3, lineColor="none").draw()
for angleDeg in range(0, 360, int(360 / tics)):
    angleRad = radians(angleDeg)
    begin = [circleRadius * sin(angleRad), circleRadius * cos(angleRad)]
    end = [begin[0] * 1.2, begin[1] * 1.2]
    visual.Line(
        win,
        start=(begin[0], begin[1]),
        end=(end[0], end[1]),
        lineColor="black",
        lineWidth=2.4,
    ).draw()

for angleDeg in range(0, 360, int(360 / stics)):
    angleRad = radians(angleDeg)
    begin = [circleRadius * 1.08 * sin(angleRad), circleRadius * 1.08 * cos(angleRad)]
    end = [begin[0] * 1.1, begin[1] * 1.1]
    visual.Line(
        win,
        start=(begin[0], begin[1]),
        end=(end[0], end[1]),
        lineColor="black",
        lineWidth=1,
    ).draw()

# Buffer it all in "circle" object
circle = visual.BufferImageStim(win)
win.clearBuffer()

# interstimulus interval
cross_ISI = visual.TextStim(
    win=win,
    name="cross_ISI",
    text="+",
    font="Arial",
    pos=(0, 0),
    height=2,
    wrapWidth=None,
    ori=0.0,
    color="black",
    colorSpace="rgb",
    opacity=None,
    languageStyle="LTR",
    depth=-1.0,
)

# ------------- FUNCTIONS ---------------


def makeBlock(condition, training):
    if training == True:
        # Set number of training repetitions
        conditionRep = trainingTrials
    else:
        # Set number of repetitions
        conditionRep = BlockTrials

    # Make a trialList with trialsPerPrime of each prime
    tmpTrials = [dict(dataDict.items()) for rep in range(conditionRep)]
    shuffle(tmpTrials)

    # Update every trial with trial-specific info
    trialList = [""] * conditionRep
    for trialNo in range(len(tmpTrials)):
        trialList[trialNo] = dict(tmpTrials[trialNo].items())
        trialList[trialNo]["no"] = trialNo + 1
        trialList[trialNo]["id"] = subjectID
        trialList[trialNo]["condition"] = condition
        trialList[trialNo]["dotDelay"] = randint(dotDelay[0], dotDelay[1])

    return trialList


# Draw a dot on the circle, given an angle
def drawDot(angleDeg, timeOut):
    if timeOut == False:
        angleRad = radians(angleDeg)
        x = circleRadius * sin(angleRad)
        y = circleRadius * cos(angleRad)
        clockDot.setPos([x, y])
        clockDot.draw()
    else:
        angleRad = radians(angleDeg)
        x = circleRadius * sin(angleRad)
        y = circleRadius * cos(angleRad)
        clockDotTimeOut.setPos([x, y])
        clockDotTimeOut.draw()


# Run a block of trials and save results
def runBlock(condition, training):
    if condition == "-":
        global counter
        counter += 1
        # interval break between blocks
        visual.TextStim(
            win,
            text="You have completed {} block, {} more to go! \n\nTake a break".format(
                counter, len(conditions) - counter
            ),
            color="black",
            height=fixationSize,
            antialias=False,
        ).draw()
        win.flip()
        time.sleep(blockbreak)  # number of seconds
        visual.TextStim(
            win,
            text="Are you ready to start a new block? \n\nPress the spacebar if you are ready to begin the next block.",
            color="black",
            pos=(0, 4.0),
            wrapWidth=50,
            height=textSize,
            antialias=False,
        ).draw()
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

        # Trigger codes to send to parallel port
        leftTrigger = 1
        rightTrigger = 2
        startTrigger = 64

        # Set up .csv save function
        if not training:
            saveFile = (
                saveFolder + "/libetrandom_" + str(subjectID) + "_" + condition + ".csv"
            )  # Filename for save-data
            # The writer function to csv
            csvWriter = csv.writer(
                open(saveFile, "w", newline=""), delimiter=","
            ).writerow
            # Writes title-row in csv
            csvWriter(dataCategories)

        # Show instruction
        instru_img.setImage(conditionTypes[conid]["instru_img"])
        instru_img.draw()
        instru_text.setText(conditionTypes[conid]["instruction"])
        instru_text.draw()
        win.flip()
        event.waitKeys(keyList=conditionTypes[conid]["ansKey"])

        # Loop through trials
        for trial in trialList:
            # Prepare each trial
            if training:
                # Show "TRAINING" instead of prime in training condition
                mainText.setText("TRAINING")

            cross_ISI.draw()
            win.flip()
            interstimTime = randint(
                interstim[0], interstim[1]
            )  # Interstimulus interval
            time.sleep(interstimTime)
            # Set text of question
            questionText.setText(conditionTypes[conid]["question"])
            # Angle of dot in degrees
            dotAngle = uniform(0, 360)
            # When not 0, indicates that the last event has occurred and the number of frames since that event
            dotDelayFrames = 0

            # Show rotating dot and handle events
            event.clearEvents()
            trialClock.reset()
            TimeOutClock.reset()
            timeOutLogic = False
            trialCounter = trialCounter + 1

            # Send start trigger
            #       trigger(startTrigger)                   # COMMENT !!!
            print(startTrigger)
            try:
                dev.activate_line(bitmask=conditionTypes[conid]["trialstart"])
            except NameError:
                pass
            while True:
                dotAngle += dotStep
                if dotAngle > 360:
                    dotAngle -= 360
                circle.draw()
                visual.TextStim(
                    win, text="+", color="black", height=fixationSize, antialias=False
                ).draw()
                drawDot(dotAngle, timeOutLogic)
                win.flip()

                # Record press
                # condition in [']:
                if conid in condition_keys:
                    # Log event
                    response = event.getKeys(
                        keyList=conditionTypes[conid]["ansKey"] + quitKeys,
                        timeStamped=trialClock,
                    )
                    # Only react on first response to this trial
                    if len(response) and not trial["pressOnset"]:
                        if response[-1][0] in quitKeys:
                            core.quit()
                        try:
                            if response[-1][0] in conditionTypes[conid]["ansKey"]:
                                try:
                                    dev.activate_line(
                                        bitmask=conditionTypes[conid]["eegLine"]
                                    )
                                except NameError:
                                    pass
                        except NameError:
                            pass
                        trial["pressOnset"] = int((response[-1][1]) * msScale) / msScale
                        trial["pressAngle"] = int((dotAngle) * degScale) / degScale
                        trial["holdTime"] = int(holdtime)

                        # or 'singlePressTimeOut':
                        if conid in condition_keys:
                            dotDelayFrames = 1  # Mark as last event

                # The little time after last event, where the dot keeps rotating.
                if dotDelayFrames:
                    TimeOutClock.reset()

                    if dotDelayFrames > trial["dotDelay"]:
                        break
                    dotDelayFrames += 1

            # Subjects selects location of target event
            # dotAngle = uniform(0, 360)                #if you dont want dot to reappear at a random place, comment this line out

            # draws a blank clcok face to cover the location for the rotating clock dot briefly.
            circle.draw()
            visual.TextStim(
                win, text="+", color="black", height=fixationSize, antialias=False
            ).draw()
            win.flip()
            time.sleep(holdtime)
            trialClock.reset()

            while True:
                circle.draw()
                questionText.draw()
                visual.TextStim(
                    win, text="+", color="black", height=fixationSize, antialias=False
                ).draw()

                if trial["timeOut"] == "yes":
                    drawDot(dotAngle, True)
                else:
                    drawDot(dotAngle, False)
                win.flip()

                # Handle responses: quit, move or answer
                response = event.waitKeys(
                    keyList=list(moveKeys.keys()) + selectKey + quitKeys
                )
                if response[-1] in quitKeys:
                    core.quit()

                if response[-1] in moveKeys:
                    dotAngle += moveKeys[response[-1]]
                    if dotAngle > 360:
                        dotAngle = dotAngle - 360
                    if dotAngle < 0:
                        dotAngle = 360 + dotAngle
                if response[-1] in selectKey:
                    trial["ansTime"] = int((trialClock.getTime()) * msScale) / msScale
                    trial["ansAngle"] = int((dotAngle) * degScale) / degScale
                    trial["ISI"] = int(interstimTime)
                    trial["wTime"] = min((trial["pressAngle"] - trial["ansAngle"]), 360-(trial["pressAngle"] - trial["ansAngle"]))* (
                        libetTime / 360
                    )
                    break

            # End of trial: save by appending data to csv. If training: stop after training trials
            if not training:
                csvWriter([trial[category] for category in dataCategories])
            else:
                if trial["no"] >= trainingTrials:
                    return


def trainingIsOver():
    # !!!!!! Set text
    questionText.setText(
        "Training is over \n\nPress with your index finger when you are ready to start the actual experiment..."
    )
    questionText.draw()
    win.flip()
    event.waitKeys()


def ThankYou():
    # !!!!!! Set text
    questionText.setText("The experiment is over. \n\nThank You... :)")
    questionText.draw()
    win.flip()
    event.waitKeys()  # event.waitKeys(ansKeys)


# ---------- RUN EXPERIMENT -------------
# ---------------------------------------
# Make random order of conditions and run experiment
conditions = [x + str(y + 1) for x in condition_keys for y in range(blockRepetitions)]
shuffle(conditions)
conditions_new = []
for i in conditions:
    conditions_new.append(i)
    conditions_new.append("-")  # adding "-" to identify if blockbreak is needed
conditions_new.pop()
print(conditions)
conditionsT = [
    x + str(y + 1)
    for x in trainingCondition_keys
    for y in range(trainingBlockRepetitions)
]
print(conditionsT)

# Run experiment
for condition in conditionsT:
    runBlock(condition, training=True)
trainingIsOver()
for condition in conditions_new:
    runBlock(condition, training=False)
ThankYou()
core.quit()
