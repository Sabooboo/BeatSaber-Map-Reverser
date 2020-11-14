import json
import os
import sys

from os import listdir
from os.path import isfile, join

import shutil
from shutil import copyfile

import tinytag
from tinytag import TinyTag as tt

# --- Fetch the directory of the map to reverse

mapDirectory = (input("Enter the directory of the map you want to reverse."))

# --- Create properties

difficultyList = []  # STR: List of song difficulty names, this includes the ".dat" at the end
songName = None  # STR: Name of the song file, including the .egg at the end
songLength = None  # NUM: Length of the song in seconds
songOffsets = []  # {STR, NUM}: Offsets for particular difficulties
songBPM = None  # NUM: BPM of the song, used for calculating note timings
imageName = None  # STR: Name of the image file used in the map, including the .jpg at the end
mapFolderName = None  # STR: The name of the folder of the map
mapFolderNameReverse = None  # STR: pam eht fo redlof eht fo eman ehT
filesMissing = []  # unused

# --- Make new directory

def findMapFolderName(direct):
    for name in direct.split("\\")[::-1]:
        if name != "":
            return (name, name[::-1])

mapFolderNames = findMapFolderName(mapDirectory)
mapFolderName = mapFolderNames[0]
mapFolderNameReverse = mapFolderNames[1]



newDirectory = os.path.join(mapDirectory, mapFolderNameReverse)
try:
    os.mkdir(newDirectory)
except FileExistsError:
    print("Reverse folder already exists. " + newDirectory)


# --- Find map info

onlyfiles = [f for f in listdir(mapDirectory) if isfile(join(mapDirectory, f))]  # Looks for files in the map directory

for fileName in onlyfiles:
    if fileName.endswith(".jpg") or fileName.endswith(".png"):
        imageName = fileName

infoFile = open(f"{mapDirectory}\\info.dat")
infoJson = json.load(infoFile)


songBPM = infoJson["_beatsPerMinute"]

for difficultyBeatmapSet in infoJson["_difficultyBeatmapSets"]:  # Standard, One Saber, etc.

    characteristicName = difficultyBeatmapSet["_beatmapCharacteristicName"]

    for difficultyBeatmap in difficultyBeatmapSet["_difficultyBeatmaps"]:
        difficultyBeatmap["_customData"]["_editorOffset"] = difficultyBeatmap["_customData"]["_editorOffset"] * 2
        difficultyBeatmap["_customData"]["_editorOldOffset"] = difficultyBeatmap["_customData"]["_editorOldOffset"] * 2  # Double the offset in info.dat
        songOffsets.append({
            "name": f'{difficultyBeatmap["_difficulty"]}{characteristicName}',
            "offset": f'{difficultyBeatmap["_customData"]["_editorOffset"]}'  # EX: {"name": "ExpertPlusStandard", "offset": -29}, offset is now redundant
        })

for fileName in os.listdir(mapDirectory):
    if fileName.lower().endswith(".dat") and fileName.lower() != "info.dat":  # .dat files that aren't the info file
        difficultyList.append(fileName)
    if fileName.lower().endswith(".egg") or fileName.lower().endswith(".ogg"):  # Song files ending in .ogg or .egg, both get read the same way.
        songName = fileName

tag = tt.get(f"{mapDirectory}\\{songName}")
songLength = tag.duration  # Outside import used for getting the duration, works for .ogg and .egg

# --- Reverse map

for difficultyName in difficultyList:

    print("working on " + difficultyName)

    with open(f"{mapDirectory}\\{difficultyName}") as inFile:
        difficultyJson = json.load(inFile)
        for difficulty in songOffsets:
            if difficulty["name"].lower() == difficultyName[:-4].lower():
                try:
                    songOffset = float(f'0.0{difficulty["offset"]}')
                except:
                    songOffset = 0
            else:
                songOffset = 0
        
        for event in difficultyJson["_events"]:  # Lighting
            event["_time"] = (songLength/60*songBPM) - (event["_time"])
        for note in difficultyJson["_notes"]:  # Blocks // Bombs
            note["_time"] = (songLength/60*songBPM) - (note["_time"])
        for wall in difficultyJson["_obstacles"]:  # Walls
            wall["_time"] = (songLength/60*songBPM) - (wall["_time"] + wall["_duration"])
        for bpmChange in difficultyJson["_customData"]["_BPMChanges"]:  # BPM Changes, though it doesnt really matter
            bpmChange["_time"] = (songLength/60*songBPM) - (bpmChange["_time"])
        for bookmark in difficultyJson["_customData"]["_bookmarks"]:  # Bookmarks
            bookmark["_time"] = (songLength/60*songBPM) - bookmark["_time"]

        # Maybe in the future I can make all the metadata also appear backwards

        # --- Dump reversed map files

        with open(f"{newDirectory}\\{difficultyName}", "w+") as outFile:
            json.dump(difficultyJson, outFile)

        with open(f"{newDirectory}\\info.dat", "w+") as outFile:
            json.dump(infoJson, outFile)

        copyfile(f"{mapDirectory}\\{imageName}", f"{newDirectory}\\{imageName}")

        copyfile (f"{mapDirectory}\\{songName}", f"{newDirectory}\\{songName}")