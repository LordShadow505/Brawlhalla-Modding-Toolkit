import json
from jpype import JInt, JString
from .bytearray import ByteArray


class SymbolClass:
    headerTagId = 0x133f
    dataFlag = "json="

    def __init__(self, symbolClassTag=None):
        self.symbolClass = symbolClassTag
        self._tags = {}

        if self.symbolClass is not None:
            for n, tag in enumerate(self.symbolClass.tags):
                self._tags[int(tag)] = self._decodeData(str(self.symbolClass.names[n]))

    def __contains__(self, item):
        return item in self._tags

    def __getitem__(self, key):
        return self._tags[key]

    def _encodeData(self, data):
        if type(data) in [dict, list, bool] or data is None:
            return f"{self.dataFlag}{json.dumps(data)}"
        else:
            return data

    def _decodeData(self, data: str):
        if data.startswith(self.dataFlag):
            try:
                return json.loads(data.replace(self.dataFlag, "", 1))
            except json.decoder.JSONDecodeError:
                return data

        return data

    def getNextTagId(self) -> int:
        return len(self._tags)

    def addTag(self, tag: int, name: object) -> None:
        #if tag in self._tags:
        #    raise SymbolClassTagAlreadyExist("This tag already exists")
        self._tags[int(tag)] = name

    def setTag(self, tag: int, name: object) -> None:
        #if tag not in self._tags:
        #    raise SymbolClassTagDoesNotExist("This tag does not exist")
        self._tags[int(tag)] = name

    def getTag(self, tag: int, default=None) -> object:
        if tag not in self._tags:
            #raise SymbolClassTagDoesNotExist("This tag does not exist")
            return default
        return self._tags.get(int(tag))

    def removeTag(self, tag: int):
        self._tags.pop(int(tag))

    def getTagByName(self, name: object) -> int:
        for tag, name_ in self._tags.items():
            if name_ == name:
                return tag

    def getTags(self):
        return self._tags.copy()

    def getByteArray(self, reverse=True) -> bytearray:
        if self.symbolClass is not None:
            self.save()
            content = bytearray(self.symbolClass.getData())

        else:
            content = ByteArray()
            content.writeUI16(len(self._tags))

            for tag, data in sorted(self._tags.items(), key=lambda x: x[0], reverse=reverse):
                content.writeUI16(tag)
                content.write(self._encodeData(data).encode())
                content.writeUI8(0x00)

        symbolClass = ByteArray()
        symbolClass.writeUI16(self.headerTagId)
        symbolClass.writeUI32(len(content))
        symbolClass.write(content)

        return symbolClass.get()

    def save(self, reverse=True):
        if self.symbolClass is not None:
            self.symbolClass.tags.clear()
            self.symbolClass.names.clear()

            for tag, data in sorted(self._tags.items(), key=lambda x: x[0], reverse=reverse):
                self.symbolClass.tags.add(JInt(tag))
                self.symbolClass.names.add(JString(self._encodeData(data)))

            self.symbolClass.setModified(True)
