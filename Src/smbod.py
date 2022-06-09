"""
Name: smbod
Version: 0.2.0
Author: Santos, ex-Naradius
E-mail: santostools@gmail.com

Description:
------------
This script can convert Space Marine game BOD files into XML format and convert back from XML to BOD.

Usage:
------
smbod [-d] [-c extension_list] [-x] [-b] source_path
        
Options:
        -d      Decompress BOD file or files
        -c      Compress BOD file or files with extensions from extension list
        -x      Decode from BOD to XML
        -b      Encode from XML to BOD

Change Log:
-----------
Version 0.2.0
+ proper hashing algorithm used for strings
Version 0.1.0
+ first release
"""

import os, sys, zlib, hashlib, getopt
from stream import Stream
from collections import OrderedDict
import xml.dom.minidom

types = {1: 'object', 
   2: 'int', 
   3: 'float', 
   4: 'bool', 
   5: str(5), 
   7: 'object', 
   9: 'array', 
   11: 'vector', 
   13: str(13), 
   15: 'hstring', 
   254: str(254), 
   255: str(255)}
typeNames = {'object': 1, 
   'int': 2, 
   'float': 3, 
   'bool': 4, 
   str(5): 5, 
   'object': 7, 
   'array': 9, 
   'vector': 11, 
   str(13): 13, 
   'hstring': 15, 
   str(254): 254, 
   str(255): 255}

def readString(stream, strings):
    hash = stream.readData(8)
    return strings[hash]


def readObject(stream, strings, doc, parent=None):
    assert stream.readByte() == 1
    cls = readString(stream, strings)
    count = stream.readLong()
    objName = 'Element' if parent else 'Object'
    object = doc.createElement(objName)
    object.setAttribute('Class', cls)
    object.setAttribute('Type', types[1])
    if parent:
        parent.appendChild(object)
    for i in range(count):
        name = readString(stream, strings)
        property = readProperty(stream, strings, doc, object)
        property.setAttribute('Name', name)
        object.appendChild(property)

    return object


def readProperty(stream, strings, doc, parent):
    type = stream.readByte()
    property = None
    if type != 7:
        property = doc.createElement('Property')
        property.setAttribute('Type', types[type])
    if type == 2:
        property.setAttribute('Value', str(stream.readLong(True)))
    elif type == 3:
        property.setAttribute('Value', str(stream.readFloat()))
    elif type == 4:
        property.setAttribute('Value', str.lower(str(stream.readBool())))
    elif type == 5:
        property.setAttribute('Value', readString(stream, strings))
    elif type == 7:
        id = stream.readLong()
        property = readObject(stream, strings, doc, parent)
        property.setAttribute('ID', str(id))
    elif type == 9:
        count = stream.readLong()
        flag = stream.readByte()
        for i in range(count):
            name = None
            if flag == 1:
                assert stream.readByte() == 5
                name = readString(stream, strings)
            prop = readProperty(stream, strings, doc, parent)
            if name:
                prop.setAttribute('Name', name)
            property.appendChild(prop)

    elif type == 11:
        count = stream.readLong()
        for i in range(count):
            prop = readProperty(stream, strings, doc, parent)
            property.appendChild(prop)

    elif type == 13:
        property.setAttribute('Value', stream.readData(8).encode('hex'))
    elif type == 15:
        property.setAttribute('Value', readString(stream, strings))
    elif type == 254:
        pass
    elif type == 255:
        property.setAttribute('Value', str(stream.readLong()))
    else:
        raise Exception(('Unknown property type: {0}!').format(type))
    return property


def guid(string):
    hash = os.popen("SpaceMarineHasher " + string.lower()).read().decode("hex")
    return str(hash)


def writeString(stream, strings, string):
    string = str(string)
    if string not in strings:
        id = guid(string)
        strings[string] = id
    stream.writeData(strings[string], 8)


def writeObject(stream, strings, object, id):
    stream.writeByte(1)
    writeString(stream, strings, object.getAttribute('Class'))
    stream.writeLong(len(object.childNodes))
    for child in object.childNodes:
        writeString(stream, strings, child.getAttribute('Name'))
        writeProperty(stream, strings, child, id)


def writeProperty(stream, strings, property, id):
    type = typeNames[property.getAttribute('Type')]
    stream.writeByte(type)
    if type == 2:
        stream.writeLong(int(property.getAttribute('Value')), True)
    elif type == 3:
        stream.writeFloat(float(property.getAttribute('Value')))
    elif type == 4:
        stream.writeBool(property.getAttribute('Value') == 'true')
    elif type == 5:
        writeString(stream, strings, property.getAttribute('Value'))
    elif type == 7:
        stream.writeLong(id[0])
        id[0] += 1
        writeObject(stream, strings, property, id)
    elif type == 9:
        stream.writeLong(len(property.childNodes))
        stream.writeBool(property.childNodes and property.childNodes[0].getAttribute('Name'))
        for child in property.childNodes:
            name = child.getAttribute('Name')
            if name:
                stream.writeByte(5)
                writeString(stream, strings, name)
            writeProperty(stream, strings, child, id)

    elif type == 11:
        stream.writeLong(len(property.childNodes))
        for child in property.childNodes:
            writeProperty(stream, strings, child, id)

    elif type == 13:
        stream.writeData(property.getAttribute('Value').decode('hex'), 8)
    elif type == 15:
        writeString(stream, strings, property.getAttribute('Value'))
    elif type == 254:
        pass
    elif type == 255:
        stream.writeLong(int(property.getAttribute('Value')))
    else:
        raise Exception(('Unknown property type: {0}!').format(type))


