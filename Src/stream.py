import struct

class Stream:

    def __init__(self, data='', byteOrder='@'):
        self.position = 0
        self.data = data
        self.size = len(self.data)
        self.byteOrder = byteOrder

    def __str__(self):
        return str(self.data)

    def __len__(self):
        return self.size

    def read(self, format):
        value = struct.unpack_from(self.byteOrder + format, self.data, self.position)
        self.position += struct.calcsize(format)
        return value

    def write(self, format, *value):
        self.data += struct.pack((self.byteOrder + format), *value)
        self.size = len(self.data)

    def skipData(self, size):
        self.position += size

    def hasData(self):
        return self.position < self.size

    def dataLeft(self):
        return self.size - self.position

    def atEnd(self):
        return self.position == self.size

    def readData(self, size):
        return self.read(('{0}s').format(size))[0]

    def writeData(self, value, size):
        self.write(('{0}s').format(size), value)

    def readBool(self):
        return self.read('?')[0]

    def writeBool(self, value):
        self.write('?', value)

    def readString(self):
        return self.readData(self.readLong())

    def writeString(self, value):
        self.writeLong(len(value))
        self.writeData(value, len(value))

    def readByte(self, signed=False):
        return self.read('b' if signed else 'B')[0]

    def writeByte(self, value, signed=False):
        self.write('b' if signed else 'B', value)

    def readShort(self, signed=False):
        return self.read('h' if signed else 'H')[0]

    def writeShort(self, value, signed=False):
        self.write('h' if signed else 'H', value)

    def readLong(self, signed=False):
        return self.read('l' if signed else 'L')[0]

    def writeLong(self, value, signed=False):
        self.write('l' if signed else 'L', value)

    def readFloat(self):
        return self.read('f')[0]

    def writeFloat(self, value):
        self.write('f', value)
# okay decompiling stream.pyo
