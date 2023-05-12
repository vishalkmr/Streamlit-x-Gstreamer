import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os , time
import cv2
import numpy as np

def add_queue(pipeline,element,leaky=False,max_buffer=200,max_bytes=10485760):
    queue=Gst.ElementFactory.make("queue")
    pipeline.add(queue)
    queue.set_property("leaky",leaky)
    queue.set_property("max-size-buffers", max_buffer)
    queue.set_property("max-size-bytes", max_bytes)
    element.link(queue)
    return queue

def add_identity(pipeline,element):
    identity=Gst.ElementFactory.make("identity")
    pipeline.add(identity)
    identity.set_property("silent",0)
    element.link(identity)
    return identity

def add_videoconvert(pipeline,element):
    videoconvert=Gst.ElementFactory.make("videoconvert")
    pipeline.add(videoconvert)
    element.link(videoconvert)
    return videoconvert


def add_capsfilter(pipeline, element):
    caps_filter = Gst.ElementFactory.make('capsfilter', 'caps')
    caps_string = 'video/x-raw(memory:NVMM), format=RGBA, width='+ str(500) + ', height=' + str(500)
    caps = Gst.Caps.from_string(caps_string)
    caps_filter.set_property('caps', caps)
    pipeline.add(caps_filter)
    element.link(caps_filter)
    return caps_filter

def input_parser(pipeline,source):
    # Create a demux element and link it to the filesrc
    demux = Gst.ElementFactory.make("identity", "qtdemux")
    pipeline.add(demux)
    source.link(demux)
    # sinkpad = streammux.get_request_pad("sink_0")
    # if not sinkpad:
    #     print(" Unable to get the sink pad of streammux \n")
    # srcpad = decoder.get_static_pad("src")
    # srcpad.link(sinkpad)

    # Create a h264parse element and link it to the demux
    parser = Gst.ElementFactory.make("h264parse", "h264parse_in")
    pipeline.add(parser)
    demux.link(parser)

    # Create an avdec_h264 element and link it to the parser
    decoder = Gst.ElementFactory.make("avdec_h264", "avdec_h264")
    pipeline.add(decoder)
    parser.link(decoder)

    return add_videoconvert(pipeline,decoder)


def output_parser(pipeline,element,output_file,async_mode=True):
    # Create an x264enc element and link it to the videoconvert
    encoder = Gst.ElementFactory.make("x264enc", "x264enc")
    pipeline.add(encoder)
    element.link(encoder)

    # Create a h264parse element and link it to the encoder
    parser = Gst.ElementFactory.make("h264parse", "h264parse_out")
    pipeline.add(parser)
    encoder.link(parser)

    # Create a mp4mux element and link it to the h264parse
    mux = Gst.ElementFactory.make("mp4mux", "mp4mux")
    pipeline.add(mux)
    parser.link(mux)

    # Create a filesink element and link it to the mp4mux
    filesink = Gst.ElementFactory.make("filesink", "filesink")
    filesink.set_property("location", output_file)  # set the output file location
    filesink.set_property("async", async_mode)
    pipeline.add(filesink)
    mux.link(filesink)

def bus_message(bus, message, pipeline, loop):
    # Handle bus messages
    t = message.type
    if t == Gst.MessageType.EOS:
        pipeline.set_state(Gst.State.NULL)
        loop.quit()
        print("End of stream")

    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        pipeline.set_state(Gst.State.NULL)
        loop.quit()
        print("Error: %s" % err, debug)

    elif t == Gst.MessageType.STATE_CHANGED:
        old_state, new_state, pending_state = message.parse_state_changed()
        print("State changed from {} to {}".format(Gst.Element.state_get_name(old_state), Gst.Element.state_get_name(new_state)))

    elif t == Gst.MessageType.TAG:
        tag_list = message.parse_tag()
        # print("Tag: %s" % tag_list.to_string())

    elif t == Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        print("Warning: %s: %s\n" % (err, debug))


