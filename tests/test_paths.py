import ctypes
import importlib
import os
import unittest
from unittest.mock import Mock, patch

from pyMT4 import MTC


class PathTests(unittest.TestCase):
    def make_tracker(self, **kwargs):
        library = Mock()
        library.Cameras_AttachAvailableCameras.return_value = 0
        library.Markers_LoadTemplates.return_value = 0
        library.Cameras_Count.return_value = 0
        with patch('pyMT4.mtc.ctypes.CDLL', return_value=library) as loader:
            tracker = MTC(**kwargs)
        return tracker, library, loader

    @patch('pyMT4.mtc.sys.platform', 'linux')
    @patch('pyMT4.mtc.find_library', return_value=None)
    @patch('pyMT4.mtc.os.path.isfile', side_effect=lambda p: p == '/usr/lib/libMTC.so')
    def test_deb_layout(self, *_):
        tracker, library, loader = self.make_tracker(mt_home='/etc/Claronav/MicronTracker4')
        loader.assert_called_with('/usr/lib/libMTC.so')
        library.Cameras_AttachAvailableCameras.assert_called_once_with(
            b'/etc/Claronav/MicronTracker4/CalibrationFiles')
        library.Markers_LoadTemplates.assert_called_once_with(
            b'/etc/Claronav/MicronTracker4/Markers')

    def test_explicit_paths(self):
        tracker, library, loader = self.make_tracker(
            mt_home='/data', library_path='/custom/libMTC.so',
            calibration_dir='/calibration', marker_dir='/templates')
        loader.assert_called_with('/custom/libMTC.so')
        library.Cameras_AttachAvailableCameras.assert_called_once_with(b'/calibration')
        library.Markers_LoadTemplates.assert_called_once_with(b'/templates')

    @patch('pyMT4.mtc.sys.platform', 'win32')
    def test_windows_layout(self):
        _, _, loader = self.make_tracker(mt_home='/sdk')
        loader.assert_called_with(os.path.join('/sdk', 'Dist64MT4', 'mtc.dll'))

    @patch('pyMT4.mtc.sys.platform', 'linux')
    @patch('pyMT4.mtc.find_library', return_value='libMTC.so')
    def test_system_loader(self, _):
        _, _, loader = self.make_tracker(mt_home='/data')
        loader.assert_called_with('libMTC.so')

    @patch('pyMT4.mtc.ctypes.CDLL', side_effect=OSError('missing dependency'))
    def test_load_failure(self, _):
        with self.assertRaisesRegex(RuntimeError, 'missing dependency'):
            MTC(mt_home='/data', library_path='/missing.so')

    @patch.dict(os.environ, {}, clear=True)
    def test_linux_home_fallback(self):
        from pyMT4 import path
        with patch('sys.platform', 'linux'):
            try:
                importlib.reload(path)
                self.assertEqual(path.MTHome, '/etc/Claronav/MicronTracker4')
            finally:
                importlib.reload(path)

    def test_streaming_mode_struct_passed_by_value(self):
        from pyMT4.structure import mtFrameType, mtDecimation, mtBitDepth, mtStreamingModeStruct
        tracker = MTC.__new__(MTC)
        tracker.mtc_lib = Mock()
        tracker._serial_number = 23901514
        tracker.mtc_lib.Cameras_StreamingModeSet.return_value = 0
        tracker.set_streaming_mode(mtFrameType.ROIs, mtDecimation.Dec41, mtBitDepth.Bpp12)
        function = tracker.mtc_lib.Cameras_StreamingModeSet
        mode, serial = function.call_args.args
        self.assertIsInstance(mode, mtStreamingModeStruct)
        self.assertEqual(serial, 23901514)
        self.assertEqual(mode.decimation, 4)
        self.assertEqual(function.argtypes, [mtStreamingModeStruct, ctypes.c_int])

    def test_handle_matches_pointer_size(self):
        self.assertEqual(ctypes.sizeof(ctypes.c_ssize_t), ctypes.sizeof(ctypes.c_void_p))


if __name__ == '__main__':
    unittest.main()
