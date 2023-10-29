##################################################################################################################
# Author: Vishal Kumar
# Email: vishalkmr01123@gmail.com
#
# This file contains the GStreamerPipeline class which is used to initialize and manage Gstreamer pipelines.
# The class provides methods for creating, initializing, and managing Gstreamer pipelines for video processing.
# It is used in conjunction with the GstreamerElements class to add and link various Gstreamer elements, 
# such as videoconvert, capsfilter, and tee.
#
# Users can override the following methods to customize the pipeline:
# - default_params: This method should be overridden to specify the default parameters of elements.
# - create_pipeline: This method should be overridden to create a specific pipeline. Use the self.elements 
#   attribute to add new elements to the pipeline.
#
# Example of creating a pipeline: [videotestsrc -> videoconvert -> autovideosink]
# def create_pipeline(self):
#     super().create_pipeline()
#     src = self.elements.videotestsrc()
#     vidconv = self.elements.videoconvert(src)
#     autovideosink = self.elements.autovideosink(vidconv)
##################################################################################################################

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import threading, os, glob, time
from elements import GstreamerElements
import streamlit as st
from utils import *
import queue, time
from streamlit.runtime.scriptrunner import add_script_run_ctx

class GStreamerPipeline:
    def __init__(self):
        # creating the pipeline
        self.default_params()
        self.create_pipeline()

    def default_params(self):
        """
        specify the default params of elements.
        """
        self.default_input_params()
        self.default_output_params()

    def create_pipeline(self):
        """
        This method should be overridden by subclasses to create the specific pipeline.
        Use self.element to add the new element in the pipeline
        super().create_pipeline() needs to be called in overridden code to initialize the pipeline
        """
        # Initialize GStreamer
        Gst.init(None)

        # Define the GStreamer pipeline
        self.pipeline = Gst.Pipeline()
        self.loop = GLib.MainLoop()
        self.main_loop_thread = threading.Thread(target=self.loop.run)
        add_script_run_ctx(self.main_loop_thread)
        self.main_loop_thread.start()

        # Class containing elements of gstreamer
        self.elements = GstreamerElements(self.pipeline)

        # Frame Counter
        self.out_frame_num = 1
        self.out_time = None

        # EOS flag
        self.eos_occurred = False

        # Add a signal watch to the bus
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.bus_message, self.pipeline, self.loop)


    def start(self):
        """
        This method is used to change the pipeline state to PLAYING
        """
        # Set the pipeline to playing state
        self.pipeline.set_state(Gst.State.PLAYING)
        self.elements.in_time = self.out_time = time.time()

    def stop(self):
        """
        This method is used to stop the pipeline e.i. send EOS
        """
        self.pipeline.send_event(Gst.Event.new_eos())

    def fetch_buffer(self):
        """
        This method is used to fetch the intermediate pipeline buffers stored in buffer_queue
        This buffer_queue is updated in appsink prob hence used only when appsink is used
        """
        item = self.elements.buffer_queue.get(timeout=1)
        self.out_frame_num  += 1
        return item

    def bus_message(self, bus, message, pipeline, loop):
        """
        This method dandles bus messages
        """
        bus_msg_enable= False
        if message.type == Gst.MessageType.EOS:
            pipeline.set_state(Gst.State.NULL)
            loop.quit()
            self.eos_occurred =True 
            if bus_msg_enable:
                print("Info: End of Stream!")

        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            pipeline.set_state(Gst.State.NULL)
            loop.quit()
            if bus_msg_enable:
                print("Error: %s" % err, debug)

        elif message.type == Gst.MessageType.STATE_CHANGED:
            old_state, new_state, pending_state = message.parse_state_changed()
            if bus_msg_enable:
                print("State changed from {} to {}".format(Gst.Element.state_get_name(old_state), Gst.Element.state_get_name(new_state)))

        elif message.type == Gst.MessageType.TAG:
            tag_list = message.parse_tag()
            # if bus_msg_enable:
            #     print("Tag: %s" % tag_list.to_string())

        elif message.type == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            if bus_msg_enable:
                print("Warning: %s: %s\n" % (err, debug))


    ##################################################################################################################
    ##########  FileSrc  #############################################################################################
    def default_input_file_params(self):
        st.session_state.file_uploaded = False
        st.session_state.update_params_from_input_file = True
        st.session_state.input_name = None
        st.session_state.input_type = None
        st.session_state.input_ext = "mp4"
        st.session_state.out_ext = "mp4"
        st.session_state.image_input = False
        st.session_state.input_height, st.session_state.input_width = 1920 ,1080
        st.session_state.max_frame = 10000

    def input_file_control(self):
        # Check the input directory exists if not create one
        if not os.path.exists("input"):
            os.makedirs("input")

        # Upload the input and save it
        input_file = st.file_uploader("Input Image/Video📷", type=["mp4","h264","jpg","png"],key="file_uploader",label_visibility="visible",on_change=self.update_input_file,accept_multiple_files=False,disabled=(st.session_state.status == "play"))
        if input_file is not None and st.session_state.update_params_from_input_file:
            # Save the input file
            with open("input/"+input_file.name, "wb") as f:
                f.write(input_file.getbuffer())
                print(f"INFO: File {input_file.name} is Uploaded and Saved.")

            #add the input details to session
            st.session_state.input_name = input_file.name
            st.session_state.input_type = input_file.type
            st.session_state.input_ext = input_file.name.split(".")[1].lower()
            if st.session_state.input_ext == "jpg" or st.session_state.input_ext == "png":
                st.session_state.image_input = True
                st.session_state.out_ext = "jpg"
            else:
                st.session_state.image_input = False
                st.session_state.out_ext = "mp4"
    
            file_path = "input/"+st.session_state.input_name 
            vid = cv2.VideoCapture(file_path)

            # print(vid.get(cv2.CAP_PROP_FOURCC))
            # print(vid.get(cv2.CV_FOURCC('H', '2', '6', '4')))

            if st.session_state.input_ext =="h264":
                print("h264 video")
                # vid.set(vid.get(cv2.CAP_PROP_FOURCC), vid.get(cv2.CV_FOURCC('H', '2', '6', '4')))
                st.session_state.max_frame = 50
            elif st.session_state.image_input:
                st.session_state.max_frame = 1
            else:
                st.session_state.max_frame = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
                # st.session_state.max_frame = 50

            st.session_state.input_width , st.session_state.input_height = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH)),int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
            st.session_state.update_params_from_input_file = False
            # st.session_state.src_crop_width_range, st.session_state.src_crop_height_range = [0, st.session_state.input_width] , [0, st.session_state.input_height]
            # st.session_state.dst_crop_width_range, st.session_state.dst_crop_height_range = [0, st.session_state.input_width] , [0, st.session_state.input_height]
            # st.session_state.src_crop = "0:0:" + str(st.session_state.input_width) + ":" + str(st.session_state.input_height)
            # st.session_state.dst_crop = "0:0:" + str(st.session_state.input_width) + ":" + str(st.session_state.input_height)
            # st.session_state.caps_width , st.session_state.caps_height = st.session_state.input_width , st.session_state.input_height

    def update_input_file(self):
        if st.session_state.file_uploader is not None:
            st.session_state.file_uploaded = True
            st.session_state.update_params_from_input_file = True

        else:
            st.session_state.file_uploaded = False
            st.session_state.update_params_from_input_file = False
    ##################################################################################################################

    ##################################################################################################################
    ##########  VideoTestSrc  ########################################################################################
    def videotestsrc_params(self):
        st.session_state.pattern = 18
        st.session_state.flip = False
        st.session_state.motion = 0
        st.session_state.animation_mode = 0

    def videotestsrc_controls(self):
        self.pattern_option = ["smpte", "snow", "black", "white", "red", "green", "blue", "checkers-1", "checkers-2", "checkers-4", "checkers-8", "circular", "blink", "smpte75", "zone-plate", "gamut", "chroma-zone-plate", "solid-color", "ball", "smpte100", "bar", "pinwheel", "spokes", "gradient", "colors"]
        st.session_state.pattern_val = self.pattern_option[st.session_state.pattern]
        st.selectbox("Test Pattern", self.pattern_option,key="pattern_val",index=st.session_state.pattern,on_change=self.update_pattern)

        col1,col2,col3,col4 = st.columns(4)
        self.motion_options = ["wavy", "sweep", "hsweep"]
        self.animation_mode_options = ["frames", "wall-time", "running-time"]
        st.session_state.motion_val = self.motion_options[st.session_state.motion]
        col1.selectbox("Motion method", self.motion_options,key="motion_val",index=st.session_state.motion,on_change=self.update_motion,disabled=(st.session_state.pattern != 18))
        st.session_state.animation_mode_val = self.animation_mode_options[st.session_state.animation_mode]
        col2.selectbox("Animation mode", self.animation_mode_options,key="animation_mode_val",index=st.session_state.animation_mode,on_change=self.update_animation,disabled=(st.session_state.pattern != 18))
        col3.checkbox("Invert colors every second",key="flip_val",value=st.session_state.flip,on_change=self.update_flip,disabled=(st.session_state.pattern != 18))

    def update_pattern(self):
        st.session_state.pattern = self.pattern_option.index(st.session_state.pattern_val)
        element = self.pipeline.get_by_name("videotestsrc")
        element.set_property("pattern", st.session_state.pattern)
        if st.session_state.pattern == 18:
            element.set_property("flip", st.session_state.flip)
            element.set_property("motion", st.session_state.motion)
            element.set_property("animation-mode", st.session_state.animation_mode)
        print(f"INFO: Pattern -->{st.session_state.pattern_val} ({st.session_state.pattern})")

    def update_flip(self):
        st.session_state.flip = st.session_state.flip_val
        element = self.pipeline.get_by_name("videotestsrc")
        element.set_property("flip", st.session_state.flip)
        print(f"INFO: Flip -->{st.session_state.flip_val} ({st.session_state.flip})")

    def update_motion(self):
        st.session_state.motion = self.motion_options.index(st.session_state.motion_val)
        element = self.pipeline.get_by_name("videotestsrc")
        element.set_property("motion", st.session_state.motion)
        print(f"INFO: Motion --> {st.session_state.motion_val} ({st.session_state.motion})")

    def update_animation(self):
        st.session_state.animation_mode = self.animation_mode_options.index(st.session_state.animation_mode_val)
        element = self.pipeline.get_by_name("videotestsrc")
        element.set_property("animation-mode", st.session_state.animation_mode)
        print(f"INFO: Animation Mode -->{st.session_state.animation_mode_val} ({st.session_state.animation_mode})")
    ##################################################################################################################


