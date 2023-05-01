import streamlit as st
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import threading
import time


class GStreamerThread(threading.Thread):
    def __init__(self, pipeline):
        threading.Thread.__init__(self)
        self.pipeline = pipeline

    def run(self):
        # Start the pipeline
        self.pipeline.set_state(Gst.State.PLAYING)
        # Run the pipeline
        bus = self.pipeline.get_bus()
        msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)
        # Stop the pipeline
        self.pipeline.set_state(Gst.State.NULL)

    def stop(self):
        # Stop the pipeline
        self.pipeline.set_state(Gst.State.NULL)

    def pause(self):
        # Pause the pipeline
        self.pipeline.set_state(Gst.State.PAUSED)

class VideoPlayer:
    def __init__(self):
        # Initialize GStreamer
        Gst.init(None)

        # Define the GStreamer pipeline
        self.pipeline_str = """videotestsrc pattern="ball" ! autovideosink"""
        self.pipeline = Gst.parse_launch(self.pipeline_str.replace("gst-launch-1.0", ""))
        if "status" not in st.session_state:
            st.session_state.status = "🔴"

        #create player layout
        self.create_player()

        # Use SessionState to persist the pipeline state across runs of the app
        self.session_state = st.session_state.setdefault("pipeline", {"pipeline": self.pipeline}) 

        # Define the GStreamer thread
        self.gst_thread = GStreamerThread(self.session_state["pipeline"])

    def start(self):
        flag = True

        # if pipeline is stoped then create new pipeline with current pipeline string
        if self.session_state["pipeline"].get_state(1)[1] == Gst.State.NULL:
            flag = self.create_pipeline(self.pipeline_str)

        if flag:
            # Start the pipeline
            self.session_state["pipeline"].set_state(Gst.State.PLAYING)
            self.gst_thread.start()
            st.session_state.status = "🟢"

    def pause(self):
        flag = True

        # if pipeline is stoped then create new pipeline with current pipeline string
        if self.session_state["pipeline"].get_state(1)[1] == Gst.State.NULL:
            flag = self.create_pipeline(self.pipeline_str)

        if flag:
            # Pause the pipeline
            self.session_state["pipeline"].set_state(Gst.State.PAUSED)
            self.gst_thread.pause()
            st.session_state.status = "🟡"

    def stop(self):
        # Stop the pipeline when the stop button is clicked
        self.session_state["pipeline"].set_state(Gst.State.NULL)
        self.gst_thread.stop()
        st.session_state.status = "🔴"

    def restart(self):
        #stop the current pipeline
        self.stop()

        # create new pipeline with current pipeline string
        if self.create_pipeline(self.pipeline_str):
            #start the new pipeline
            self.start()

    def create_pipeline(self,pipeline_str):
        try:
            # Define the GStreamer pipeline
            self.pipeline_str = pipeline_str
            self.pipeline = Gst.parse_launch(self.pipeline_str.replace("gst-launch-1.0 ", ""))

            # Set the new pipeline as the value of the "pipeline" key in the session state dictionary
            self.session_state["pipeline"] = self.pipeline
            
            # Create a new GStreamer thread with the new pipeline
            self.gst_thread = GStreamerThread(self.session_state["pipeline"])
            return True
        except Exception as e:
            st.error(str(e))
            return False

    def update_pipeline(self):
        #update the pipeline string
        self.pipeline_str = st.session_state.input_pipeline.strip()

        # restart the pipeline with new pipeline string
        self.restart()

    def create_player(self):
        # Define the Streamlit app
        st.title(st.session_state.status+" Gst-Launch App "+st.session_state.status)

        #input the gst-pipeline string 
        self.pipeline_str = st.text_input(' ',value=self.pipeline_str,key="input_pipeline",on_change=self.update_pipeline,label_visibility="collapsed")

        # Define the start and stop buttons
        col1,col2,col3,col4 = st.columns(4)
        start_button = col1.button("Start",on_click=self.start)
        pause_button = col2.button("Pause",on_click=self.pause)
        stop_button = col3.button("Stop",on_click=self.stop)
        restart_button = col4.button("Restart",on_click=self.restart)


if __name__ == "__main__":
    player = VideoPlayer()