# Define a callback function to receive the buffer data on appsink
def appsink_buffer(appsink,username):
    sample = appsink.emit("pull-sample")
    if sample:
        buffer = sample.get_buffer()
        # print("________"*10)

        # Parsing caps format
        caps_format = sample.get_caps().get_structure(0)
        w, h,format = caps_format.get_value('width'), caps_format.get_value('height'),caps_format.get_value('format')
        # print("buffer-",buffer.offset)
        # print(caps_format)

        # Parsing the buffer into yuv2 image
        buffer_size = buffer.get_size()
        # print(buffer_size,w,h)
        data = buffer.extract_dup(0, buffer_size)
        bgr_image = buffer_to_bgr(data,w,h,format)

        cv2.imwrite(f"output/{username}_output.jpg",bgr_image)

        # print("________"*10)
        # print("\n\n\n")
    return Gst.FlowReturn.OK

def yv12_to_bgr(data: bytes, width: int, height: int) -> np.ndarray:
    print("YV12 ----> BGR")
    y_size = width * height
    uv_size = int(y_size / 4)
    y_plane = np.frombuffer(data[:y_size], dtype=np.uint8).reshape((height, width))
    v_plane = np.frombuffer(data[(y_size + uv_size):], dtype=np.uint8).reshape((int(height / 2), int(width / 2)))
    u_plane = np.frombuffer(data[(y_size):(y_size + uv_size)], dtype=np.uint8).reshape((int(height / 2), int(width / 2)))
    u_plane = cv2.resize(u_plane, (width, height // 2), interpolation=cv2.INTER_LINEAR)
    v_plane = cv2.resize(v_plane, (width, height // 2), interpolation=cv2.INTER_LINEAR)
    u_plane = np.repeat(u_plane, 2, axis=0)  # Upsample U plane
    v_plane = np.repeat(v_plane, 2, axis=0)  # Upsample V plane
    yuv_image = np.dstack((y_plane, u_plane, v_plane))
    bgr_image = cv2.cvtColor(yuv_image, cv2.COLOR_YUV2RGB)
    return bgr_image

def yuy2_to_bgr(data: bytes, width: int, height: int) -> np.ndarray:
    # print("YUY2 ----> BGR")
    yuv2_array = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 2))
    bgr_image = cv2.cvtColor(yuv2_array, cv2.COLOR_YUV2BGR_YUYV)
    return bgr_image


def i420_to_bgr(data: bytes, width: int, height: int) -> np.ndarray:
    # print("I420 ----> BGR")
    y_size = width * height
    u_size = int(y_size / 4)
    v_size = u_size
    y_plane = np.frombuffer(data[:y_size], dtype=np.uint8).reshape((height, width))
    u_plane = np.frombuffer(data[y_size:(y_size+u_size)], dtype=np.uint8).reshape((int(height / 2), int(width / 2)))
    v_plane = np.frombuffer(data[(y_size+u_size):(y_size+u_size+v_size)], dtype=np.uint8).reshape((int(height / 2), int(width / 2)))
    u_plane = cv2.resize(u_plane, (width, height // 2), interpolation=cv2.INTER_LINEAR)
    v_plane = cv2.resize(v_plane, (width, height // 2), interpolation=cv2.INTER_LINEAR)
    u_plane = np.repeat(u_plane, 2, axis=0)  # Upsample U plane
    v_plane = np.repeat(v_plane, 2, axis=0)  # Upsample V plane
    yuv_image = np.dstack((y_plane, u_plane, v_plane))
    bgr_image = cv2.cvtColor(yuv_image, cv2.COLOR_YUV2BGR)
    return bgr_image

def buffer_to_bgr(data,w,h,format):
    if format =="YUY2":
        return yuy2_to_bgr(data, w, h)
    elif format =="YV12":
        return yv12_to_bgr(data, w, h)
    elif format =="I420":
        return i420_to_bgr(data, w, h)
    else:
        print("Wrong format",format)


