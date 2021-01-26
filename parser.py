# -*- coding: utf-8 -*-
from pathlib import Path
from typing import List, Tuple, Union

try:
    from typing import Final
except ImportError:
    class _Final:
        def __getitem__(self, item):
            return item


    Final = _Final()

try:
    import numpy as np
except ImportError:
    np = None
    import struct

try:
    from smb.SMBHandler import SMBHandler
except ImportError:
    SMBHandler = None
    __smb_opener = None
else:
    import urllib.request
    __smb_opener = urllib.request.build_opener(SMBHandler)

__all__ = ['parse']

_CHANNELS_COUNT: Final[int] = 52


def _parse_with_struct(filename: Union[str, Path]) -> Tuple[List[str], List[List[float]]]:
    double_size: Final[int] = struct.calcsize('<d')
    with (filename.open('rb') if isinstance(filename, Path) else
          __smb_opener.open(filename) if __smb_opener is not None and filename.startswith('smb://') else
          open(filename, 'rb')) as f_in:
        f_in.seek(0x1800 + 32)
        titles: List[str] = list(map(lambda s: s.strip(b'\0').decode('ascii'),
                                     struct.unpack_from('<' + '32s' * (_CHANNELS_COUNT - 1),
                                                        f_in.read((_CHANNELS_COUNT - 1) * 32))))
        f_in.seek(0x3000)
        data: List[List[float]] = [[] for _ in range(_CHANNELS_COUNT - 1)]
        while True:
            data_size_data: bytes = f_in.read(double_size)
            if not data_size_data:
                break
            data_size: int = int(struct.unpack_from('<d', data_size_data)[0]) - double_size
            line_data: bytes = f_in.read(data_size)
            if len(line_data) != data_size:
                raise IOError('Corrupted or incomplete data found')
            count: int = len(line_data) // double_size
            if count != _CHANNELS_COUNT - 1:
                raise RuntimeError(f'Do not know how to process {count} channels')
            for index, item in enumerate(struct.unpack_from(f'<{_CHANNELS_COUNT - 1}d', line_data)):
                data[index].append(item)
        return titles, data


def _parse_with_numpy(filename: Union[str, Path]) -> Tuple[List[str], np.ndarray]:
    if np is None:
        raise ImportError('Module `numpy` is not loaded')

    if isinstance(filename, str) and filename.startswith('file:'):
        filename = filename[len('file:'):]

    with (filename.open('rb') if isinstance(filename, Path) else
          __smb_opener.open(filename) if __smb_opener is not None and filename.startswith('smb:') else
          open(filename, 'rb')) as f_in:
        f_in.seek(0x1800 + 32)
        titles: List[str] = [f_in.read(32).strip(b'\0').decode('ascii') for _ in range(_CHANNELS_COUNT - 1)]
        f_in.seek(0x3000)
        dt = np.dtype(np.float64)
        dt = dt.newbyteorder('<')
        data: np.ndarray = np.frombuffer(f_in.read(), dtype=dt)
        if not (data.size / _CHANNELS_COUNT).is_integer():
            data = data[:-(data.size % _CHANNELS_COUNT)]
            # raise RuntimeError(f'Do not know how to process {data.size} numbers')
        return titles, data.reshape((_CHANNELS_COUNT, -1), order='F')[1:]


if np is None:
    parse = _parse_with_struct
else:
    parse = _parse_with_numpy
