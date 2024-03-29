# Streamlit-x-Gstreamer
This project demonstrates integrating a GStreamer video player into a Streamlit window. It leverages the power of GStreamer for video processing and rendering while utilizing the user-friendly interface of Streamlit for interactive controls. With this integration, users can easily configure video parameters, start and stop the video playback, and view the output within the Streamlit app. It simplifies creating a GStreamer-based video player and makes it accessible to developers using Streamlit for their applications.


[https://github.com/vishalkmr/Streamlit-x-Gstreamer/assets/20735280/d36f6592-fba1-4c83-95de-9f974dfd3ba4](https://github.com/vishalkmr/Streamlit-x-Gstreamer/assets/20735280/b3b5d049-98d3-4684-968b-85bf627599a2)

 
## Dependencies
Before running this application, make sure you have the following dependencies installed:

1. Python 3

   You can install Python 3 from the official [Python](https://www.python.org/downloads/) website.

2. Streamlit
  
   To install [Streamlit](https://docs.streamlit.io/library/get-started/installation) use the following cmd:
   ```sh
   pip install streamlit
   ```

3. GStreamer

   To install [GStreamer](https://gstreamer.freedesktop.org/documentation/installing/index.html?gi-language=c) use the following cmd:
   ```sh
   sudo apt-get install libgstreamer1.0-dev gstreamer1.0-plugins-good gstreamer1.0-tools
   ```

## Task Done
- [x] Integrating GStreamer-based video player with Streamlit frameworks
- [x] Implementing methods to update the Videotestsrc parameters dynamically
- [x] Adding start, stop, and reset buttons to control the pipeline.
- [x] Displaying the intermediate frames in the Streamlit app from the data recived at appsink
- [x] Displaying/Download the final video output

## Future Work
- [ ] Add a pause button to pause and resume the pipeline
