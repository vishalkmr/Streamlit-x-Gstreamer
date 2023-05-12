# Streamlit-x-Gstreamer
 This repository contains sample Streamlit apps that uses GStreamer for video streaming. These applications that demonstrate how to integrate GStreamer pipeline and applications with Streamlit, a popular Python library for building interactive web applications.
## Dependencies
Before running this application, make sure you have the following dependencies installed:

- Python 3
- Streamlit
- GStreamer

You can install Python 3 from the official [Python](https://www.python.org/downloads/) website.

To install [Streamlit](https://docs.streamlit.io/library/get-started/installation) and [GStreamer](https://gstreamer.freedesktop.org/documentation/installing/index.html?gi-language=c), you can run the following command in your terminal:

```
    pip install streamlit
```


    sudo apt-get install libgstreamer1.0-dev gstreamer1.0-plugins-good gstreamer1.0-tools


deepstream-app -c




deepstream-app : Support of Trafficcamnet as PGIE and 2 new SGIE models with DS reference app

So, now, the DS reference app will have a new Trafficcamnet as PGIE and 2 new SGIE models.

PGIE will be replaced by Trafficcamnet - https://catalog.ngc.nvidia.com/orgs/nvidia/teams/tao/models/trafficcamnet  
Car Make model will be replaced by VehickeMakeNet: https://catalog.ngc.nvidia.com/orgs/nvidia/teams/tao/models/vehiclemakenet
Car type model will be replaced by VehicleTypeNet: https://catalog.ngc.nvidia.com/orgs/nvidia/teams/tao/models/vehicletypenet  
Car color model will not be used. This is because there is no equivalent model on NGC.

DSNEX-4034
Bug 3962287

Unit-Test:
 we have to run the deepstream app with all the configs which are modified, for example
- deepstream-app -c source30_1080p_dec_infer-resnet_tiled_display_int8.txt
- deepstream-app -c source30_1080p_dec_preprocess_infer-resnet_tiled_display_int8.txt
- deepstream-app -c source4_1080p_dec_infer-resnet_tracker_sgie_tiled_display_int8_gpu1.txt
- deepstream-app -c source4_1080p_dec_infer-resnet_tracker_sgie_tiled_display_int8.txt
- deepstream-app -c source4_1080p_dec_preprocess_infer-resnet_preprocess_sgie_tiled_display_int8.txt