def trimNode(parent):
    for child in parent.childNodes[:]:
        if child.nodeType == xml.dom.Node.TEXT_NODE and child.data.strip() == '':
            parent.removeChild(child)
        else:
            trimNode(child)


def loadFile(path):
    file = open(path, 'rb')
    stream = Stream(file.read())
    file.close()
    data = ''
    if stream.readData(3) == 'BOD':
        stream.readByte()
        stream.readByte()
        compressed = stream.readByte()
        stream.readLong()
        if compressed:
            size = stream.readLong()
            data = zlib.decompress(stream.readData(stream.dataLeft()))
            assert len(data) == size
        else:
            data = stream.readData(stream.dataLeft())
    return Stream(data)


def compress(path):
    stream = loadFile(path)
    if len(stream) > 0:
        print ('Compressing {0}...').format(path)
        out = Stream()
        out.writeData('BOD', 3)
        out.writeByte(253)
        out.writeByte(2)
        out.writeByte(1)
        out.writeLong(1)
        out.writeLong(len(stream))
        data = zlib.compress(str(stream), 9)
        out.writeData(data, len(data))
        with open(path, 'wb') as (file):
            file.write(str(out))


def decompress(path):
    stream = loadFile(path)
    if len(stream) > 0:
        print ('Decompressing {0}...').format(path)
        out = Stream()
        out.writeData('BOD', 3)
        out.writeByte(253)
        out.writeByte(2)
        out.writeByte(0)
        out.writeLong(1)
        out.writeData(str(stream), len(stream))
        with open(path, 'wb') as (file):
            file.write(str(out))


def decode(path):
    stream = loadFile(path)
    if len(stream) > 0:
        print ('Decoding {0}...').format(path)
        numStrings = stream.readLong()
        maxLength = stream.readLong()
        strings = {}
        for i in range(numStrings):
            id = stream.readData(8)
            name = stream.readString()
            strings[id] = name

        doc = xml.dom.minidom.Document()
        doc.appendChild(readObject(stream, strings, doc))
        assert stream.position == len(stream)
        with open(path + '.xml', 'wt') as (file):
            doc.writexml(file, addindent='\t', newl='\n', encoding='UTF-8')


def encode(path):
    print ('Encoding {0}...').format(path)
    doc = xml.dom.minidom.parse(path)
    trimNode(doc.documentElement)
    stream = Stream()
    stream.writeData('BOD', 3)
    stream.writeByte(253)
    stream.writeByte(2)
    stream.writeByte(0)
    stream.writeLong(1)
    strings = OrderedDict()
    data = Stream()
    writeObject(data, strings, doc.documentElement, [0])
    stream.writeLong(len(strings))
    stream.writeLong(len(max(strings, key=len)) if strings else 0)
    for string, id in strings.iteritems():
        stream.writeData(id, 8)
        stream.writeString(string)

    with open(os.path.splitext(path)[0], 'wb') as (file):
        file.write(str(stream))
        file.write(str(data))


def usage():
    print '\nUsage: smbod [-d] [-c extension_list] [-x] [-b] source_path'
    print '\nOptions: '
    print '\t-d\tDecompress BOD file or files'
    print '\t-c\tCompress BOD file or files with extensions from extension list'
    print '\t-x\tDecode from BOD to XML'
    print '\t-b\tEncode from XML to BOD'


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'dc:xb')
        if not opts:
            usage()
            sys.exit()
        extensions = []
        for opt, arg in opts:
            function = None
            if opt == '-d':
                function = decompress
            elif opt == '-c':
                function = compress
                extensions = arg.split()
            elif opt == '-x':
                function = decode
            elif opt == '-b':
                function = encode
                extensions = ['xml']
            src = args[0] if args else os.getcwd()
            if os.path.isdir(src):
                for root, dirs, files in os.walk(src):
                    for name in files:
                        path = os.path.join(root, name)
                        if not extensions or os.path.splitext(path)[1].lstrip('.') in extensions:
                            function(path)

            elif not extensions or os.path.splitext(src)[1].lstrip('.') in extensions:
                function(src)

    except getopt.GetoptError as err:
        print 'Error: ' + str(err)
        usage()
# okay decompiling smbod.py.pyc
