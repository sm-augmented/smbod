# Space Marine BOD converter
Decompiled and modified with proper hashing algorithm Santos' smbod tool that converts BOD files into XML and visa versa, decompresses and compresses BOD files.

## Usage
Requires Python 2.7 and now expects [smhasher](https://github.com/sm-augmented/smhasher) to be built and placed near smbod.py.

Decompress mode is typically used to load model-related BODs (.bmat, .o3d, .object-manifest) that are compressed by default into 3ds Max with Santos' Space Marine 3ds Max scripts.