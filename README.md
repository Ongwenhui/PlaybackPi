# PlaybackPi
All the files in here go into the <code>/home/pi/mqtt_client</code> directory in the playback RPi. There are two things that are dfferent in this repo: the <code>Maskers</code>
directory containing all the audio files (maskers and audio prompts for playback, evaluation and end of experiment) and the <code>ParticipantOrder</code> directory
containing all the CSV files detailing the specific orders of masker playback for each participant (for this one, I've uploaded a zip file containing the CSVs instead).

# mqttlogicimplementaion.py usage
Run <code>python3 mqttlogicimplementation2.py</code> to start the script. There will be a prompt that looks like this:
  Enter the id of the participant (3 digits): 
Input only the last 3 digits of the participant id e.g. participant_00001 enter only '001'
There will be a pause while the first batch of predictions is being fetched from IoT Core. After the predictions are fetched, there will be another prompt for a keypress to proceed with the rest of the experiment.

## Playback
The initial 30s playback of the selected masker will begin after the audio prompt. There are multiple possible functions that may be called depending on what is in the 'name' column of the CSV:
- <code>play4maskers</code> is called when name == 'AMSS4'. It plays the top 4 non-unique maskers from the predictions.
- <code>play2maskers</code> is called when name == 'AMSS2'. It plays the top 2 unique maskers from the predictions.
- <code>playmasker</code> is called when name == 'AMSS1'. It plays the top masker from the predictions.
- <code>playfixedmasker</code> is called by default if name =/= any of the above. It plays the name of the masker at the gain specified by the 'gain' column in the CSV.
This function is called for all other scenarios (random ARAUS, top ARAUS, bird_prior, water_prior, silence30s).
(Note: There will be a delay before the maskers are played for <code>play4maskers</code> and <code>play2maskers</code>. This is because the code is generating the 4 channel audio data on the spot).

## Evaluation
After the initial 30s playback of the masker is done, the evaluation phase will begin after the audio prompt. During the evaluation, the previous masker will be played
on loop for the participant. At any point during the evaluation phase, the participant can press any key on the keyboard to proceed to the next masker. Note that the
keyboard input must be done in the terminal that's running the script.

## End of experiment
The experiment will end after a total of 24 maskers. There will be an audio prompt signalling the end of the experiment.

# Other notes
I've uploaded this version of the playback pi image into Teams
