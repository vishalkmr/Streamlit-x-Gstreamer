import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
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

def add_capsfilter(pipeline, element, format="I420"):
    caps_str = f"video/x-raw, format=(string){format}"
    caps = Gst.caps_from_string(caps_str)
    capsfilter = Gst.ElementFactory.make("capsfilter")
    capsfilter.set_property("caps", caps)
    pipeline.add(capsfilter)
    element.link(capsfilter)
    return capsfilter

def output_parser(pipeline,element,output_file,ext,async_mode=True):
    if ext == "mp4":
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
        encoded_output = mux

    elif ext == "jpg":
        # Create an jpegenc element
        encoder = Gst.ElementFactory.make("jpegenc", "jpegenc")
        pipeline.add(encoder)
        element.link(encoder)
        encoded_output = add_videoconvert(pipeline,encoder)

    elif ext == "png":
        # Create an pngenc element
        encoder = Gst.ElementFactory.make("pngenc", "pngenc")
        pipeline.add(encoder)
        element.link(encoder)
        encoded_output = encoder

    # Create a filesink element and link it encoded_output
    filesink = Gst.ElementFactory.make("filesink", "filesink")
    filesink.set_property("location", output_file+"."+ext)  # set the output file location
    filesink.set_property("async", async_mode)
    pipeline.add(filesink)
    encoded_output.link(filesink)

def bus_message(bus, message, pipeline, loop):
    # Handle bus messages
    t = message.type
    if t == Gst.MessageType.EOS:
        print("End of stream begin")
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

        cv2.imwrite(f"output/{username}_intermediate_output.jpg",bgr_image)
        # print(f"appsink-->  output/{username}_intermediate_output.jpg")
        # print("________"*10)

    return Gst.FlowReturn.OK

def yv12_to_bgr(data: bytes, width: int, height: int) -> np.ndarray:
    # print("YV12 ----> BGR")
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
