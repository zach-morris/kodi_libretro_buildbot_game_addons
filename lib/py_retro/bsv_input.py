"""
Read input from a bsnes movie file (*.bsv)
"""
from struct import Struct, error as StructError
from binascii import crc32

BSV_MAGIC = b'BSV1'
HEADER_STRUCT = Struct('<4s3I')
RECORD_STRUCT = Struct('<h')

# Due to poorly-worded documentation, some versions of SSNES produce BSV files
# with the magic number reversed. Such files are otherwise fine, so we'll
# accept them.
BSV_SSNES_MAGIC = b'1VSB'


class CorruptFile(Exception):
    pass


class CartMismatch(Exception):
    pass


class BSV:
    """
    Iterate the contents of the given BSV file.

    filenameOrHandle should either be a string containing the path to a BSV
    file, or a file-like object containing a BSV file.

    Once we've reached the end of the input recorded in the BSV file, we just
    yield an infinite stream of zeroes.
    """

    def __init__(self, filenameOrHandle):
        if isinstance(filenameOrHandle, str):
            self.handle = open(filenameOrHandle, 'rb')
        else:
            self.handle = filenameOrHandle

        # Read and sanity-check the header.
        magic, serializerVersion, cartCRC, stateSize = self._extract(HEADER_STRUCT)

        if magic not in (BSV_MAGIC, BSV_SSNES_MAGIC):
            raise CorruptFile("File %r has bad magic %r, expected %r"
                    % (filenameOrHandle, magic, BSV_MAGIC))

        self.serializer_version = serializerVersion
        self.cart_crc = cartCRC
        self.state_data = self.handle.read(stateSize)

        self.active = True

    def _extract(self, s):
        """
        Read an instance of the given structure from the given file handle.
        """
        return s.unpack(self.handle.read(s.size))

    def input_state(self, port, device, index, id_):
        if self.active:
            try:
                return self._extract(RECORD_STRUCT)[0]
            except StructError:
                # end of the file
                self.active = False
        return 0


def set_input_state_file(core, filename, restore=True, expectedCartCRC=None):
    """
    Sets the BSV file containing the log of input states.

    !!! Also restores the savestate contained in the file !!!
    !!! unless the argument 'restore' is set to False.    !!!

    Unlike core.EmulatedSNES.set_input_state_cb, this function takes a
    filename to use, rather than a function.
    """

    bsv = BSV(filename)

    if expectedCartCRC is not None and bsv.cart_crc != expectedCartCRC:
        raise CartMismatch("Movie is for cart with CRC32 %r, expected %r"
                % (bsv.cart_crc, expectedCartCRC))

    if restore:
        # retry loop for the multi-threaded ParaLLEl-N64,
        # which refuses to load state while 'initializing'
        for i in range(100):
            # noinspection PyBroadException
            try:
                core.unserialize(bsv.state_data)
                break
            except:
                if i == 99:
                    raise
                core.run()

    core.set_input_state_cb(bsv.input_state)
    return bsv

