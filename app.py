##################################################################################################################
# Author: Vishal Kumar
# Email: vishalkmr01123@gmail.com
#
# The file uses the Streamlit library to create a web-based user interface for the Gstreamer pipeline.
# It includes the Pipeline class, which extends the GStreamerPipeline class, and the Player class, which manages the pipeline.
# The Pipeline class is used to create a specific Gstreamer pipeline, and the Player class is used to start, stop, and reset the pipeline.
# The file also includes controls for the pipeline parameters and output methods, and it displays the processed video output.
##################################################################################################################


import streamlit as st
from pipeline import Pipeline , TestPipeline
import random, time, string, os
from PIL import Image
import glob
import os, time, threading
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib
from streamlit.runtime.scriptrunner import add_script_run_ctx
# Hide the header and footer
st.markdown(""" <style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style> """, unsafe_allow_html=True)

class Player:
    def __init__(self):
        # __init__ is not called once then set the session prams
        if "pipeline" not in st.session_state:
            self.create_user()
            
            # Define the GStreamer pipeline status to stop
            st.session_state.status = "stop"

            # Creating pipeline object
            st.session_state.pipeline = Pipeline()
            st.session_state.output_available = False

            self.default_params()

    def default_params(self):
        st.session_state.pipeline.default_params()
        st.session_state.output_available = False

    def create_user(self):
        # Check if the user has a UUID stored in their browser's cookies
        self.username = st.session_state.get('username')
        if self.username is not None:
            return
        
        # If the user does not have a UUID, generate one and store it in their browser's cookies
        self.username = ''.join(random.choice(string.ascii_lowercase) for i in range(4))
        st.session_state.username = self.username

    def check_eos(self):
        while True:
            time.sleep(.1)
            if st.session_state.status == "play":
                if st.session_state.pipeline.eos_occurred:
                    print("######################################### EOS FOund .....")
                    self.stop()
                    print("--> check_eos stop done")
                    break
                else:
                    print("######################################### Runiing .....")
                
            else:
                print("#########################################Stoped .....")

    def display_output(self):
        # Display the processed output
        
        with st.sidebar:
            output = st.expander("Output 📷",expanded=True)
            with output:
                #initial image window
                window = st.empty()
                txt1 = st.empty()
                txt2 = st.empty()
                txt3 = st.empty()
                # Display the saved output when pipeline is stope
                if st.session_state.output_available:
                    # Load the image from file
                    if st.session_state.image_input:
                        image = Image.open(f"output/{st.session_state.username}_output.{st.session_state.out_ext}")
                        window.image(image)
                    
                    # Load the video from file
                    else:
                        video = open(f"output/{st.session_state.username}_output.{st.session_state.out_ext}", 'rb')
                        video_bytes = video.read()

                        window.video(video_bytes)

                    print(f"INFO: Output File output/{st.session_state.username}_output.{st.session_state.input_ext} is Uploaded")
                    # Download button
                    col1 , col2 , col3= st.columns(3)
                    with open(f"output/{st.session_state.username}_output.{st.session_state.out_ext}", "rb") as file:
                        btn = col2.download_button(
                                label="Download 🔽",
                                data=file,
                                file_name=f"output.{st.session_state.out_ext}")
                        
                # Display the intermediate frames if pipeline is running
                elif st.session_state.status == "play":
                  while True:
                        # Get the current state of the pipeline and call stop if pipeline is NULL state
                        ret, state, _ = st.session_state.pipeline.pipeline.get_state(0)
                        if ret == Gst.StateChangeReturn.SUCCESS:
                            if Gst.Element.state_get_name(state) == "NULL":
                                self.stop()
                                st.rerun()

                        if (st.session_state.input_ext == "h264" or st.session_state.input_ext == "mp4"):
                            try:
                                txt1.text(f"\nInFrame->{st.session_state.pipeline.elements.in_frame_num} OutFrame->{st.session_state.pipeline.out_frame_num}")
                                txt2.text(f"TotalFrame->{st.session_state.max_frame}")
                                txt3.text(f"InFPS : {round(st.session_state.pipeline.elements.in_frame_num/(time.time()-st.session_state.pipeline.elements.in_time),2)}   OutFPS : {round(st.session_state.pipeline.out_frame_num/(time.time()-st.session_state.pipeline.out_time),2)}")
                                image = st.session_state.pipeline.fetch_buffer()
                                window.image(image,use_column_width="always")
                            except Exception as e:
                                pass

                        # if st.session_state.image_input:
                        #     time.sleep(1)
                        #     self.stop()
                        #     st.rerun()

                        # if (st.session_state.input_ext == "h264" or st.session_state.input_ext == "mp4"):
                        #     # Display image when eos not found or still some buffer left in queue
                        #     while (not st.session_state.pipeline.eos_occurred) or (st.session_state.pipeline.elements.in_frame_num ==1 or st.session_state.pipeline.out_frame_num < st.session_state.pipeline.elements.in_frame_num):
                        #         print("---- inside display")
                        #         txt1.text(f"\nInFrame->{st.session_state.pipeline.elements.in_frame_num} OutFrame->{st.session_state.pipeline.out_frame_num}")
                        #         txt2.text(f"TotalFrame->{st.session_state.max_frame}")
                        #         txt3.text(f"InFPS : {round(st.session_state.pipeline.elements.in_frame_num/(time.time()-st.session_state.pipeline.elements.in_time),2)}   OutFPS : {round(st.session_state.pipeline.out_frame_num/(time.time()-st.session_state.pipeline.out_time),2)}")
                        #         image = st.session_state.pipeline.fetch_buffer()
                        #         window.image(image,use_column_width="always")
                        #     else:
                        #         print("########## found eos from display ")
                        #         self.stop()
                        #         st.rerun()


    def clear_user_data(self):
        # Get a list of all files that start with 'output/{st.session_state.username}_output'
        files = glob.glob(f"output/{st.session_state.username}_output*")
        # Loop through the list and remove each file
        for file in files:
            try:
                os.remove(file)
            except OSError as e:
                print(f"Error: {file} : {e.strerror}")

    def consol(self):
        try:
            # Define the Streamlit app
            if st.session_state.status == "play":
                st.markdown("<h1 style='text-align: center; color: green;'>Streamlit-x-Gstreamer</h1>", unsafe_allow_html=True)
            elif st.session_state.status == "stop":
                st.markdown("<h1 style='text-align: center; color: red;'>Streamlit-x-Gstreamer</h1>", unsafe_allow_html=True)
            else:
                st.markdown("<h1 style='text-align: center; color: orange;'>Streamlit-x-Gstreamer</h1>", unsafe_allow_html=True)

            # Define input controls for pipeline parameters
            st.session_state.pipeline.input_controls()


            st.session_state.pipeline.output_controls()

            # Define the start and stop buttons
            col1,col2,col3 = st.columns(3)
            col1.button("Start",on_click=self.start)
            col2.button("Stop",on_click=self.stop)
            col3.button("Reset",on_click=self.default_params,disabled=(st.session_state.status == "play"))

            # Debug session state
            st.write(st.session_state)

            self.display_output()
        except Exception as e:  
            pass

    def start(self):
        # Stop the already running pipeline
        if st.session_state.status == "play":
            self.stop()
        # Start the pipeline
        st.session_state.status = "play"
        st.session_state.output_available = False
        self.clear_user_data()
        
        # self.test_thread = threading.Thread(target=self.check_eos)
        # add_script_run_ctx(self.test_thread)
        # self.test_thread.start()
        
        st.session_state.pipeline.start()

    def stop(self):
        # Stop the pipeline when the stop button is clicked
        if st.session_state.status != "stop":
            st.session_state.status = "stop"
            st.session_state.pipeline.stop()
            while True:
                if  os.path.isfile(f"output/{st.session_state.username}_output.{st.session_state.out_ext}"):
                    print(f"INFO: Output File output/{st.session_state.username}_output.{st.session_state.out_ext} is Saved")
                    st.session_state.output_available = True
                    # st.session_state.pipeline.eos_occurred = False
                    time.sleep(1)
                    break


if __name__ == "__main__":
    player = Player()  
    player.consol()
