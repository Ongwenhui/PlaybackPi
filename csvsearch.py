import csv
calibgains = {}
with open("/home/pi/maskers/Calibrations_final_speaker.csv", 'r') as file:
    csvreader = csv.reader(file)
    header = next(csvreader)
    for row in csvreader:
        entrycount = 0
        currmasker = ""
        nextgain = 0
        for entry in row:
            if entrycount == 0:
                calibgains[entry] = {}
                currmasker = entry
            elif entrycount != 0 and (entrycount % 2) != 0:
                nextgain = float(entry)
            elif entrycount != 0 and (entrycount % 2) == 0:
                calibgains[currmasker][str(int(float(entry)))] = nextgain 
            entrycount += 1

# print(header)
print(calibgains['bird_00070.wav'])