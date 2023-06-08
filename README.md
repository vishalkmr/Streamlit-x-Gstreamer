# Streamlit-x-Gstreamer
This project demonstrate a way to integrate a GStreamer video player into a Streamlit window. It leverages the power of GStreamer for video processing and rendering while utilizing the user-friendly interface of Streamlit for interactive controls. With this integration, users can easily configure video parameters, start, stop, and restart the video playback, and view the output within the Streamlit app. It simplifies the process of creating a GStreamer-based video player and makes it accessible to developers using Streamlit for their applications.


https://github.com/vishalkmr/Streamlit-x-Gstreamer/assets/20735280/a965bdad-efc6-4b26-9b96-225bbec99314


 
## Dependencies
Before running this application, make sure you have the following dependencies installed:

- Python 3
You can install Python 3 from the official [Python](https://www.python.org/downloads/) website.

- Streamlit
To install [Streamlit](https://docs.streamlit.io/library/get-started/installation) use the following cmd:
```
    pip install streamlit
```

- GStreamer
To install [GStreamer](https://gstreamer.freedesktop.org/documentation/installing/index.html?gi-language=c) use the following cmd:
```
    sudo apt-get install libgstreamer1.0-dev gstreamer1.0-plugins-good gstreamer1.0-tools
```

## Task Done
- [x] Integrating GStreamer-based video player with Streamlit frameworks
- [x] Implementing methods to update the Videotestsrc parameters dynamically
- [x] Adding start, stop, restart, and reset buttons to control the pipeline.
- [x] Displaying the intermediate frames in the Streamlit app from the data recived at appsink
- [x] Displaying/Download the final video output

## Future Work
- [ ] Use Webrtc component to stream the gstreamer buffer directly to the streamlit browser
- [ ] Add a pause button to pause and resume the pipeline