class Pipeline(GStreamerPipeline):
    def __init__(self):
        super().__init__()

    ##################################################################################################################
    ########## Creating Specific Pipeline ############################################################################
    def create_pipeline(self):
        # Overriding base class create_pipeline to initialize the pipeline 
        super().create_pipeline()

        # VideotestSrc is used as input source
        if st.session_state.input_method == "VideoTestSrc":
            src = self.elements.videotestsrc(st.session_state.pattern,st.session_state.flip,st.session_state.motion,st.session_state.animation_mode)

        # FileSrc is used as input source
        if st.session_state.input_method == "FileSrc":
            src = self.elements.read_input(input_file="input/"+st.session_state.input_name, width=st.session_state.input_width, height=st.session_state.input_height)

        vidconv = self.elements.videoconvert(src)
        vidconv = self.elements.videoconvert(vidconv)
        tee = self.elements.tee(vidconv)

        if st.session_state.appsink_enabled:
            queue = self.elements.queue(tee)
            queue = self.elements.capsfilter(queue, format="I420")
            self.elements.appsink(queue)

        if st.session_state.filesink_enabled:
            # Check if output directory exists if not create one
            if not os.path.exists("output"):
                os.makedirs("output")

            queue = self.elements.queue(tee)
            self.elements.write_output(queue, output_file=f"{st.session_state.username}_output", file_ext=st.session_state.out_ext)

        if st.session_state.autovideosink_enabled:
            queue = self.elements.queue(tee)
            self.elements.autovideosink(queue,)
    ##################################################################################################################
    def start(self):
        self.create_pipeline()
        super().start()

    ##################################################################################################################
    ##########  Pipeline Input Sinks  ################################################################################
    def default_input_params(self):
        st.session_state.input_method = "VideoTestSrc"
        self.videotestsrc_params()
        self.default_input_file_params()

    def input_controls(self):
        input = st.expander("Input Methods",expanded=True)
        with input:
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px; border: 1px solid grey;'>", unsafe_allow_html=True)
            self.input_method_list =["VideoTestSrc", "FileSrc"]
            selected_option = st.radio(" ", self.input_method_list, key="input_method_val", index=self.input_method_list.index(st.session_state.input_method), label_visibility="collapsed", horizontal=True, on_change=self.update_input_method,disabled=(st.session_state.status == "play"))
            if selected_option == "VideoTestSrc":
                self.videotestsrc_controls()
            elif selected_option == "FileSrc":
                self.input_file_control()

    def update_input_method(self):
        st.session_state.input_method = st.session_state.input_method_val
        print(f"INFO: Input Method -->{st.session_state.input_method_val} ({st.session_state.input_method})")
    ##################################################################################################################

    ##################################################################################################################
    ##########  Pipeline Output Sinks  ###############################################################################
    def default_output_params(self):
        st.session_state.appsink_enabled = True
        st.session_state.filesink_enabled = True
        st.session_state.autovideosink_enabled = False

    def output_controls(self):
        output = st.expander("Output Methods",expanded=True)
        with output:
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px; border: 1px solid grey;'>", unsafe_allow_html=True)
            col1,col2,col3 = st.columns(3)
            col1.checkbox("Appsink",key="appsink_val",value=st.session_state.appsink_enabled,help="display the live frames on browser",on_change=self.update_appsink,disabled=(st.session_state.status == "play"))
            col2.checkbox("Filesink",key="filesink_val",value=st.session_state.filesink_enabled,help="save the created video",on_change=self.update_filesink,disabled=(st.session_state.status == "play"))
            col3.checkbox("AutoVideoSink",key="autovideosink_val",value=st.session_state.autovideosink_enabled,help="display the live frames on system",on_change=self.update_autovideosink,disabled=(st.session_state.status == "play"))

    def update_appsink(self):
        st.session_state.appsink_enabled = st.session_state.appsink_val
        print(f"INFO: Appsink Enabled -->{st.session_state.appsink_val} ({st.session_state.appsink_enabled})")

    def update_filesink(self):
        st.session_state.filesink_enabled = st.session_state.filesink_val
        print(f"INFO: Filesink Enabled -->{st.session_state.filesink_val} ({st.session_state.filesink_enabled})")

    def update_autovideosink(self):
        st.session_state.autovideosink_enabled = st.session_state.autovideosink_val
        print(f"INFO: AutoVideoSink Enabled -->{st.session_state.autovideosink_val} ({st.session_state.autovideosink_enabled})")
    ##################################################################################################################


