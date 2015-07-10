#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import time
import uuid
import json
import tempfile
import subprocess



if sys.version_info[:2] >= (3, 0):
    decode_if_py3 = lambda x: x.decode("utf8")
else:
    decode_if_py3 = lambda x: x


if sys.platform == "win32":
    PLATFORM   = "windows"
else:
    PLATFORM   = "linux"




class Log():
    def __init__(self, user="Unknown"):
        self.user = user
        self.formats = {
            "DEBUG"     : "DEBUG      \033[34m{0:<15} {1}\033[0m",
            "INFO"      : "INFO       {0:<15} {1}",
            "WARNING"   : "\033[33mWARNING\033[0m    {0:<15} {1}",
            "ERROR"     : "\033[31mERROR\033[0m      {0:<15} {1}",
            "GOOD NEWS" : "\033[32mGOOD NEWS\033[0m  {0:<15} {1}"
            }

    def _send(self, msgtype, message):
        if PLATFORM == "linux":
            try:
                print (self.formats[msgtype].format(self.user, message))
            except:
                print (message.encode("utf-8"))
        else:
            try:
                print ("{0:<10} {1:<15} {2}".format(msgtype, self.user, message))
            except:
                print (message.encode("utf-8"))

    def debug   (self,msg): self._send("DEBUG", msg) 
    def info    (self,msg): self._send("INFO", msg) 
    def warning (self,msg): self._send("WARNING", msg) 
    def error   (self,msg): self._send("ERROR", msg) 
    def goodnews(self,msg): self._send("GOOD NEWS", msg) 


####################################
## FFMPEG Filters

def join_filters(*filters):
    """Joins multiple filters"""
    return "[in]{}[out]".format("[out];[out]".join(i for i in filters if i))

def filter_deinterlace():
    """Yadif deinterlace"""
    return "yadif=0:-1:0"

def filter_arc(w, h, aspect):
    """Aspect ratio convertor. you must specify output size and source aspect ratio (as float)"""
    taspect = float(w)/h
    if abs(taspect - aspect) < 0.01:
        return "scale=%s:%s"%(w,h)
    if taspect > aspect: # pillarbox
        pt = 0
        ph = h
        pw = int (h*aspect)
        pl = int((w - pw)/2.0)
    else: # letterbox
        pl = 0
        pw = w
        ph = int(w * (1/aspect))
        pt = int((h - ph)/2.0)
    return "scale=%s:%s[out];[out]pad=%s:%s:%s:%s:black" % (pw,ph,w,h,pl,pt)

## FFMPEG Filters
##############################
## Processing

class BaseProcessor():
    default_args = []

    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.args = []
        for arg in self.default_args:
            self.args.append(str(arg))
        for arg in args:
            self.args.append(str(arg))
        self.proc = None
        self.err = ""
        self.buff = ""

    def start(self, **kwargs):
        message = "Executing: " + " ".join(self.args)
        if "logging" in self.kwargs:
            self.kwargs["logging"].debug(message)
        else:
            print (message)
        self.proc = subprocess.Popen(
            self.args,
            stdin=kwargs.get("stdin", None),
            stdout=kwargs.get("stdout", subprocess.PIPE),
            stderr=kwargs.get("stderr", subprocess.PIPE)
            )
        if kwargs.get("check_output", True):
            self.check_output(handler=kwargs.get("handler", False))

    @property 
    def error(self):
        return self.err + self.buff + decode_if_py3(self.proc.stderr.read())


class FFMpeg(BaseProcessor):
    default_args = ["ffmpeg", "-y"]

    def check_output(self, handler=False):
        self.buff = ""
        while self.proc.poll() == None:
            ch = decode_if_py3(self.proc.stderr.read(1))
            if ch in ["\n", "\r"]:
                if self.buff.startswith("frame="):
                    at_frame = self.buff.split("fps")[0].split("=")[1].strip()
                    if handler:
                        handler(at_frame)
                self.err += self.buff + "\n"
                self.buff = ""
            else:
                self.buff += ch
        return self.proc.returncode


