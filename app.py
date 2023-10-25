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
from pipeline import GStreamerPipeline
import random, time, string, os

# Hide the header and footer
st.markdown(""" <style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style> """, unsafe_allow_html=True)

class Pipeline(GStreamerPipeline):
    def __init__(self):
        super().__init__()

    def create_pipeline(self):
        # Overriding base class create_pipeline to inintialize the pipeline 
        super().create_pipeline()

        # Creating specific pipeline
        src = self.elements.videotestsrc(st.session_state.pattern,st.session_state.flip,st.session_state.motion,st.session_state.animation_mode)
        vidconv = self.elements.videoconvert(src)
        vidconv = self.elements.capsfilter(vidconv,format="I420")
        tee = self.elements.tee(vidconv)

        if st.session_state.appsink_enabled:
            queue= self.elements.queue(tee)
            self.elements.appsink(queue)

        if st.session_state.filesink_enabled:
            queue= self.elements.queue(tee)
            self.elements.save_output(queue, output_file=f"{st.session_state.username}_output", file_ext="mp4")

        if st.session_state.autovideosink_enabled:
            queue= self.elements.queue(tee)
            self.elements.autovideosink(queue, sync=False)

    def start(self):
        self.create_pipeline()
        super().start()

    def default_params(self):
        self.videotestsrc_params()
        self.default_output_pramas()

    def controls(self,):
        self.videotestsrc_controls()
        self.output_controls()

    ##################################################################################################################
    ##########  Vdeotestsrc  #########################################################################################
    def videotestsrc_params(self):
        st.session_state.pattern = 18
        st.session_state.flip = False
        st.session_state.motion = 0
        st.session_state.animation_mode = 0

    def videotestsrc_controls(self):
        videotestsrc = st.expander("Sample Input Video Source [Videotestsrc]",expanded=True)
        with videotestsrc:
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px; border: 1px solid grey;'>", unsafe_allow_html=True)

            self.pattern_option = ["smpte", "snow", "black", "white", "red", "green", "blue", "checkers-1", "checkers-2", "checkers-4", "checkers-8", "circular", "blink", "smpte75", "zone-plate", "gamut", "chroma-zone-plate", "solid-color", "ball", "smpte100", "bar", "pinwheel", "spokes", "gradient", "colors"]
            st.session_state.pattern_val = self.pattern_option[st.session_state.pattern]
            st.selectbox("Select video test source", self.pattern_option,key="pattern_val",index=st.session_state.pattern,on_change=self.update_pattern)

            col1,col2,col3,col4 = st.columns(4)
            self.motion_options = ["wavy", "sweep", "hsweep"]
            self.animation_mode_options = ["frames", "wall-time", "running-time"]
            st.session_state.motion_val = self.motion_options[st.session_state.motion]
            col1.selectbox("Select motion mehtod", self.motion_options,key="motion_val",index=st.session_state.motion,on_change=self.update_motion,disabled=(st.session_state.pattern != 18))
            st.session_state.animation_mode_val = self.animation_mode_options[st.session_state.animation_mode]
            col2.selectbox("Select animation mode", self.animation_mode_options,key="animation_mode_val",index=st.session_state.animation_mode,on_change=self.update_animation,disabled=(st.session_state.pattern != 18))
            col3.checkbox("Invert colors every second",key="flip_val",value=st.session_state.flip,on_change=self.update_flip,disabled=(st.session_state.pattern != 18))

    def update_pattern(self):
        st.session_state.pattern = self.pattern_option.index(st.session_state.pattern_val)
        element = self.pipeline.get_by_name("videotestsrc")
        element.set_property("pattern", st.session_state.pattern)
        if st.session_state.pattern == 18:
            element.set_property("flip", st.session_state.flip)
            element.set_property("motion", st.session_state.motion)
            element.set_property("animation-mode", st.session_state.animation_mode)
        print(f"Updated pattern -->{st.session_state.pattern_val} ({st.session_state.pattern})")

    def update_flip(self):
        st.session_state.flip = st.session_state.flip_val
        element = self.pipeline.get_by_name("videotestsrc")
        element.set_property("flip", st.session_state.flip)
        print(f"Updated flip -->{st.session_state.flip_val} ({st.session_state.flip})")

    def update_motion(self):
        st.session_state.motion = self.motion_options.index(st.session_state.motion_val)
        element = self.pipeline.get_by_name("videotestsrc")
        element.set_property("motion", st.session_state.motion)
        print(f"Updated motion --> {st.session_state.motion_val} ({st.session_state.motion})")

    def update_animation(self):
        st.session_state.animation_mode = self.animation_mode_options.index(st.session_state.animation_mode_val)
        element = self.pipeline.get_by_name("videotestsrc")
        element.set_property("animation-mode", st.session_state.animation_mode)
        print(f"Updated animation-mode -->{st.session_state.animation_mode_val} ({st.session_state.animation_mode})")
    ##################################################################################################################

    ##################################################################################################################
    ##########  Pipeline Output Sinks  ###############################################################################
    def default_output_pramas(self):
        st.session_state.appsink_enabled = True
        st.session_state.filesink_enabled = False
        st.session_state.autovideosink_enabled = False

    def output_controls(self):
        output = st.expander("Different Ouputs Methods",expanded=True)
        with output:
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px; border: 1px solid grey;'>", unsafe_allow_html=True)
            col1,col2,col3 = st.columns(3)
            col1.checkbox("Appsink",key="appsink_val",value=st.session_state.appsink_enabled,help="display the live frames on browser",on_change=self.update_appsink,disabled=(st.session_state.status == "play"))
            col2.checkbox("Filesink",key="filesink_val",value=st.session_state.filesink_enabled,help="save the created video",on_change=self.update_filesink,disabled=(st.session_state.status == "play"))
            col3.checkbox("AutoVideoSink",key="autovideosink_val",value=st.session_state.autovideosink_enabled,help="display the live frames on system",on_change=self.update_autovideosink,disabled=(st.session_state.status == "play"))

    def update_appsink(self):
        st.session_state.appsink_enabled = st.session_state.appsink_val
        print(f"Updated Appsink -->{st.session_state.appsink_val} ({st.session_state.appsink_enabled})")

    def update_filesink(self):
        st.session_state.filesink_enabled = st.session_state.filesink_val
        print(f"Updated Filesink -->{st.session_state.filesink_val} ({st.session_state.filesink_enabled})")

    def update_autovideosink(self):
        st.session_state.autovideosink_enabled = st.session_state.autovideosink_val
        print(f"Updated AutoVideoSink -->{st.session_state.autovideosink_val} ({st.session_state.autovideosink_enabled})")
    ##################################################################################################################


