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
import threading
from elements import GstreamerElements

class GStreamerPipeline:
    def __init__(self):
        # creating the pipeline
        self.default_params()

    def default_params(self):
        """
        This method should be overridden by subclasses to spacify the default params of elements.
        """
        pass

    def create_pipeline(self):
        """
        This method should be overridden by subclasses to create the specific pipeline.
        Use self.element to add the new element in the pipeline
        super().create_pipeline() needs to be called in overriden code to inintialize the pipeline
        """
        # Initialize GStreamer
        Gst.init(None)

        # Define the GStreamer pipeline
        self.pipeline = Gst.Pipeline()
        self.loop = GLib.MainLoop()
        main_loop_thread = threading.Thread(target=self.loop.run)
        main_loop_thread.start()

        # Class containing elements of gstreamer
        self.elements = GstreamerElements(self.pipeline)

        # Add a signal watch to the bus
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.bus_message, self.pipeline, self.loop)

    def start(self):
        """
        This method is used to change the pipeline state to PLAYING
        """
        self.pipeline.set_state(Gst.State.PLAYING)

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
        return self.elements.buffer_queue.get()

    def bus_message(self, bus, message, pipeline, loop):
        """
        This mehtod dandles bus messages
        """
        bus_msg_enable= False
        if message.type == Gst.MessageType.EOS:
            pipeline.set_state(Gst.State.NULL)
            loop.quit()
            if bus_msg_enable:
                print("End of Stream")

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
            if bus_msg_enable:
                print("Tag: %s" % tag_list.to_string())

        elif message.type == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            if bus_msg_enable:
                print("Warning: %s: %s\n" % (err, debug))
