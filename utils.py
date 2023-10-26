##################################################################################################################
# Author: Vishal Kumar
# Email: vishalkmr01123@gmail.com
#
# This file contains utility functions for variuos task needed during gstreamer pipeline processing.
##################################################################################################################


import cv2
import numpy as np

def element_info(function):
    def wraper(*args, **kwargs):
        print("pipeline <--",function.__name__,str(kwargs))
        result = function(*args, **kwargs)
        return result
    return wraper

def fromat_info(function):
    def wraper(*args, **kwargs):
        print(function.__name__)
        result = function(*args, **kwargs)
        return result
    return wraper

class RGB_Converter:
    """
    This class provides utility functions to convert YUV images to RGB format.
    """
    def __init__(self) -> None:
        pass

    def buffer_to_rgb(self, data, w, h, format):
        if format =="YUY2":
            return self.yuy2_to_rgb(data, w, h)
        elif format =="YV12":
            return self.yv12_to_rgb(data, w, h)
        elif format =="I420":
            return self.i420_to_rgb(data, w, h)
        elif format =="BGR":
            return self.bgr_to_rgb(data, w, h)
        else:
            print("Wrong format",format)

    def bgr_to_rgb(self, data, width, height):
        """
        Convert BGR image to RGB format.

        Parameters:
        data : Input image data in YV12 format.
        width (int): Width of the input image.
        height (int): Height of the input image.

        Returns:
        np.ndarray: Output image in RGB format.
        """
        numpy_array = np.ndarray((height, width, 3),buffer=data,dtype=np.uint8)
        rgb_image = cv2.cvtColor(numpy_array, cv2.COLOR_BGR2RGB)
        return rgb_image

    def yv12_to_rgb(self, data, width, height):
        """
        Convert YV12 image to RGB format.

        Parameters:
        data : Input image data in YV12 format.
        width (int): Width of the input image.
        height (int): Height of the input image.

        Returns:
        np.ndarray: Output image in RGB format.
        """
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
        rgb_image = cv2.cvtColor(yuv_image, cv2.COLOR_YUV2BGR)
        return rgb_image

    def yuy2_to_rgb(self, data, width, height):
        """
        Convert YUY2 image to RGB format.

        Parameters:
        data : Input image data in YUY2 format.
        width (int): Width of the input image.
        height (int): Height of the input image.

        Returns:
        np.ndarray: Output image in RGB format.
        """
        # Convert the byte data to a numpy array with dtype uint8 and reshape it to the image dimensions
        yuv2_array = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 2))

        # Convert the YUV image to RGB format using OpenCV
        rgb_image = cv2.cvtColor(yuv2_array, cv2.COLOR_YUV2RGB_YUYV)

        return rgb_image


    def i420_to_rgb(self, data, width, height):
        """
        Convert I420 image to RGB format.

        Parameters:
        data : Input image data in I420 format.
        width (int): Width of the input image.
        height (int): Height of the input image.

        Returns:
        np.ndarray: Output image in RGB format.
        """
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
        rgb_image = cv2.cvtColor(yuv_image, cv2.COLOR_YUV2RGB)
        return rgb_image


