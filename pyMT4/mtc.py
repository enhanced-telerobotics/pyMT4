import os
import warnings
import ctypes
import logging
import numpy as np
from ctypes import *
from typing import Tuple
from .path import MTHome
from .structure import *

MT_MAX_STRING_LENGTH = 400


class MTC(object):
    """
    MTC provides a Python interface to the MT4 camera tracking system via its shared library.
        This class handles loading the MT4 DLL, attaching cameras, loading marker templates, and provides
        methods for camera and marker management, including retrieving camera information, setting streaming
        modes, processing frames, and extracting marker poses.
        
    Class Variables:
        mtc_lib (ctypes.CDLL): The loaded MT4 shared library.
        mthome (str): Path to the MT4 home directory.
        _camera (int): Handle to the currently selected camera.
        _serial_number (int): Serial number of the selected camera.
        _markers (int): Handle to the collection of detected markers.
        _poseXf (int): Handle to the 3D transformation object for marker pose.
        _ref_marker (int): Handle to the reference marker (if set).
    """
    mtc_lib: ctypes.CDLL
    mthome: str

    _camera: int
    _serial_number: int

    _markers: int
    _poseXf: int
    _ref_marker: int

    def __init__(self,
                 mt_home: str = MTHome,
                 cam_index: int = 0) -> None:
        """
        Initializes the MTC class, loading the shared library and attaching available cameras.

        Parameters:
            mt_home (str): The path to the MTHome directory.
        """
        self.mtc_lib = None
        self.mthome = mt_home

        # Load the shared library
        try:
            lib_path = os.path.join(self.mthome, 'Dist64MT4', 'mtc.dll')
            self.mtc_lib = ctypes.CDLL(lib_path)
        except OSError as e:
            raise RuntimeError(
                f"Could not load MTC library from {lib_path}: {e}")

        # Set types for MTLastErrorString
        self.mtc_lib.MTLastErrorString.restype = c_char_p

        # Attach available cameras
        self._attach_cameras()
        self._load_marker_templates()

        # Count number of cameras
        camera_count = self.get_camera_count()

        if camera_count:
            assert cam_index < camera_count, \
                f"Camera index {cam_index} is out of range. Available cameras: {camera_count}"

            # Obtain a handle to the camera
            self._camera = self.get_camera(cam_index)

            # Obtain its serial number
            self._serial_number = self.get_serial_number(self._camera)

            # Set streaming mode
            self.set_streaming_mode(mtFrameType.ROIs,
                                    mtDecimation.Dec41,
                                    mtBitDepth.Bpp14)

            # Init collection handles
            self._markers = self._create_collection()
            self._poseXf = self._create_xform3d()
        else:
            warnings.warn("No camera to connect", ResourceWarning)

    def get_camera_count(self) -> int:
        """
        Returns the count of attached cameras.

        Returns:
            int: Number of attached cameras.
        """
        # Set function return type
        self.mtc_lib.Cameras_Count.restype = c_int

        if self.mtc_lib:
            return self.mtc_lib.Cameras_Count()
        return 0

    def get_camera(self, index: int) -> int:
        """
        Gets the camera handle for a specified index.

        Parameters:
            index (int): The index of the camera.

        Returns:
            int: The camera handle if successful, otherwise None.
        """
        # Set function argument and return types
        self.mtc_lib.Cameras_ItemGet.argtypes = [c_int, POINTER(c_longlong)]
        self.mtc_lib.Cameras_ItemGet.restype = c_int

        if self.mtc_lib:
            camera_handle = c_longlong()
            result = self.mtc_lib.Cameras_ItemGet(index, byref(camera_handle))
            if result == 0:
                return camera_handle.value
            else:
                self._process_error("Cameras_ItemGet")
        return None

    def get_serial_number(self, camera_handle: int = None) -> int:
        """
        Retrieves the serial number of the specified camera.

        Parameters:
            camera_handle (int): The handle of the camera.

        Returns:
            int: The serial number of the camera if successful, otherwise None.
        """
        # Set function argument and return types
        self.mtc_lib.Camera_SerialNumberGet.argtypes = [
            c_longlong, POINTER(c_int)]
        self.mtc_lib.Camera_SerialNumberGet.restype = c_int

        # Set to the default camera
        if camera_handle is None:
            camera_handle = self._camera

        if self.mtc_lib:
            serial_number = c_int()
            result = self.mtc_lib.Camera_SerialNumberGet(
                camera_handle, byref(serial_number))
            if result == 0:
                return serial_number.value
            else:
                self._process_error("Camera_SerialNumberGet")
        return None

    def get_camera_resolution(self, camera_handle: int = None) -> Tuple[int, int]:
        """
        Retrieves the resolution (width and height) of the specified camera.

        Parameters:
            camera_handle (int): The handle of the camera.

        Returns:
            tuple: A tuple (width, height) representing the resolution of the camera if successful,
                otherwise None.
        """
        # Set function argument and return types
        self.mtc_lib.Camera_ResolutionGet.argtypes = [
            c_longlong, POINTER(c_int), POINTER(c_int)]
        self.mtc_lib.Camera_ResolutionGet.restype = c_int

        # Set to the default camera
        if camera_handle is None:
            camera_handle = self._camera

        if self.mtc_lib:
            width = c_int()
            height = c_int()
            result = self.mtc_lib.Camera_ResolutionGet(
                camera_handle, byref(width), byref(height))
            if result == 0:
                return (width.value, height.value)
            else:
                self._process_error("Camera_ResolutionGet")
        return None

    def set_streaming_mode(self,
                           frame_type: mtFrameType,
                           decimation: mtDecimation,
                           bit_depth: mtBitDepth) -> None:
        """
        Sets the streaming mode for the specified camera by serial number.

        Parameters:
            serial_number (int): The serial number of the camera.
            frame_type (mtFrameType): The frame type to set.
            decimation (mtDecimation): The decimation level to set.
            bit_depth (mtBitDepth): The bit depth to set.
        """
        # Create an instance of the struct with desired settings
        streaming_mode = mtStreamingModeStruct(frame_type=frame_type.value,
                                               decimation=decimation.value,
                                               bit_depth=bit_depth.value)

        # Set function argument and return types
        self.mtc_lib.Cameras_StreamingModeSet.argtypes = [
            POINTER(mtStreamingModeStruct), c_int]
        self.mtc_lib.Cameras_StreamingModeSet.restype = c_int

        # Call the function to set streaming mode
        result = self.mtc_lib.Cameras_StreamingModeSet(
            byref(streaming_mode), self._serial_number)
        if result != 0:
            self._process_error("Cameras_StreamingModeSet")

    def set_reference_marker(self, ref_name: str) -> None:
        """
        Sets the reference marker by its name.

        Parameters:
            ref_name (str): The name of the reference marker to set.
        """
        # Dictionary for all markers
        markers = {}

        # Loop over each marker to retrieve its handle and name
        for i in range(self._get_markers()):
            handle = self._get_marker(i)
            name = self._get_marker_name(handle)
            markers[name] = handle

        if ref_name not in markers:
            raise ValueError(f"Reference frame '{ref_name}' not existed.")
        else:
            self._ref_marker = markers[ref_name]

    def get_poses(self, rot: bool = True) -> dict:
        """
        Retrieves the poses (positions and optional rotation matrices) of detected markers.

        Parameters:
            rot (bool): Whether to include rotation matrices in the output. Defaults to True.

        Returns:
            dict: A dictionary where keys are marker names and values are dictionaries containing:
                - 'pos': A NumPy array of the marker's position (x, y, z).
                - 'rot': A NumPy array of the marker's 3x3 rotation matrix, if `rot` is True.
        """
        # Dictionary to hold marker data
        markers = {}

        # Get the number of markers identified in the current frame
        num_markers = self._get_markers()

        # Loop over each marker to retrieve its pose
        for i in range(num_markers):
            # Get the handle of the current marker from the collection
            marker = self._get_marker(i)

            # Get the name of the marker
            name = self._get_marker_name(marker)

            # Optional: Set the reference for the marker
            if hasattr(self, '_ref_marker'):
                self._set_reference_marker(marker)

            # Get the pose of the marker
            pose = self._get_poes(marker, rot)

            # Store the retrieved data
            markers[name] = pose

        return markers

    def close(self) -> None:
        """
        Detaches all cameras and releases resources.
        """
        if self.mtc_lib:
            self.mtc_lib.Cameras_Detach.argtypes = []
            self.mtc_lib.Cameras_Detach.restype = None
            self.mtc_lib.Cameras_Detach()

    def _process_error(self, function_name: str) -> None:
        """
        Processes and logs an error message for the specified function.

        Parameters:
            function_name (str): The name of the function where the error occurred.
        """
        error_message = self.mtc_lib.MTLastErrorString().decode('utf-8')
        raise RuntimeError(f"Error in {function_name}: {error_message}")

    def _attach_cameras(self) -> None:
        """
        Attaches available cameras using the calibration directory.
        """
        # Set function argument and return types
        self.mtc_lib.Cameras_AttachAvailableCameras.argtypes = [c_char_p]
        self.mtc_lib.Cameras_AttachAvailableCameras.restype = c_int

        # Set the calibration directory path
        calibration_dir = os.path.join(
            self.mthome, 'CalibrationFiles').encode('utf-8')

        # Attach available cameras
        result = self.mtc_lib.Cameras_AttachAvailableCameras(calibration_dir)
        if result != 0:
            self._process_error("Cameras_AttachAvailableCameras")
        else:
            logging.info("Successfully attached available cameras.")

    def _load_marker_templates(self) -> None:
        """
        Loads marker templates from the specified directory.
        """
        # Set function argument and return types
        self.mtc_lib.Markers_LoadTemplates.argtypes = [c_char_p]
        self.mtc_lib.Markers_LoadTemplates.restype = c_int

        # Set the marker templates directory path
        marker_dir = os.path.join(self.mthome, 'Markers').encode('utf-8')

        # Load the marker templates
        result = self.mtc_lib.Markers_LoadTemplates(marker_dir)
        if result != 0:
            self._process_error("Markers_LoadTemplates")
        else:
            logging.info("Successfully loaded marker templates.")

    def _create_collection(self) -> int:
        """
        Creates a new collection and returns its handle.

        Returns:
            int: The handle of the new collection as an integer, or None if creation failed.
        """
        # Set the return type of Collection_New to c_longlong
        self.mtc_lib.Collection_New.restype = c_longlong

        if self.mtc_lib:
            # Call the function and get the handle
            collection_handle = self.mtc_lib.Collection_New()
            if collection_handle:
                return collection_handle
            else:
                self._process_error("Collection_New")
        return None

    def _create_xform3d(self) -> int:
        """
        Creates a new 3D transformation object and returns its handle.

        Returns:
            int: The handle of the new 3D transformation object as an integer, or None if creation failed.
        """
        # Set the return type of Xform3D_New to c_longlong
        self.mtc_lib.Xform3D_New.restype = c_longlong

        if self.mtc_lib:
            # Call the function and get the handle
            xform3d_handle = self.mtc_lib.Xform3D_New()
            if xform3d_handle:
                return xform3d_handle
            else:
                self._process_error("Xform3D_New")
        return None

    def _get_markers(self) -> int:
        """
        Grabs a frame from the camera, processes it to identify markers,
        and returns the number of markers identified.

        Returns:
            int: The number of markers identified in the current frame.
        """
        # Define the argument types for the required functions
        self.mtc_lib.Cameras_GrabFrame.argtypes = [c_longlong]
        self.mtc_lib.Cameras_GrabFrame.restype = c_int

        self.mtc_lib.Markers_ProcessFrame.argtypes = [c_longlong]
        self.mtc_lib.Markers_ProcessFrame.restype = c_int

        self.mtc_lib.Markers_IdentifiedMarkersGet.argtypes = [
            c_longlong, c_longlong]
        self.mtc_lib.Markers_IdentifiedMarkersGet.restype = c_int

        self.mtc_lib.Collection_Count.argtypes = [c_longlong]
        self.mtc_lib.Collection_Count.restype = c_int

        # Grab a frame from the camera
        result = self.mtc_lib.Cameras_GrabFrame(self._camera)
        if result != 0:  # Check for success, assuming 0 indicates success
            self._process_error("Cameras_GrabFrame")
            return 0

        # Process the frame to identify markers
        result = self.mtc_lib.Markers_ProcessFrame(self._camera)
        if result != 0:
            self._process_error("Markers_ProcessFrame")
            return 0

        # Get the identified markers from the processed frame
        result = self.mtc_lib.Markers_IdentifiedMarkersGet(
            self._camera, self._markers)
        if result != 0:
            self._process_error("Markers_IdentifiedMarkersGet")
            return 0

        # Count the number of markers in the collection
        num_markers = self.mtc_lib.Collection_Count(self._markers)

        return num_markers

    def _get_marker_name(self, marker_handle: int) -> str:
        """
        Retrieves the name of the specified marker.

        Parameters:
            marker_handle (int): The handle of the marker.

        Returns:
            str: The name of the marker as a string, or None if the operation failed.
        """
        # Set function argument and return types
        self.mtc_lib.Marker_NameGet.argtypes = [
            c_longlong, c_char_p, c_int, POINTER(c_int)]
        self.mtc_lib.Marker_NameGet.restype = c_int

        if self.mtc_lib:
            name_buffer = create_string_buffer(
                MT_MAX_STRING_LENGTH)  # Create a buffer for the name
            actual_chars = c_int()  # Variable to hold the actual number of characters written

            # Call the function to get the marker name
            result = self.mtc_lib.Marker_NameGet(
                marker_handle, name_buffer, MT_MAX_STRING_LENGTH, byref(actual_chars))
            if result == 0:
                # Convert the buffer to a Python string, limited to the actual number of characters
                return name_buffer.value.decode('utf-8')[:actual_chars.value]
            else:
                self._process_error("Marker_NameGet")
        return None

    def _get_marker(self,
                    index: int) -> int:
        """"
        Retrieves the marker handle for a specified index and updates the poseXf with the marker's pose.

        Parameters:
            index (int): The index of the marker.
        """
        # Define the argument and return types for the functions used
        self.mtc_lib.Collection_Int.argtypes = [c_longlong, c_int]
        self.mtc_lib.Collection_Int.restype = c_longlong

        self.mtc_lib.Marker_Marker2CameraXfGet.argtypes = [
            c_longlong, c_longlong, c_longlong, POINTER(c_longlong)]
        self.mtc_lib.Marker_Marker2CameraXfGet.restype = c_int

        # Get the handle of the current marker from the collection
        marker = self.mtc_lib.Collection_Int(self._markers, index + 1)

        # Update the poseXf with the marker's pose
        camera_identifier = c_longlong()
        self.mtc_lib.Marker_Marker2CameraXfGet(
            marker, self._camera, self._poseXf, byref(camera_identifier))

        return marker

    def _get_poes(self, marker: int, rot: bool = True) -> dict:
        """
        Retrieves the pose (position and optional rotation matrix) of a given marker.

        Parameters:
            marker (int): The handle of the marker.
            rot (bool, optional): Whether to include the rotation matrix in the output. Defaults to True.

        Returns:
            dict: A dictionary containing:
            - 'pos': A NumPy array of the marker's position (x, y, z).
            - 'rot': A NumPy array of the marker's 3x3 rotation matrix, if `rot` is True.
        """
        if hasattr(self, '_ref_marker'):
            # Define the argument and return types for the functions used
            self.mtc_lib.Marker_Marker2ReferenceXfGet.argtypes = [
                c_longlong, c_longlong, c_longlong, POINTER(c_longlong)]
            self.mtc_lib.Marker_Marker2ReferenceXfGet.restype = c_int

            # Update the poseXf with the marker's pose
            camera_identifier = c_longlong()
            self.mtc_lib.Marker_Marker2ReferenceXfGet(
                marker, self._camera, self._poseXf, byref(camera_identifier))
        else:
            # Define the argument and return types for the functions used
            self.mtc_lib.Marker_Marker2CameraXfGet.argtypes = [
                c_longlong, c_longlong, c_longlong, POINTER(c_longlong)]
            self.mtc_lib.Marker_Marker2CameraXfGet.restype = c_int

            # Update the poseXf with the marker's pose
            camera_identifier = c_longlong()
            self.mtc_lib.Marker_Marker2CameraXfGet(
                marker, self._camera, self._poseXf, byref(camera_identifier))

        # Retrieve the position of the marker
        positions = self._get_position()
        marker_pose = {'pos': positions}

        # Optionally retrieve the rotation matrix of the marker
        if rot:
            rotations = self._get_rotation()
            marker_pose['rot'] = rotations

        return marker_pose

    def _get_position(self) -> np.ndarray:
        """
        Retrieves the position of the marker from the poseXf and returns it as a NumPy array.

        Returns:
            np.ndarray: A NumPy array containing the position of the marker (x, y, z).
        """
        # Define the argument and return types for the functions used
        self.mtc_lib.Xform3D_ShiftGet.argtypes = [
            c_longlong, POINTER(c_double * 3)]
        self.mtc_lib.Xform3D_ShiftGet.restype = c_int

        # Retrieve the position of the marker
        positions = (c_double * 3)()
        self.mtc_lib.Xform3D_ShiftGet(self._poseXf, byref(positions))
        np_positions = np.frombuffer(positions, dtype=np.float64)

        return np.copy(np_positions)

    def _get_rotation(self) -> np.ndarray:
        """
        Retrieves the rotation matrix of the marker from the poseXf and returns it as a NumPy array.

        Returns:
            np.ndarray: A NumPy array containing the rotation matrix of the marker (3x3).
        """
        # Define the argument and return types for the functions used
        self.mtc_lib.Xform3D_RotMatGet.argtypes = [
            c_longlong, POINTER(c_double * 9)]
        self.mtc_lib.Xform3D_RotMatGet.restype = c_int

        # Retrieve the rotation matrix of the marker
        rot_matrix = (c_double * 9)()
        self.mtc_lib.Xform3D_RotMatGet(self._poseXf, byref(rot_matrix))
        np_rot_matrix = np.frombuffer(
            rot_matrix, dtype=np.float64).reshape((3, 3))

        # Transpose the rotation matrix to match the generally expected orientation
        return np.copy(np_rot_matrix.T)

    def _set_reference_marker(self, marker: int) -> None:
        """
        Sets the reference marker for the specified marker.

        Parameters:
            marker (int): The handle of the marker for which to set the reference marker.
        """
        # Set function argument and return types
        self.mtc_lib.Marker_ReferenceMarkerHandleSet.argtypes = [
            c_longlong, c_longlong]
        self.mtc_lib.Marker_ReferenceMarkerHandleSet.restype = c_int

        # Set the reference frame for the specified marker
        result = self.mtc_lib.Marker_ReferenceMarkerHandleSet(
            marker, self._ref_marker)

        if result != 0:
            self._process_error("Marker_ReferenceMarkerHandleSet")
