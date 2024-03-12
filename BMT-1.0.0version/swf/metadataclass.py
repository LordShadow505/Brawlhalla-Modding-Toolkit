import json
from typing import Union
from .bytearray import ByteArray
from ffdec.classes import MetadataTag


class MetadataClass:
    headerTagId = 0x137f

    def __init__(self, metadataClassTag=None):
        self.metadata = metadataClassTag
        self.data = {}

        if isinstance(self.metadata, MetadataTag):
            try:
                self.data = json.loads(str(self.metadata.xmlMetadata))
            except json.decoder.JSONDecodeError:
                pass

    def set(self, data: Union[list, dict]):
        if isinstance(data, (list, dict)):
            self.data = data

    def get(self) -> Union[list, dict]:
        return self.data.copy()

    def save(self):
        if isinstance(self.metadata, MetadataTag):
            self.metadata.xmlMetadata = json.dumps(self.data)
            self.metadata.setModified(True)

    def getByteArray(self) -> bytearray:
        content = bytearray(json.dumps(self.data).encode("UTF-8"))

        metadata = ByteArray()
        metadata.writeUI16(self.headerTagId)
        metadata.writeUI32(len(content))
        metadata.write(content)

        return metadata.get()
