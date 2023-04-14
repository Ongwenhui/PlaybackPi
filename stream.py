import argparse
import queue
import sys
import threading

import sounddevice as sd
import soundfile as sf


file2 = 'bird_00065.wav'
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
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
# parser.add_argument(
#     "maskerpath", metavar='maskerpath',
#     help='audio file to be played back')
# parser.add_argument(
#     'file1', metavar='FILE1',
#     help='audio file1 to be played back')
# parser.add_argument(
#     'file2', metavar='FILE2',
#     help='audio file2 to be played back')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='output device (numeric ID or substring)')
parser.add_argument(
    '-b', '--blocksize', type=int, default=2048,
    help='block size (default: %(default)s)')
parser.add_argument(
    '-q', '--buffersize', type=int, default=20,
    help='number of blocks used for buffering (default: %(default)s)')
args = parser.parse_args(remaining)
if args.blocksize == 0:
    parser.error('blocksize must not be zero')
if args.buffersize < 1:
    parser.error('buffersize must be at least 1')

q = queue.Queue(maxsize=args.buffersize)
q2 =queue.Queue()
event = threading.Event()


def callback(outdata, frames, time, status):
    assert frames == args.blocksize
    if status.output_underflow:
        print('Output underflow: increase blocksize?', file=sys.stderr)
        raise sd.CallbackAbort
    assert not status
    try:
        data = q.get_nowait()
        # print(data)
    except queue.Empty:
        print('Buffer is empty: increase buffersize?', file=sys.stderr)
        raise sd.CallbackAbort
    if len(data) < len(outdata):
        outdata[:len(data)] = data
        outdata[len(data):].fill(0)
        raise sd.CallbackStop
    else:
        outdata[:] = data

def soundplayer(maskerpath,file1,file2):
    try:
        with sf.SoundFile(maskerpath + file1) as f:
            for _ in range(args.buffersize):
                data = f.read(args.blocksize, always_2d=True)
                # print(data.shape)
                if not data:
                    break
                q.put_nowait(data)  # Pre-fill queue
        # f = sf.SoundFile(maskerpath + file1)
            stream = sd.OutputStream(
                samplerate=f.samplerate, blocksize=args.blocksize,
                device=args.device, channels=f.channels,
                callback=callback, finished_callback=event.set)
            with stream:


                timeout = args.blocksize * args.buffersize / f.samplerate
                inputtextdata = "file1"
                while data:

                    # data = f.read(args.blocksize, dtype='float32')
                    # q.put(data, timeout=timeout)
                    if not q2.empty():
                        inputtextdatanew = q2.get_nowait()
                    else:
                        inputtextdatanew = ""
                    # else:
                    #     inputtextdata - ""
                    if inputtextdatanew == "file1" and inputtextdatanew != inputtextdata:
                        for i in range(5):
                            print(i)
                            # data = f.read(args.blocksize, always_2d=True)*(1/(i+1))
                            # q.put(data, timeout=timeout)
                        f = sf.SoundFile(maskerpath + file1)
                        inputtextdata = inputtextdatanew
                    elif inputtextdatanew == "file2" and inputtextdatanew != inputtextdata:
                        for i in range(5):
                            data = f.read(args.blocksize, always_2d=True)*(1/(i+1))
                            # print(data)
                            q.put(data, timeout=timeout)
                        f = sf.SoundFile(maskerpath + file2)
                        inputtextdata = inputtextdatanew
                    else:
                        data = f.read(args.blocksize, always_2d=True)
                        q.put(data, timeout=timeout)
                        
                event.wait()  # Wait until playback is finished

    except KeyboardInterrupt:
        parser.exit('\nInterrupted by user')
    except queue.Full:
        # A timeout occurred, i.e. there was an error in the callback
        parser.exit(1)
    except Exception as e:
        parser.exit(type(e).__name__ + ': ' + str(e))
def inputtext():
    while True:
        whichfile = input("Play which file?")
        q2.put(whichfile)
        print("Playing: " + whichfile)
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
soundplayer_thread.start()
input_thread.start()
soundplayer_thread.join()
input_thread.join()
