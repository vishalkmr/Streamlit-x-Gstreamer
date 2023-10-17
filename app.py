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

# hide the header and footer
st.markdown(""" <style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style> """, unsafe_allow_html=True)
file_loop = False

class GstreamerPlayer:
    def __init__(self):
        # __init__ is not called once then set the sesion pramas
        if "init" not in st.session_state:
            # Check if output directory exists if not create one
            if not os.path.exists("output"):
                os.makedirs("output")

            # Define the GStreamer pipeline status to stop
            st.session_state.status = "🔴"

            # Define pipeline elements default values
            self.default_params()
   
           # Initialize GStreamer
            Gst.init(None)

            # Define GStreamer pipeline need to update or not
            # Also create/(update with default) the pipeline for the 1st time
            st.session_state.update_pipeline_enable = True
            st.session_state.output_available = False
            self.update_pipeline()

            # Set the init params
            st.session_state.init = True

    #################################################################################################################################
    ############################ App Consol #########################################################################################
    def consol(self):
        try:
            # Define the Streamlit app
            st.title(st.session_state.status+" Gstreamer Test App "+st.session_state.status)

            input = st.expander("Videotestsrc Params",expanded=True )
            with input:
                st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px; border: 1px solid grey;'>", unsafe_allow_html=True)
            
                self.pattern_option = ["smpte", "snow", "black", "white", "red", "green", "blue", "checkers-1", "checkers-2", "checkers-4", "checkers-8", "circular", "blink", "smpte75", "zone-plate", "gamut", "chroma-zone-plate", "solid-color", "ball", "smpte100", "bar", "pinwheel", "spokes", "gradient", "colors"]
                st.session_state.pattern_val = self.pattern_option[st.session_state.pattern]
                st.selectbox("Select video test source", self.pattern_option,key="pattern_val",index=st.session_state.pattern,on_change=self.update_pattern)
                
                col1,col2,col3 = st.columns(3)
                self.motion_options = ["wavy", "sweep", "hsweep"]
                self.animation_mode_options = ["frames", "wall-time", "running-time"]
                st.session_state.motion_val = self.motion_options[st.session_state.motion]
                col1.selectbox("Select motion mehtod", self.motion_options,key="motion_val",index=st.session_state.motion,on_change=self.update_motion,disabled=(st.session_state.pattern != 18))                
                st.session_state.animation_mode_val = self.animation_mode_options[st.session_state.animation_mode]
                col2.selectbox("Select animation mode", self.animation_mode_options,key="animation_mode_val",index=st.session_state.animation_mode,on_change=self.update_animation,disabled=(st.session_state.pattern != 18))
                col3.checkbox("Invert colors every second",key="flip_val",value=st.session_state.flip,on_change=self.update_flip,disabled=(st.session_state.pattern != 18))

            # Define the start and stop buttons
            col1,col2,col3,col4 = st.columns(4)
            col1.button("Start",on_click=self.start)
            col2.button("Stop",on_click=self.stop)
            col3.button("Restart",on_click=self.restart)
            col4.button("Reset",on_click=self.default_params,disabled=(st.session_state.status == "🟢"))

            # Debug session state
            # st.write(st.session_state)

            # Display the processed output
            with st.sidebar:
                self.display_output()

        except Exception as e:
            print(e)
    #################################################################################################################################

    #################################################################################################################################
    ############################ Pipeline & Controls ################################################################################
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
                source.set_property("pattern",st.session_state.pattern)
                if st.session_state.pattern == 18:
                    source.set_property("flip", st.session_state.flip)
                    source.set_property("motion", st.session_state.motion)
                    source.set_property("animation-mode", st.session_state.animation_mode)

                st.session_state.pipeline.add(source)

                # Create a tee element
                tee = Gst.ElementFactory.make("tee", "tee")
                st.session_state.pipeline.add(tee)
                source.link(tee)

                # Create an appsink element and link it to the tee
                tee1 = add_queue(st.session_state.pipeline,tee)
                tee1 = add_capsfilter(st.session_state.pipeline,tee1)
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

                # Save the output stream
                tee2 = add_queue(st.session_state.pipeline,tee)
                output_parser(st.session_state.pipeline,tee2,output_file=f"output/{st.session_state.username}_output",async_mode=False,ext="mp4")

                # Create an autovideosink element and link it to the tee
                tee3 = add_queue(st.session_state.pipeline,tee,leaky=True)
                autovideosink = Gst.ElementFactory.make('autovideosink', 'autovideosink')
                st.session_state.pipeline.add(autovideosink)
                autovideosink.set_property("sync", False)
                tee3.link(autovideosink)
                add_queue(st.session_state.pipeline,autovideosink)

                # Add a signal watch to the bus
                bus = st.session_state.pipeline.get_bus()
                bus.add_signal_watch()
                bus.connect("message", bus_message, st.session_state.pipeline, st.session_state.loop)

            except Exception as e:
                st.error(str(e))

            # Disable the pipeline updation until next update call
            st.session_state.update_pipeline = False

    def start(self):
        st.session_state.update_pipeline_enable = True
        st.session_state.output_available = False
        self.update_pipeline()

        # Start the pipeline
        st.session_state.status = "🟢"
        st.session_state.pipeline.set_state(Gst.State.PLAYING)
        st.session_state.output_available = False
        time.sleep(.3)

    def stop(self,already_stoped=False):
        # Stop the pipeline when the stop button is clicked
        if st.session_state.status != "🔴":
            st.session_state.status = "🔴"
            if not already_stoped:
                st.session_state.pipeline.send_event(Gst.Event.new_eos())
            time.sleep(.5)

            # Saving data
            if os.path.isfile(f"output/{st.session_state.username}_output.mp4"):
                print("Saving data....")
                st.session_state.output_available = True

    def restart(self):
        # Stop the current pipeline
        self.stop()

        # Start the current pipeline
        self.start()

    def default_params(self):
        st.session_state.pattern = 18
        st.session_state.flip = False
        st.session_state.motion = 0
        st.session_state.animation_mode = 0
    #################################################################################################################################

    #################################################################################################################################
    ###########################  VideoTestSrc Params  ###############################################################################
    def update_pattern(self):
        st.session_state.pattern = self.pattern_option.index(st.session_state.pattern_val)
        element = st.session_state.pipeline.get_by_name("source")
        element.set_property("pattern", st.session_state.pattern)
        print(f"Updated pattern -->{st.session_state.pattern_val} ({st.session_state.pattern})")

    def update_flip(self):
        st.session_state.flip = st.session_state.flip_val
        element = st.session_state.pipeline.get_by_name("source")
        element.set_property("flip", st.session_state.flip)
        print(f"Updated flip -->{st.session_state.flip_val} ({st.session_state.flip})")

    def update_motion(self):
        st.session_state.motion = self.motion_options.index(st.session_state.motion_val)
        element = st.session_state.pipeline.get_by_name("source")
        element.set_property("motion", st.session_state.motion)
        print(f"Updated motion --> {st.session_state.motion_val} ({st.session_state.motion})")

    def update_animation(self):
        st.session_state.animation_mode = self.animation_mode_options.index(st.session_state.animation_mode_val)
        element = st.session_state.pipeline.get_by_name("source")
        element.set_property("animation-mode", st.session_state.animation_mode)
        print(f"Updated animation-mode -->{st.session_state.animation_mode_val} ({st.session_state.animation_mode})")
    #################################################################################################################################

    #################################################################################################################################
    ############################ Output Display #####################################################################################
    def display_output(self):
        output = st.expander("Output 📷",expanded=True)
        with output:
            #initial image window
            window = st.empty()

            # Display the ouput video if available
            if st.session_state.output_available:
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

            # Display the intermediate frames if pipeline is running
            elif st.session_state.status == "🟢":
                while True:
                    # Get the current state of the pipeline and call stop if pipeline is NULL state
                    ret, state, _ = st.session_state.pipeline.get_state(0)
                    if ret == Gst.StateChangeReturn.SUCCESS:
                        if Gst.Element.state_get_name(state) == "NULL":
                            self.stop(already_stoped=True)
                            st.rerun()

                    try:
                        window.image(f"output/{st.session_state.username}_intermediate_output.jpg",use_column_width="always")
                        time.sleep(.2)
                        st.rerun()

                    except Exception as e:
                        st.rerun()
    #################################################################################################################################

def get_username():
    # Check if the user has a UUID stored in their browser's cookies
    username = st.session_state.get('username')
    if username is not None:
        return username
    
    # If the user does not have a UUID, generate one and store it in their browser's cookies
    username = ''.join(random.choice(string.ascii_lowercase) for i in range(4))
    st.session_state['username'] = username
    return username


# @st.cache_data
def create_player(username):
    return GstreamerPlayer()

if __name__ == "__main__":
    username =  get_username()
    player = create_player(username)
    player.consol()
