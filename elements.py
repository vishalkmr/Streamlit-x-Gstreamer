##################################################################################################################
# Author: Vishal Kumar
# Email: vishalkmr01123@gmail.com
#
# This file contains the GstreamerElements class which is used to initialize and manage Gstreamer elements.
# The class provides methods for creating and linking various Gstreamer elements, such as videoconvert, capsfilter. 
# It is used in conjunction with the GStreamerPipeline class to build and manage Gstreamer pipelines for video processing.
##################################################################################################################

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import queue , threading
from utils import *
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx


class GstreamerElements: 
    def __init__(self, pipeline):
        """
        Initializes the Gstreamer_Elements class with a given pipeline.

        Args:
            pipeline (Gst.Pipeline): The Gstreamer pipeline to which elements will be added.
        """
        self.pipeline = pipeline
        self.buffer_queue = queue.Queue(maxsize=10000)
        self.in_frame_num = 1
        self.in_time = None
        
        progress_text = "Frame processed"
        self.my_bar = st.empty()
    @element_info
    def videotestsrc(self, pattern=18, flip=False, motion=0, animation_mode=0):
        """
        This function adds a videotestsrc element in the Gstreamer pipeline and sets its properties.

        Args:
            pattern (int): The test pattern to produce. The pattern is a number that corresponds to a specific test pattern in the Gstreamer library.
            flip (bool, optional): If set to True, the video will be flipped. Defaults to False.
            motion (int, optional): The motion of the video. Defaults to 0.
            animation_mode (int, optional): The animation mode of the video. Defaults to 0.

        Returns:
            Gst.Element: The videotestsrc element that was created and added to the pipeline.
        """
        videotestsrc = Gst.ElementFactory.make("videotestsrc", "videotestsrc")
        videotestsrc.set_property("pattern",pattern)
        if pattern == 18:
            videotestsrc.set_property("flip", flip)
            videotestsrc.set_property("motion", motion)
            videotestsrc.set_property("animation-mode", animation_mode)
        self.pipeline.add(videotestsrc)
        return videotestsrc

    @element_info
    def filesrc(self, file_path):
        """
        This function adds a filesrc element to the Gstreamer pipeline and sets the file path.

        Args:
            file_path (str): The path to the input file.

        Returns:
            Gst.Element: The filesrc element that was created and added to the pipeline.
        """
        filesrc = Gst.ElementFactory.make("filesrc", "filesrc")
        filesrc.set_property("location", file_path)
        self.pipeline.add(filesrc)
        return filesrc

    @element_info
    def nvjpegdec(self, element):
        """
        This function adds an nvjpegdec element to the Gstreamer pipeline and links it to a previous element.

        Args:
            element (Gst.Element): The Gstreamer element to which the nvjpegdec is linked.

        Returns:
            Gst.Element: The nvjpegdec element that was created and added to the pipeline.
        """
        nvjpegdec = Gst.ElementFactory.make("nvjpegdec", "nvjpegdec")
        self.pipeline.add(nvjpegdec)
        element.link(nvjpegdec)
        return nvjpegdec

    @element_info
    def jpegdec(self, element):
        """
        This function adds a jpegdec element to the Gstreamer pipeline and links it to a previous element.

        Args:
            element (Gst.Element): The Gstreamer element to which the jpegdec is linked.

        Returns:
            Gst.Element: The jpegdec element that was created and added to the pipeline.
        """
        jpegdec = Gst.ElementFactory.make("jpegdec")
        self.pipeline.add(jpegdec)
        element.link(jpegdec)
        return jpegdec

    @element_info
    def pngdec(self, element):
        """
        This function adds a pngdec element to the Gstreamer pipeline and links it to a previous element.

        Args:
            element (Gst.Element): The Gstreamer element to which the pngdec is linked.

        Returns:
            Gst.Element: The pngdec element that was created and added to the pipeline.
        """
        pngdec = Gst.ElementFactory.make("pngdec")
        self.pipeline.add(pngdec)
        element.link(pngdec)
        return pngdec

    @element_info
    def qtdemux(self, element):
        """
        This function adds a qtdemux element to the Gstreamer pipeline and links it to a previous element.

        Args:
            element (Gst.Element): The Gstreamer element to which the qtdemux is linked.

        Returns:
            Gst.Element: The qtdemux element that was created and added to the pipeline.
        """
        qtdemux = Gst.ElementFactory.make("qtdemux")
        self.pipeline.add(qtdemux)
        element.link(qtdemux)
        return qtdemux


    def demuxer_pad_added(self, demuxer, pad, avdec_h264):

        # comment out below to debug inside callbacks
        # import pydevd_pycharm
        # pydevd_pycharm.settrace()

        if pad.name == 'video_0':
            demuxer.link(avdec_h264)

    @element_info
    def nvstreammux(self, element, width, height, batch_size=1):
        """
        This function adds an nvstreammux element to the Gstreamer pipeline and sets its properties.

        Args:
            width (int): The width of the output stream.
            height (int): The height of the output stream.
            batch_size (int, optional): The number of batched frames. Defaults to 1.

        Returns:
            Gst.Element: The nvstreammux element that was created and added to the pipeline.
        """
        nvstreammux = Gst.ElementFactory.make("nvstreammux", "nvstreammux")
        self.pipeline.add(nvstreammux)
        element.link(nvstreammux)
        nvstreammux.set_property("width", width)
        nvstreammux.set_property("height", height)
        nvstreammux.set_property("batch-size", batch_size)
        return nvstreammux


    @element_info
    def h264parse(self, element):
        """
        This function adds an h264parse element to the Gstreamer pipeline and links it to a previous element.

        Args:
            element (Gst.Element): The Gstreamer element to which the h264parse is linked.

        Returns:
            Gst.Element: The h264parse element that was created and added to the pipeline.
        """
        h264parse = Gst.ElementFactory.make("h264parse")
        self.pipeline.add(h264parse)
        element.link(h264parse)
        return h264parse

    @element_info
    def avdec_h264(self, element=None):
        """
        This function adds an avdec_h264 element to the Gstreamer pipeline and links it to a previous element.

        Returns:
            Gst.Element: The avdec_h264 element that was created and added to the pipeline.
        """
        avdec_h264 = Gst.ElementFactory.make("avdec_h264", "avdec_h264")
        self.pipeline.add(avdec_h264)
        
        if element is not None:
            element.link(avdec_h264)

        return avdec_h264

    def nvv4l2decoder(self, element):
        """
        This function adds an nvv4l2decoder element to the Gstreamer pipeline and links it to a previous element.

        Args:
            element (Gst.Element): The Gstreamer element to which the nvv4l2decoder is linked.

        Returns:
            Gst.Element: The nvv4l2decoder element that was created and added to the pipeline.
        """
        nvv4l2decoder = Gst.ElementFactory.make("nvv4l2decoder", "nvv4l2decoder")
        self.pipeline.add(nvv4l2decoder)
        element.link(nvv4l2decoder)
        return nvv4l2decoder

    @element_info
    def uridecodebin(self, uri):
        """
        This function adds a uridecodebin element to the Gstreamer pipeline and sets the uri.

        Args:
            uri (str): The uri to the input file.

        Returns:
            Gst.Element: The uridecodebin element that was created and added to the pipeline.
        """
        uridecodebin = Gst.ElementFactory.make("uridecodebin", "uridecodebin")
        uridecodebin.set_property("uri", uri)
        self.pipeline.add(uridecodebin)
        return uridecodebin

    @element_info
    def identity(self, element, silent=0):
        """
        This function adds an identity element in the Gstreamer pipeline and sets its properties.

        Args:
            element (Gst.Element): The Gstreamer element to which the identity is linked.
            silent (bool, optional): If set to True, the identity element will not log info messages. Defaults to False.

        Returns:
            Gst.Element: The identity element that was created and added to the pipeline.
        """
        identity = Gst.ElementFactory.make("identity")
        self.pipeline.add(identity)
        identity.set_property("silent",silent)
        element.link(identity)
        return identity

    @element_info
    def queue(self, element, leaky=False, max_buffer=200, max_bytes=10485760):
        """
        This function adds a queue element in the Gstreamer pipeline and sets its properties.

        Args:
            element (Gst.Element): The Gstreamer element to which the queue is linked.
            leaky (bool, optional): If set to True, the queue becomes leaky and can drop old buffers when the queue is full. Defaults to False.
            max_buffer (int, optional): The maximum number of buffers that can be stored in the queue. If the queue is full, it will not accept any more buffers until a buffer is removed. Defaults to 200.
            max_bytes (int, optional): The maximum amount of data in bytes that can be stored in the queue. If the queue is full, it will not accept any more data until some data is removed. Defaults to 10485760 (10 MB).

        Returns:
            Gst.Element: The queue element that was created and added to the pipeline.
        """
        queue = Gst.ElementFactory.make("queue")
        queue.set_property("leaky",leaky)
        queue.set_property("max-size-buffers", max_buffer)
        queue.set_property("max-size-bytes", max_bytes)
        self.pipeline.add(queue)
        element.link(queue)
        return queue

    @element_info
    def tee(self, element):
        """
        This function adds a tee element in the Gstreamer pipeline and sets its properties.

        Args:
            element (Gst.Element): The Gstreamer element to which the tee is linked.

        Returns:
            Gst.Element: The tee element that was created and added to the pipeline.
        """
        tee = Gst.ElementFactory.make("tee")
        self.pipeline.add(tee)
        element.link(tee)
        return tee

    def multi_queue(self, element, n):
        """
        This function adds a tee element and n queue elements in the Gstreamer pipeline and sets their properties.

        Args:
            element (Gst.Element): The Gstreamer element to which the tee is linked.
            n (int): The number of tee branches to be created.

        Returns:
            list: The list of queue elements that were created and added to the pipeline.
        """
        tee = self.tee(element)
        queues = []
        for _ in range(n):
            queue = self.queue(tee)
            queues.append(queue)
        return queues

    @element_info
    def videoconvert(self, element):
        """
        This function adds a videoconvert element in the Gstreamer pipeline and sets its properties.

        Args:
            element (Gst.Element): The Gstreamer element to which the videoconvert is linked.

        Returns:
            Gst.Element: The videoconvert element that was created and added to the pipeline.
        """
        videoconvert = Gst.ElementFactory.make("videoconvert")
        self.pipeline.add(videoconvert)
        element.link(videoconvert)
        return videoconvert

    @element_info
    def nvvideoconvert(self, element, flip_method, interpolation_method, src_crop, dest_crop):
        """
        This function adds an nvvideoconvert element to the Gstreamer pipeline and sets its properties.
        The nvvideoconvert element is used for format conversion and scaling of video frames in NVIDIA GPU-accelerated pipelines.

        Args:
            element (Gst.Element): The Gstreamer element to which the nvvideoconvert is linked.
            flip_method (str): The flip method for video conversion.
            interpolation_method (str): The interpolation method for video conversion.
            src_crop (str): The source crop for video conversion.
            dest_crop (str): The destination crop for video conversion.

        Returns:
            Gst.Element: The nvvideoconvert element that was created and added to the pipeline.
        """
        nvvideoconvert = Gst.ElementFactory.make("nvvideoconvert", "nvvideoconvert")
        nvvideoconvert.set_property("flip-method", flip_method)
        nvvideoconvert.set_property("interpolation-method", interpolation_method)
        nvvideoconvert.set_property("src-crop", src_crop)
        nvvideoconvert.set_property("dest-crop", dest_crop)
        self.pipeline.add(nvvideoconvert)
        element.link(nvvideoconvert)
        return nvvideoconvert


    @element_info
    def capsfilter(self, element, memory_type=None, format=None, width=None, height=None):
        """
        This function adds a capsfilter element to the Gstreamer pipeline and sets its properties based on width, height, and memory type.

        Args:
            element (Gst.Element): The Gstreamer element to which the capsfilter is linked.
            memory_type (str, optional): The memory type (e.g., 'NVMM', 'System'). Defaults to 'System'.
            format (str, optional): The format of the video data. Defaults to "I420".
            width (int): The desired width of the video stream.
            height (int): The desired height of the video stream.

        Returns:
            Gst.Element: The capsfilter element that was created and added to the pipeline.
        """
        caps_filter = Gst.ElementFactory.make('capsfilter', 'caps')
        caps_string = ""

        if memory_type:
            caps_string += f'video/x-raw(memory:{memory_type})'
        else:
            caps_string = f'video/x-raw'

        if format:
            caps_string += f', format=(string){format}'
        else:
            caps_string += f'"'

        if width and width:
            caps_string += f', width={width}, height={height}'

        caps = Gst.Caps.from_string(caps_string)
        caps_filter.set_property('caps', caps)
        self.pipeline.add(caps_filter)
        element.link(caps_filter)
        return caps_filter


    @element_info
    def textoverlay(self, element, text=None, valignment="bottom", halignment="center", font_desc="Sans, 24"):
        """
        This function creates a textoverlay element in the Gstreamer pipeline and sets its properties.

        Args:
            element (Gst.Element): The Gstreamer element to which the textoverlay is linked.
            text (str): The text to be displayed.
            valignment (str, optional): Vertical alignment of the text. Defaults to "bottom".
            halignment (str, optional): Horizontal alignment of the text. Defaults to "center".
            font_desc (str, optional): Font description of the text. Defaults to "Sans, 24".

        Returns:
            Gst.Element: The textoverlay element that was created and added to the pipeline.
        """
        textoverlay = Gst.ElementFactory.make("textoverlay", "textoverlay")
        if text:
            textoverlay.set_property("text", text)
            textoverlay.set_property("valignment", valignment)
            textoverlay.set_property("halignment", halignment)
            textoverlay.set_property("font-desc", font_desc)
        self.pipeline.add(textoverlay)
        element.link(textoverlay)
        return textoverlay

    @element_info
    def pngenc(self, element, compression_level=9):
        """
        This function adds a pngenc element to the Gstreamer pipeline, sets its properties, and links it to a previous element.

        Args:
            element (Gst.Element): The Gstreamer element to which the pngenc is linked.
            compression_level (int, optional): The PNG compression level (0-9). Defaults to 9.

        Returns:
            Gst.Element: The pngenc element that was created and added to the pipeline.
        """
        pngenc = Gst.ElementFactory.make("pngenc", "pngenc")
        pngenc.set_property("compression-level", compression_level)
        self.pipeline.add(pngenc)
        element.link(pngenc)
        return pngenc

    @element_info
    def jpegenc(self, element, quality=85):
        """
        This function adds a jpegenc element to the Gstreamer pipeline, sets its properties, and links it to a previous element.

        Args:
            element (Gst.Element): The Gstreamer element to which the jpegenc is linked.
            quality (int, optional): The JPEG compression quality (0-100). Defaults to 85.

        Returns:
            Gst.Element: The jpegenc element that was created and added to the pipeline.
        """
        jpegenc = Gst.ElementFactory.make("jpegenc", "jpegenc")
        jpegenc.set_property("quality", quality)
        self.pipeline.add(jpegenc)
        element.link(jpegenc)
        return jpegenc

    @element_info
    def x264enc(self, element, bitrate=2000, speed_preset="ultrafast", tune="zerolatency"):
        """
        This function adds an x264enc element to the Gstreamer pipeline, sets its properties, and links it to a previous element.

        Args:
            element (Gst.Element): The Gstreamer element to which the x264enc is linked.
            bitrate (int, optional): The desired bitrate for the encoded video in Kbps. Defaults to 2000.
            speed_preset (str, optional): The encoding speed preset (e.g., 'ultrafast', 'superfast', 'veryfast'). Defaults to 'ultrafast'.
            tune (str, optional): The x264enc tune option (e.g., 'zerolatency', 'film', 'animation'). Defaults to 'zerolatency'.

        Returns:
            Gst.Element: The x264enc element that was created and added to the pipeline.
        """
        x264enc = Gst.ElementFactory.make("x264enc", "x264enc")
        x264enc.set_property("bitrate", bitrate)
        x264enc.set_property("speed-preset", speed_preset)
        x264enc.set_property("tune", tune)
        self.pipeline.add(x264enc)
        element.link(x264enc)
        return x264enc

    def nvv4l2h264enc(self, element, bitrate=2000000, preset="hp", control_rate=1):
        """
        This function adds an nvv4l2h264enc element to the Gstreamer pipeline, sets its properties, and links it to a previous element.

        Args:
            element (Gst.Element): The Gstreamer element to which the nvv4l2h264enc is linked.
            bitrate (int, optional): The desired bitrate for the encoded video in bps (bits per second). Defaults to 2,000,000 bps (2 Mbps).
            preset (str, optional): The encoder preset (e.g., 'hp', 'hq', 'll', 'll-hp'). Defaults to 'hp'.
            control_rate (int, optional): The control rate (1 = constant bitrate, 2 = variable bitrate). Defaults to 1 (constant bitrate).

        Returns:
            Gst.Element: The nvv4l2h264enc element that was created and added to the pipeline.
        """
        nvv4l2h264enc = Gst.ElementFactory.make("nvv4l2h264enc", "nvv4l2h264enc")
        nvv4l2h264enc.set_property("bitrate", bitrate)
        nvv4l2h264enc.set_property("preset", preset)
        nvv4l2h264enc.set_property("control-rate", control_rate)
        self.pipeline.add(nvv4l2h264enc)
        element.link(nvv4l2h264enc)
        return nvv4l2h264enc

    @element_info
    def qtmux(self, element):
        """
        This function adds a qtmux element to the Gstreamer pipeline and links it to a previous element.

        Args:
            element (Gst.Element): The Gstreamer element to which the qtmux is linked.

        Returns:
            Gst.Element: The qtmux element that was created and added to the pipeline.
        """
        qtmux = Gst.ElementFactory.make("qtmux", "qtmux")
        self.pipeline.add(qtmux)
        element.link(qtmux)
        return qtmux

    @element_info
    def mp4mux(self, element):
        """
        This function adds an mp4mux element to the Gstreamer pipeline and links it to a previous element.

        Args:
            element (Gst.Element): The Gstreamer element to which the mp4mux is linked.

        Returns:
            Gst.Element: The mp4mux element that was created and added to the pipeline.
        """
        mp4mux = Gst.ElementFactory.make("mp4mux", "mp4mux")
        self.pipeline.add(mp4mux)
        element.link(mp4mux)
        return mp4mux

    @element_info
    def filesink(self, element, output_file, file_ext):
        """
        This function adds a filesink element to the Gstreamer pipeline, sets its properties, and links it to a previous element.

        Args:
            element (Gst.Element): The Gstreamer element to which the filesink is linked.
            output_file (str): The name of the output file without the file extension.
            file_ext (str): The file extension (e.g., 'mp4', 'avi', 'mkv').

        Returns:
            Gst.Element: The filesink element that was created and added to the pipeline.
        """
        filesink = Gst.ElementFactory.make("filesink", "filesink")
        filesink.set_property("location", f"output/{output_file}.{file_ext}")
        filesink.set_property("async", True)
        self.pipeline.add(filesink)
        element.link(filesink)
        return filesink

    @element_info
    def autovideosink(self, element, sync=True):
        """
        This function adds an autovideosink element in the Gstreamer pipeline and sets its properties.

        Args:
            element (Gst.Element): The Gstreamer element to which the autovideosink is linked.
            sync: 

        Returns:
            Gst.Element: The autovideosink element that was created and added to the pipeline.
        """
        autovideosink = Gst.ElementFactory.make("autovideosink","autovideosink")
        autovideosink.set_property("sync", sync)
        self.pipeline.add(autovideosink)
        element.link(autovideosink)
        return autovideosink

    # Define a callback function to receive the buffer data on appsink
    def buffer_dump_prob(self, appsink):
        sample = appsink.emit("pull-sample")
        if sample:
            self.in_frame_num +=1
            # st.session_state.in_frame +=1
            buffer = sample.get_buffer()
            # Parsing caps format
            caps_format = sample.get_caps().get_structure(0)
            w, h,format = caps_format.get_value('width'), caps_format.get_value('height'),caps_format.get_value('format')
            # Parsing the buffer into yuv2 image
            buffer_size = buffer.get_size()
            data = buffer.extract_dup(0, buffer_size)
            rgb_converter = RGB_Converter()
            rgb_image = rgb_converter.buffer_to_rgb(data,w,h,format)
            #push the buffer into buffer_queue
            # rgb_image = cv2.resize(rgb_image, (320, 240))
            self.buffer_queue.put(rgb_image,block=False)

        return Gst.FlowReturn.OK

    @element_info
    def appsink(self, element):
        """
        This function adds an appsink element in the Gstreamer pipeline, sets its properties, and connects the buffer_dump_prob function to its "new-sample" signal.

        Args:
            element (Gst.Element): The Gstreamer element to which the appsink is linked.

        Returns:
            Gst.Element: The appsink element that was created and added to the pipeline.
        """
        appsink = Gst.ElementFactory.make("appsink", "appsink")
        # Set the appsink to emit signals when data is available
        appsink.set_property("buffer-list", True)
        appsink.set_property("emit-signals", True)
        appsink.set_property("drop", True)

        # Connect the callback function to the appsink's "new-sample" signal
        appsink.connect("new-sample", self.buffer_dump_prob)

        self.pipeline.add(appsink)
        element.link(appsink)
        return appsink


    def read_input(self, input_file, width=None, height=None):
        filesrc = self.filesrc(file_path=input_file)
        file_ext = input_file.split(".")[-1].lower()

        if file_ext == "h264":
            # Since the data format in the input file is elementary h264 stream, We need a h264parser
            parser = self.h264parse(filesrc)

            # Use avdec_h264 for decoding h264
            decoder = self.avdec_h264(parser)

        elif file_ext == "mp4":
            qtdemux = self.qtdemux(filesrc)
            decoder = self.avdec_h264()
            # Dynamically link the qtdemux and decoder
            qtdemux.connect("pad-added", self.demuxer_pad_added, decoder)

        elif file_ext == "jpg":
            # Create an jpegdec element
            decoder = self.jpegdec(filesrc)

        elif file_ext == "png":
            # Create an pngdec element
            decoder = self.pngdec(filesrc)
            # decoder = self.videoconvert(decoder)

        # decoded_output = self.videoconvert(decoder)
        return decoder
    
    def read_input1(self, input_file, width=None, height=None):
        filesrc = self.filesrc(file_path=input_file)
        file_ext = input_file.split(".")[-1].lower()

        if file_ext == "h264":
            # Since the data format in the input file is elementary h264 stream, We need a h264parser
            parser = self.h264parse(filesrc)

            # Use avdec_h264 for decoding h264
            decoder = self.nvv4l2decoder(parser)

        elif file_ext == "mp4":
            qtdemux = self.qtdemux(filesrc)
            decoder = self.avdec_h264()
            # Dynamically link the qtdemux and decoder
            qtdemux.connect("pad-added", self.demuxer_pad_added, decoder)
        
        elif file_ext == "jpg":
            # Create an jpegdec element
            decoder = self.jpegdec(filesrc)

        elif file_ext == "png":
            # Create an pngenc element
            decoder = self.pngenc(filesrc)

        streammux = self.nvstreammux(width=width, height=height)
        sinkpad = streammux.get_request_pad("sink_0")
        srcpad = decoder.get_static_pad("src")
        srcpad.link(sinkpad)


        # decoded_output = self.videoconvert(decoder)
        return streammux

    def write_output(self, element, output_file, file_ext, async_mode=False):
        if file_ext == "mp4" or file_ext == "h264":
            # Create an x264enc element and link it to the videoconvert
            encoder = self.x264enc(element)

            # Create a h264parse element and link it to the encoder
            parser = self.h264parse(encoder)

            # Create a mp4mux element and link it to the h264parse
            encoded_output = self.mp4mux(parser)

            file_ext = "mp4"

        elif file_ext == "jpg":
            # Create an jpegenc element
            encoder = self.jpegenc(element)
            # encoded_output = self.videoconvert(encoder)
            encoded_output = encoder


        elif file_ext == "png":
            # Create an pngenc element
            encoder = self.pngenc(element)
            encoded_output = self.videoconvert(encoder)
        
        return self.filesink(encoded_output, output_file=output_file, file_ext=file_ext)


    def write_output1(self, element, output_file, file_ext):
        if file_ext == "mp4" or file_ext == "h264":
            # Create an nvv4l2h264enc element and link it to the videoconvert
            encoder = self.nvv4l2h264enc(element)

            # Create a h264parse element and link it to the encoder
            parser = self.h264parse(encoder)

            # Create a qtmux element and link it to the h264parse
            encoded_output = self.qtmux(parser)

            file_ext = "mp4"

        elif file_ext == "jpg":
            # Create an jpegenc element
            encoder = self.jpegenc(element)
            encoded_output = self.nvvideoconvert(encoder)

        elif file_ext == "png":
            # Create an pngenc element
            encoder = self.pngenc(element)
            encoded_output = self.nvvideoconvert(encoder)
        
        return self.filesink(encoded_output, output_file=output_file, file_ext=file_ext)
