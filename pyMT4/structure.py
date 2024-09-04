from ctypes import Structure, c_int
from enum import IntEnum


class mtFrameType(IntEnum):
    """
    Enum representing the frame type for camera streaming.

    Attributes:
        NoneType (int): Error-state, no frame type set.
        Full (int): Frames received at full resolution and bit-depth.
        ROIs (int): Only regions of interest (ROIs) are received.
        Alternating (int): Alternating frames of ROIs and image data are received.
    """
    NoneType = 0        # Error-state, no frame type set
    Full = 1            # Frames received at full resolution and bit-depth
    ROIs = 2            # Only XPoint regions of interest are received
    Alternating = 3     # Alternating frames of ROIs and image data are received


class mtDecimation(IntEnum):
    """
    Enum representing the decimation level for camera streaming.

    Attributes:
        NoneType (int): Error-state, no decimation mode set.
        Dec11 (int): Images received with no decimation (1:1).
        Dec21 (int): Images received with 2:1 decimation (every 2nd row and column is kept).
        Dec41 (int): Images received with 4:1 decimation (every 4th row and column is kept).
    """
    NoneType = 0        # Error-state, no decimation mode set
    Dec11 = 1           # Images received with no decimation (1:1)
    Dec21 = 2           # Images received with 2:1 decimation, every 2nd row and column is kept
    Dec41 = 3           # Images received with 4:1 decimation, every 4th row and column is kept


class mtBitDepth(IntEnum):
    """
    Enum representing the pixel bit depth for camera streaming.

    Attributes:
        NoneType (int): Error-state, no pixel depth set.
        Bpp14 (int): 14-bit pixel depth requested.
        Bpp12 (int): 12-bit pixel depth requested.
    """
    NoneType = 0        # Error-state, no pixel depth set
    Bpp14 = 1           # 14-bit pixel depth requested
    Bpp12 = 2           # 12-bit pixel depth requested


class mtStreamingModeStruct(Structure):
    """
    Structure representing the streaming mode settings for a camera.

    Fields:
        frame_type (int): The frame type (mtFrameType) to use for streaming.
        decimation (int): The decimation level (mtDecimation) to use for streaming.
        bit_depth (int): The pixel bit depth (mtBitDepth) to use for streaming.
    
    Usage:
        streaming_mode = mtStreamingModeStruct(
            frame_type=mtFrameType.Full,
            decimation=mtDecimation.Dec11,
            bit_depth=mtBitDepth.Bpp14
        )
    """
    _fields_ = [
        ("frame_type", c_int),  # Use the enum mtFrameType
        ("decimation", c_int),  # Use the enum mtDecimation
        ("bit_depth", c_int)    # Use the enum mtBitDepth
    ]
