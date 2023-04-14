import argparse
import queue
import sys
import threading
import numpy

import sounddevice as sd
import soundfile as sf

file2 = 'wind_00038.wav'
file1 = 'water_00042.wav'
maskerpath = "/home/pi/maskers/"

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
buffersize = 20
blocksize = 2048


def callback(outdata, frames, time, status):
    data = numpy.zeros((2048,1))
    assert frames == blocksize
    if status.output_underflow:
        print('Output underflow: increase blocksize?', file=sys.stderr)
        raise sd.CallbackAbort
    assert not status
    try:
        data = q.get_nowait()
    except queue.Empty as e:
        print('Buffer is empty: increase buffersize?', file=sys.stderr)
        raise sd.CallbackAbort from e
    if len(data) < len(outdata) and not q.empty():
        outdata[:len(data)] = data
        outdata[len(data):].fill(0)
        print("track ending")
        raise sd.CallbackStop
    else:
        outdata[:] = data

def soundplayer(maskerpath,file1,file2,inputtextdata= ""):
    global q 
    q = queue.Queue(maxsize=buffersize)
    print("q is clear")
    while q2.empty() and inputtextdata =="":
        pass

    try:
        with sf.SoundFile(maskerpath + file1) as f:
            stream = sd.OutputStream(
                samplerate=f.samplerate, blocksize=blocksize,
                device=7, channels=f.channels,
                callback=callback, finished_callback=event.set)
            with stream:
                timeout = blocksize * buffersize / f.samplerate
                if inputtextdata == "":
                    inputtextdata = q2.get_nowait()
                q3.queue.clear()
                q3.put_nowait(inputtextdata)
                fadelength = 80

                if inputtextdata == "file1":
                    whichfile = file1
                elif inputtextdata == "file2":
                    whichfile = file2

                f = sf.SoundFile(maskerpath + whichfile)
                for _ in range(int(buffersize/2)):
                    data = f.read(blocksize, always_2d=True)
                    if not len(data):
                        break
                    q.put_nowait(data)  # Pre-fill queue
                while len(data):
                    if not q2.empty():
                        inputtextdatanew = q2.get_nowait()
                        print("inputtextdatanew =" + inputtextdatanew)
                        q3.queue.clear()
                        q3.put_nowait(inputtextdatanew)
                        print("putting " + inputtextdatanew + " into q3")
                    else:
                        inputtextdatanew = ""
                    if inputtextdatanew == "file1" and inputtextdatanew != inputtextdata:
                        fnew = sf.SoundFile(maskerpath + file1)
                        for i in range(fadelength):
                            data = f.read(blocksize, always_2d=True)*(1-(i/fadelength)) + fnew.read(blocksize, always_2d=True)*(i/fadelength)
                            q.put(data, timeout=timeout)
                        f = fnew
                        inputtextdata = inputtextdatanew
                    elif inputtextdatanew == "file2" and inputtextdatanew != inputtextdata:
                        fnew = sf.SoundFile(maskerpath + file2)
                        for i in range(fadelength):
                            data = f.read(blocksize, always_2d=True)*(1-(i/fadelength)) + fnew.read(blocksize, always_2d=True)*(i/fadelength)
                            q.put(data, timeout=timeout)
                        f = fnew
                        inputtextdata = inputtextdatanew
                    else:
                        data = f.read(blocksize, always_2d=True)
                        q.put(data, timeout=timeout)
                event.wait()  # Wait until playback is finished
            print("read done")
    except KeyboardInterrupt:
        exit

def inputtext():
    while True:
        whichfile = input("Play which file?")
        q2.put(whichfile)
        print("Playing: " + whichfile)
def looper():
    while True:
        if not q3.empty():
            currentlyplaying = q3.get_nowait()

        else:
            currentlyplaying = ""
        print("currentlyplaying =" + currentlyplaying)
        soundplayer(maskerpath,file1,file2,currentlyplaying)

soundplayer_thread = threading.Thread(
        target=soundplayer,
        name="soundplayer",
        args=(maskerpath,file1,file2),
        daemon=True,
    )
input_thread = threading.Thread(
        target=inputtext,
        name="inputtext",
        args=(),
        daemon=True,
    )

looper_thread = threading.Thread(
        target=looper,
        name="looper",
        args=(),
        daemon=True,
    )

input_thread.start()
q2 =queue.Queue()
q3 = queue.Queue(maxsize=1)
event = threading.Event()
looper_thread.start()
looper_thread.join()
input_thread.join()