class Sox(BaseProcessor):
    default_args = ["sox", "-S"]

    def check_output(self, handler=False):
        self.buff = ""
        while self.proc.poll() == None:
            ch = decode_if_py3(self.proc.stderr.read(1))
            if ch in ["\n", "\r"]:
                if self.buff.startswith("In:"):
                    at_frame = self.buff.split("%")[0].split(":")[1].strip()
                    if handler:
                        handler(at_frame)
                self.err += self.buff + "\n"
                self.buff = ""
            else:
                self.buff += ch
        return self.proc.returncode

## Processing
##############################



class Themis():
    def __init__(self, fname, **kwargs):
        self.logging = kwargs.get("logging", Log("Themis"))
        if not hasattr(self.logging, "goodnews"):
            self.logging.goodnews  = self.logging.info

        self.fname = fname
        self.kwargs = kwargs

        self.loudness = False
        self.probe_result = {}
        self.tempfiles = []
        self.status = "(no result)"


    def get_temp(self, container=False):
        dr = tempfile.gettempdir()
        fn = uuid.uuid1() 
        filename =  os.path.join(dr, str(fn))
        if container:
            filename += "." + container
        self.tempfiles.append(filename)
        return filename


    def clean_temp(self):
        if self.tempfiles:
            self.logging.debug("Cleaning-up temporary files")
            for f in self.tempfiles:
                if os.path.exists(f):
                    try:
                        self.logging.warning("Unable to remove temporary file {}".format(f))
                        os.remove(f)
                    except:
                        pass

    def __del__(self):
        self.clean_temp()


    def set_status(self, message, level="debug"):
        self.status = message
        {
        False : lambda x: x,
        "debug" : self.logging.debug,
        "info" : self.logging.info,
        "warning" : self.logging.warning,
        "error" : self.logging.error
        }[level](message)


    def probe(self):
        cmd = [
            "ffprobe",
            "-show_format",
            "-show_streams",
            "-print_format", "json",
            self.fname
            ]
        FNULL = open(os.devnull, "w")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=FNULL)
        while proc.poll() == None:
            time.sleep(.1)

        if proc.returncode:
            self.logging.error("Unable to ffprobe")
            return False

        self.probe_result = json.loads(decode_if_py3(proc.stdout.read()))
        return self.probe_result


    def r128(self):
        cmd = [
            "ffmpeg",
            "-i", self.fname,
            "-filter_complex", "ebur128",
            "-vn",
            "-f", "null",
            os.devnull
            ]

        self.loudness = False

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while proc.poll() == None:
            line = decode_if_py3(proc.stderr.readline())
            if line.strip().startswith("I:"):
                self.loudness = float(line.split("I:")[-1].strip().rstrip(" LUFS"))

        if proc.returncode:
            return False

        if self.loudness == -70.0:
            self.loudness = False

        return self.loudness


    def analyze(self):
        self.logging.debug("FFProbing file {}".format(self.fname))
        self.probe()
        self.logging.debug("R128 mettering file {}".format(self.fname))
        self.r128()
        self.logging.debug("Source loudness: {} LUFS".format(self.loudness))


    def process(self, output, profile):
        self.logging.info("Transcoding {} to {}".format(self.fname, profile["name"]))
        if not self.probe_result:
            self.set_status("Unable to open source file metadata", "error")
            return False

        ###################################################################
        ## Extract streams information

        atracks = {}
        format_info = self.probe_result["format"]

        for stream in self.probe_result["streams"]:
            if stream["codec_type"] == "video":

                # Frame rate detection
                fps_n, fps_d = [float(e) for e in stream["r_frame_rate"].split("/")]
                source_fps = fps_n / fps_d

                # Aspect ratio detection
                try:
                    dar_n, dar_d = [float(e) for e in stream["display_aspect_ratio"].split(":")]
                    if not (dar_n and dar_d):
                        raise Exception
                except:
                    dar_n, dar_d = float(stream["width"]), float(stream["height"])
                source_dar = dar_n / dar_d

                # Video track duration
                try:
                    source_vdur = float(stream["duration"])
                except: 
                    source_vdur = False

                source_vcodec = stream["codec_name"]
                source_pix_fmt = stream["pix_fmt"]
                source_width = stream["width"]
                source_height = stream["height"]
                video_index = stream["index"]


            elif stream["codec_type"] == "audio":
                atracks[int(stream["index"])] = stream 

        track_indices = atracks.keys()
        atrack = {}

        if track_indices:
            atrack = atracks[min(track_indices)]
            has_audio = True
        else:
            has_audio = False

        duration = source_vdur or float(format_info["duration"])

        ## Extract streams information
        ###################################################################
        ## Check, which streams must be re-encoded

        compare_v = [
            ["container", os.path.splitext(self.fname)[1][1:]],
            ["fps", source_fps],
            ["video_codec",  source_vcodec],
            ["pixel_format", source_pix_fmt],
            ["width",  source_width],
            ["height", source_height]
            ]


        for key, val in compare_v:
            if profile[key] != val:
                self.logging.debug("Source {} does not match target format. IS: {} SHOULD BE: {}".format(key, val, profile[key]) )
                encode_video = True
                break
        else:
            encode_video = False


        ## Check, which streams must be re-encoded
        ###################################################################

        profile_fps = profile.get("fps", 25)

        if self.loudness:
            gain = self.kwargs.get("target_loudness", -23) - self.loudness
            if abs(gain) < 0.5:
                gain = 0
        else:
            gain = 0



        if encode_video:

            filters = []
            if profile.get("deinterlace", False):
                filters.append(filter_deinterlace())

            filters.append(filter_arc(profile["width"], profile["height"], source_dar) )

            if source_fps >= profile_fps or profile_fps - source_fps > 4:
                self.logging.debug("Source FPS: {}".format(source_fps))
                self.logging.debug("Target FPS: {}".format(profile_fps))

                cmd = [
                    "-i", self.fname,
                    "-r", profile_fps,
                    "-filter:v", join_filters(*filters),
                    "-pix_fmt", profile.get("pixel_format", "yuv422p"),
                    "-c:v", profile["video_codec"],
                    "-b:v", profile["video_bitrate"],
                    "-map", "0:{}".format(video_index),
                ]

                if has_audio:
                    self.logging.debug("Source has audio")
                    cmd.append("-map")
                    cmd.append("0:{}".format(atrack["index"]))

                    cmd.append("-c:a")
                    cmd.append(profile.get("audio_codec", "pcm_s16le"))

                    cmd.append("-ar")
                    cmd.append(profile.get("audio_sample_rate", 48000))

                    if profile.get("audio_bitrate", False):
                        cmd.append("-b:a")
                        cmd.append(profile["audio_bitrate"])

                    if gain:
                        self.logging.debug("Adjusting gain by {} dB".format(gain))
                        cmd.append("-filter:a")
                        cmd.append("volume={}dB".format(gain))


                cmd.append("-map_metadata")
                cmd.append("-1")

                cmd.append("-video_track_timescale")
                cmd.append(profile_fps)

                cmd.append(output)

                self.set_status("Encoding video (straight from {} to {})".format(source_fps, profile_fps), "info")
                ffmpeg = FFMpeg(*cmd, logging=self.logging)
                result = ffmpeg.start()

                if result:
                    logging.error("Encoding failed: {}".format(ffmpeg.error))
                    return False

            else:

                if has_audio:
                    sox_tempo = float(profile_fps) / source_fps

                    self.logging.debug ("Extracting audio track")

                    audio_temp_name = self.get_temp("wav")
                    audio_temp_name2 = self.get_temp("wav")

                    cmd = [
                            "-i", self.fname,
                            "-vn",
                            "-map", "0:{}".format(atrack["index"]),
                            "-c:a", "pcm_s16le",
                            audio_temp_name
                        ]

                    ffmpeg = FFMpeg(*cmd, logging=self.logging)
                    result = ffmpeg.start()
                    if result:
                        logging.error("Audio extraction failed: {}".format(ffmpeg.error))
                        return False


                    cmd = [
                            audio_temp_name,
                            "-r", profile.get("audio_sample_rate", 48000),
                            audio_temp_name2
                        ]

                    if sox_tempo:
                        self.logging.debug("SOX Tempo: {}".format(sox_tempo))
                        cmd.append("tempo")
                        cmd.append(sox_tempo)

                    if gain:
                        self.logging.debug("SOX Gain: {}".format(gain))
                        cmd.append("gain")
                        cmd.append(gain)

                    self.logging.debug("Processing audio")
                    sox = Sox(*cmd, logging=self.logging)
                    result = sox.start()

                    if result:
                        logging.error("SOX Failed: {}".format(sox.error))
                        return False


                self.set_status("Encoding video (reclock from {} to {})".format(source_fps, profile_fps), "info")

                cmd1 = [
                    "-i", self.fname,
                    "-an",
                    "-filter:v", join_filters(*filters),
                    "-pix_fmt", "yuv422p",
                    "-f", "rawvideo",
                    "-"
                    ]

                cmd2 = [
                    "-f", "rawvideo",
                    "-pix_fmt", "yuv422p",
                    "-s", "{}x{}".format(profile["width"], profile["height"]),
                    "-i", "-",
                    ]

                if has_audio:
                    cmd2.append("-i")
                    cmd2.append(audio_temp_name2)

                    cmd2.append("-c:a")
                    cmd2.append(profile.get("audio_codec", "pcm_s16le"))

                    cmd2.append("-ar")
                    cmd2.append(profile.get("audio_sample_rate", 48000))

                    if profile.get("audio_bitrate", False):
                        cmd2.append("-b:a")
                        cmd2.append(profile["audio_bitrate"])


                cmd2.append("-r")
                cmd2.append(profile_fps)

                cmd2.append("-c:v")
                cmd2.append(profile["video_codec"])
                cmd2.append("-b:v")
                cmd2.append(profile["video_bitrate"])


                cmd2.append("-map_metadata")
                cmd2.append("-1")

                cmd2.append("-video_track_timescale")
                cmd2.append(profile_fps)

                cmd2.append(output)



                p1 = FFMpeg(*cmd1, logging=self.logging)
                p1.start(check_output=False)

                p2 = FFMpeg(*cmd2, logging=self.logging)
                p2.start(check_output=False, stdin=p1.proc.stdout)

                p1.proc.stdout.close()


                while True:
                    if p1.proc.poll() != None:
                        logging.debug("Proc 1 ended")
                    elif p2.proc.poll() != None:
                        logging.debug("Proc 2 ended")
                    else:
                        time.sleep(.001)
                        continue
                    break


        # Just change audio gain
        elif gain:
            self.logging.debug("Adjusting gain by {} dB".format(gain))
            cmd = [
                    "-i", self.fname,

                    "-map", "0:{}".format(video_index),
                    "-map", "0:{}".format(atrack["index"]),

                    "-c:v", "copy",
                    "-c:a", profile.get("audio_codec", "pcm_s16le"),
                    "-ar", profile.get("audio_sample_rate", 48000),
                    "-filter:a", "volume={}dB".format(gain)
                ]


            if profile.get("audio_bitrate", False):
                cmd.append("-b:a")
                cmd.append(profile["audio_bitrate"])

            cmd.append("-map_metadata")
            cmd.append("-1")

            cmd.append("-video_track_timescale")
            cmd.append(profile_fps)

            cmd.append(output)

            ffmpeg = FFMpeg(*cmd, logging=self.logging)
            ffmpeg.start()

        else:
            self.logging.info("Moving file".format(gain))
            os.rename(self.fname, output)


        self.logging.goodnews("Encoding completed")
        return True
