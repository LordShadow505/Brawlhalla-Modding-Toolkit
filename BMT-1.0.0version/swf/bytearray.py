class ByteArray:
    def __init__(self):
        self._bytearray = bytearray()

    def _normalize_data(self, data):
        if type(data) == self.__class__:
            return data._bytearray
        else:
            return data

    def writeUI32(self, data):
        data = self._normalize_data(data)

        for n in range(4):
            self._bytearray.append((data >> 8*n) & 0xff)

    def writeUI16(self, data):
        data = self._normalize_data(data)

        self._bytearray.append(data & 0xff)
        self._bytearray.append((data >> 8) & 0xff)

    def writeUI8(self, data):
        data = self._normalize_data(data)

        self._bytearray.append(data & 0xff)

    def write(self, data):
        data = self._normalize_data(data)

        for _elem in data:
            self._bytearray.append(_elem)

    def get(self) -> bytearray:
        return self._bytearray

    def __len__(self):
        return len(self._bytearray)
