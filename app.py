import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import streamlit as st
import os
import os, time, threading
from streamlit.runtime.scriptrunner import add_script_run_ctx
from gstreamer_utils import *
import random
import string

class GstreamerPlayer:
    def __init__(self):
         # Initialize GStreamer
        Gst.init(None)

        # Define the GStreamer pipeline status
        if "status" not in st.session_state:
            st.session_state.status = "🔴"

        # Check if output directory exists if not create one
        if not os.path.exists("output"):
            os.makedirs("output")

        # Define GStreamer pipeline need to update or not
        # Also create/(update with default) the pipeline for the 1st time
        if "update_pipeline_enable" not in st.session_state:
            st.session_state.update_pipeline_enable = True
            st.session_state.lock = lock
            st.session_state.output_available = False
            # self.clear_space()
            self.update_pipeline()

        # Define pipeline elements default values
        if "pattern" not in st.session_state:
            st.session_state.pattern = "ball"

        if "flip" not in st.session_state:
            st.session_state.flip = False

        if "motion" not in st.session_state:
            st.session_state.motion = "wavy"

        if "animation_mode" not in st.session_state:
            st.session_state.animation_mode = "frames"

    def consol(self):
        # Define the Streamlit app
        st.title(st.session_state.status+" Gstreamer Test App "+st.session_state.status)

        col1,col2,col3 = st.columns(3)
        test_src_options = ["smpte", "snow", "ball", "black", "white", "red", "green", "blue", "checkers-1", "checkers-2", "checkers-4", "checkers-8", "circular", "blink", "zone-plate", "gamut", "chroma-zone-plate", "solid-color"]
        motion_options = ["wavy", "sweep", "hsweep"]
        animation_mode_options = ["frames", "wall-time", "running-time"]

        # Define the start and stop buttons
        col1,col2,col3 = st.columns(3)
        col1.button("Start",on_click=self.start)
        col2.button("Stop",on_click=self.stop)
        col3.button("Restart",on_click=self.restart)

        st.selectbox("Select video test source", test_src_options,key="pattern_val",index=test_src_options.index(st.session_state.pattern),on_change=self.update_pattern)
        
        if st.session_state.pattern_val == "ball":
            col1,col2,col3 = st.columns(3)
            col1.selectbox("Select motion mehtod", motion_options,key="motion_val",index=motion_options.index(st.session_state.motion),on_change=self.update_motion)
            col2.selectbox("Select animation mode", animation_mode_options,key="animation_mode_val",index=animation_mode_options.index(st.session_state.animation_mode),on_change=self.update_animation)
            col3.checkbox("Invert colors every second",key="flip_val",value=st.session_state.flip,on_change=self.update_flip)

        self.display_output()

    def display_output(self):
        with st.sidebar:
            output = st.expander("📷",expanded=True)
            with output:
                window = st.empty()
                if st.session_state.status == "🟢":
                    #initial image window
                    try:
                        while True:
                            window.image(f"output/{st.session_state.username}_output.jpg",use_column_width="always")
                            time.sleep(.2)
                            st.experimental_rerun()

                    except Exception as e:
                        st.experimental_rerun()
                elif st.session_state.output_available:
                    # Load the video from file
                    video = open(f"output/{st.session_state.username}_output.mp4", 'rb')
                    video_bytes = video.read()

                    # Display the video in Streamlit
                    window.video(video_bytes)

                    # Download button
                    col1 , col2 , col3= st.columns(3)
                    with open(f"output/{st.session_state.username}_output.mp4", "rb") as file:
                        btn = col2.download_button(
                                label="Download 🔽",
                                data=file,
                                file_name="output.mp4")

    def save_video(self):
        if os.path.isfile(f"output/{st.session_state.username}_output.mp4"):
            print("Saving video....")
            st.session_state.output_available = True

    def clear_space(self):
        directory = 'output/'

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)

    def update_pattern(self):
        st.session_state.pattern = st.session_state.pattern_val
        element = st.session_state.pipeline.get_by_name("source")
        element.set_property("pattern", st.session_state.pattern_val)

    def update_flip(self):
        st.session_state.flip = st.session_state.flip_val
        element = st.session_state.pipeline.get_by_name("source")
        element.set_property("flip", st.session_state.flip_val)

    def update_motion(self):
        st.session_state.motion = st.session_state.motion_val
        element = st.session_state.pipeline.get_by_name("source")
        element.set_property("motion", st.session_state.motion_val)

    def update_animation(self):
        st.session_state.animation_mode = st.session_state.animation_mode_val
        element = st.session_state.pipeline.get_by_name("source")
        element.set_property("animation-mode", st.session_state.animation_mode_val)

    def update_pipeline(self):
        if "update_pipeline_enable" in st.session_state and st.session_state.update_pipeline_enable:
            try:
                # Define the GStreamer pipeline
                st.session_state.pipeline = Gst.Pipeline()
                st.session_state.loop = GLib.MainLoop()
                main_loop_thread = threading.Thread(target=st.session_state.loop.run)
                main_loop_thread.start()

                # Create a file source element
                source = Gst.ElementFactory.make("videotestsrc", "source")
                source.set_property("pattern","ball")
                st.session_state.pipeline.add(source)

                # Create a tee element
                tee = Gst.ElementFactory.make("tee", "tee")
                st.session_state.pipeline.add(tee)
                source.link(tee)

                tee1 = add_queue(st.session_state.pipeline,tee)
                tee2 = add_queue(st.session_state.pipeline,tee)

                # Create an appsink element and link it to the tee
                appsink = Gst.ElementFactory.make("appsink", "sink")
                st.session_state.pipeline.add(appsink)
                tee1.link(appsink)

                # Set the appsink to emit signals when data is available
                appsink.set_property("emit-signals", True)
                appsink.set_property("drop", True)

                # Start the background thread to generate image data
                generation_thread = threading.Thread(target=appsink_buffer, args=(appsink,st.session_state.username))
                add_script_run_ctx(generation_thread)
                generation_thread.start()

                # Connect the callback function to the appsink's "new-sample" signal
                appsink.connect("new-sample", appsink_buffer,st.session_state.username)

                output_parser(st.session_state.pipeline,tee2,output_file=f"output/{st.session_state.username}_output.mp4",async_mode=False)

                # # Create an autovideosink element and link it to the tee
                # tee3 = add_queue(st.session_state.pipeline,tee,leaky=True)
                # autovideosink = Gst.ElementFactory.make('autovideosink', 'autovideosink')
                # st.session_state.pipeline.add(autovideosink)
                # autovideosink.set_property("sync", False)
                # tee3.link(autovideosink)
                # add_queue(st.session_state.pipeline,autovideosink)

                # Add a signal watch to the bus
                bus = st.session_state.pipeline.get_bus()
                bus.add_signal_watch()
                bus.connect("message", bus_message, st.session_state.pipeline, st.session_state.loop)

            except Exception as e:
                st.error(str(e))

            # Disable the pipeline updation until next update call
            st.session_state.update_pipeline = False

    def start(self):
        with st.session_state.lock:
            # Start the pipeline
            st.session_state.status = "🟢"
            time.sleep(.2)
            st.session_state.pipeline.set_state(Gst.State.PLAYING)
            st.session_state.output_available = False
            time.sleep(.2)

    def stop(self):
        with st.session_state.lock:
            # Stop the pipeline when the stop button is clicked
            if st.session_state.status != "🔴":
                st.session_state.status = "🔴"
                time.sleep(.2)
                st.session_state.pipeline.set_state(Gst.State.PLAYING)
                st.session_state.pipeline.send_event(Gst.Event.new_eos())
                time.sleep(.2)
                self.save_video()
        

    def restart(self):
        with st.session_state.lock:
            # Stop the current pipeline
            st.session_state.pipeline.set_state(Gst.State.NULL)
            st.session_state.loop.quit()

            # Start the current pipeline
            st.session_state.status = "🟢"
            time.sleep(.2)
            st.session_state.pipeline.set_state(Gst.State.PLAYING)
            st.session_state.output_available = False
            time.sleep(.2)

# Lock to access shared item
lock = threading.Lock()

def get_username():
    # Check if the user has a UUID stored in their browser's cookies
    username = st.session_state.get('username')
    if username is not None:
        return username
    
    # If the user does not have a UUID, generate one and store it in their browser's cookies
    username = ''.join(random.choice(string.ascii_lowercase) for i in range(4))
    st.session_state['username'] = username
    return username


if __name__ == "__main__":
    username = get_username()
    player = GstreamerPlayer()
    player.consol()