class Player:
    def __init__(self):
        # __init__ is not called once then set the sesion pramas
        if "pipeline" not in st.session_state:
            self.create_user()
            
            # Define the GStreamer pipeline status to stop
            st.session_state.status = "stop"

            # Creating pipeline object
            st.session_state.pipeline = Pipeline()

            # Check if output directory exists if not create one
            if not os.path.exists("output"):
                os.makedirs("output")

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
            st.session_state.pipeline.controls()

            # Define the start and stop buttons
            col1,col2,col3 = st.columns(3)
            col1.button("Start",on_click=self.start)
            col2.button("Stop",on_click=self.stop)
            col3.button("Reset",on_click=self.default_params,disabled=(st.session_state.status == "play"))

            # Debug session state
            # st.write(st.session_state)

            # Display the processed output
            with st.sidebar:
                output = st.expander("Output 📷",expanded=True)
                with output:
                    #initial image window
                    window = st.empty()
                    # Display the saved ouput when pipeline is stoped
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
                    elif st.session_state.status == "play":
                        while True:
                            image = st.session_state.pipeline.fetch_buffer()
                            window.image(image,use_column_width="always")
        except Exception as e:  
            print(e)

    def start(self):
        # Stop the already running pipeline
        if st.session_state.status == "play":
            self.stop()
        # Start the pipeline
        st.session_state.status = "play"
        st.session_state.output_available = False
        st.session_state.pipeline.start()

    def stop(self):
        # Stop the pipeline when the stop button is clicked
        if st.session_state.status != "stop":
            st.session_state.status = "stop"
            st.session_state.pipeline.stop()
            time.sleep(.1)
            if st.session_state.filesink_enabled and os.path.isfile(f"output/{st.session_state.username}_output.mp4"):
                st.session_state.output_available = True


if __name__ == "__main__":
    player = Player()  
    player.consol()
