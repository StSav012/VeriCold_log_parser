# -*- coding: utf-8 -*-
from pathlib import Path
from typing import BinaryIO, Final, List, Optional, Tuple, Union

_MAX_CHANNELS_COUNT: Final[int] = 52

__all__ = ['parse']


try:
    import numpy as np
    from numpy.typing import NDArray

    def parse(filename: Union[str, Path, BinaryIO]) -> Tuple[List[str], NDArray[np.float64]]:
        def _parse(file_handle: BinaryIO) -> Tuple[List[str], NDArray[np.float64]]:
            file_handle.seek(0x1800 + 32)
            titles: List[str] = [file_handle.read(32).strip(b'\0').decode('ascii')
                                 for _ in range(_MAX_CHANNELS_COUNT - 1)]
            titles = list(filter(None, titles))
            file_handle.seek(0x3000)
            # noinspection PyTypeChecker
            dt: np.dtype = np.dtype(np.float64).newbyteorder('<')
            data: NDArray[np.float64] = np.frombuffer(file_handle.read(), dtype=dt)
            i: int = 0
            data_item_size: Optional[int] = None
            while i < data.size:
                if data_item_size is None:
                    data_item_size = int(round(data[i] / dt.itemsize))
                elif int(round(data[i] / dt.itemsize)) != data_item_size:
                    raise RuntimeError('Inconsistent data: some records are faulty')
                i += int(round(data[i] / dt.itemsize))
            if data_item_size is None:
                return [], np.empty(0)
            return titles, data.reshape((data_item_size, -1), order='F')[1:(len(titles) + 1)].astype(np.float64)

        if isinstance(filename, BinaryIO):
            return _parse(filename)
        f_in: BinaryIO
        with (filename.open('rb') if isinstance(filename, Path) else open(filename, 'rb')) as f_in:
            return _parse(f_in)

except ImportError:
    import struct

    def parse(filename: Union[str, Path, BinaryIO]) -> Tuple[List[str], List[List[float]]]:
        def _parse(file_handle: BinaryIO) -> Tuple[List[str], List[List[float]]]:
            file_handle.seek(0x1800 + 32)
            titles: List[str] = list(map(lambda s: s.strip(b'\0').decode('ascii'),
                                         struct.unpack_from('<' + '32s' * (_MAX_CHANNELS_COUNT - 1),
                                                            file_handle.read((_MAX_CHANNELS_COUNT - 1) * 32))))
            titles = list(filter(None, titles))
            file_handle.seek(0x3000)
            data: List[List[float]] = [[] for _ in range(len(titles))]
            while True:
                data_size_data: bytes = file_handle.read(double_size)
                if not data_size_data:
                    break
                data_size: int = int(struct.unpack_from('<d', data_size_data)[0]) - double_size
                line_data: bytes = file_handle.read(data_size)
                if len(line_data) != data_size:
                    raise IOError('Corrupted or incomplete data found')
                count: int = len(line_data) // double_size
                if count != len(titles):
                    raise RuntimeError(f'Do not know how to process {count} channels')
                for index, item in enumerate(struct.unpack_from(f'<{len(titles)}d', line_data)):
                    data[index].append(item)
            return titles, data

        double_size: Final[int] = struct.calcsize('<d')

        if isinstance(filename, BinaryIO):
            return _parse(filename)
        f_in: BinaryIO
        with (filename.open('rb') if isinstance(filename, Path) else open(filename, 'rb')) as f_in:
            return _parse(f_in)