class TestPipeline(GStreamerPipeline):
    def __init__(self):
        super().__init__()

    def create_pipeline(self):
        # Overriding base class create_pipeline to initialize the pipeline 
        super().create_pipeline()

        # Using videotestsrc
        # src = self.elements.videotestsrc()

        src = self.elements.read_input(input_file="input/3.h264")
        st.session_state.input_ext = "h264"
        st.session_state.out_ext = "mp4"

        # src = self.elements.read_input(input_file="input/sample_1080p_h264_small.mp4")
        # src = self.elements.read_input(input_file="input/sample_1080p_h264.mp4")


        # src = self.elements.read_input(input_file="input/1.PNG")
        # st.session_state.input_ext ="png"
        # st.session_state.image_input = True

        # src = self.elements.read_input(input_file="input/team.jpg")
        # st.session_state.input_ext ="jpg"
        # st.session_state.image_input = True

        vidconv = self.elements.videoconvert(src)
        tee = self.elements.tee(vidconv)

        if st.session_state.appsink_enabled:
            queue= self.elements.queue(tee)
            queue = self.elements.capsfilter(queue, format="I420")
            self.elements.appsink(queue)

        if st.session_state.filesink_enabled:
            # Check if output directory exists if not create one
            if not os.path.exists("output"):
                os.makedirs("output")

            queue = self.elements.queue(tee)
            self.elements.write_output(queue, output_file=f"{st.session_state.username}_output", file_ext=st.session_state.out_ext)


        if st.session_state.autovideosink_enabled:
            queue= self.elements.queue(tee)
            self.elements.autovideosink(queue)

    def start(self):
        self.create_pipeline()
        super().start()


    ##################################################################################################################
    ##########  Pipeline Input Sinks  ################################################################################
    def default_input_params(self):
        st.session_state.input_ext = "mp4"
        st.session_state.out_ext = "mp4"
        st.session_state.image_input = False
        st.session_state.max_frame = 1000

    def input_controls(self):
        pass
    ##################################################################################################################


    ##################################################################################################################
    ##########  Pipeline Output Sinks  ###############################################################################
    def default_output_params(self):
        st.session_state.appsink_enabled = True
        st.session_state.filesink_enabled = True
        st.session_state.autovideosink_enabled = False

    def output_controls(self):
        output = st.expander("Output Methods",expanded=True)
        with output:
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px; border: 1px solid grey;'>", unsafe_allow_html=True)
            col1,col2,col3 = st.columns(3)
            col1.checkbox("Appsink",key="appsink_val",value=st.session_state.appsink_enabled,help="display the live frames on browser",on_change=self.update_appsink,disabled=(st.session_state.status == "play"))
            col2.checkbox("Filesink",key="filesink_val",value=st.session_state.filesink_enabled,help="save the created video",on_change=self.update_filesink,disabled=(st.session_state.status == "play"))
            col3.checkbox("AutoVideoSink",key="autovideosink_val",value=st.session_state.autovideosink_enabled,help="display the live frames on system",on_change=self.update_autovideosink,disabled=(st.session_state.status == "play"))

    def update_appsink(self):
        st.session_state.appsink_enabled = st.session_state.appsink_val
        print(f"INFO: Appsink Enabled -->{st.session_state.appsink_val} ({st.session_state.appsink_enabled})")

    def update_filesink(self):
        st.session_state.filesink_enabled = st.session_state.filesink_val
        print(f"INFO: Filesink Enabled -->{st.session_state.filesink_val} ({st.session_state.filesink_enabled})")

    def update_autovideosink(self):
        st.session_state.autovideosink_enabled = st.session_state.autovideosink_val
        print(f"INFO: AutoVideoSink Enabled -->{st.session_state.autovideosink_val} ({st.session_state.autovideosink_enabled})")
    ##################################################################################################################
