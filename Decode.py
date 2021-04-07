from json import JSONDecoder, JSONDecodeError
import re

def decode_stacked(document, pos=0, decoder=JSONDecoder()):
    try:
        NOT_WHITESPACE = re.compile(r'[^\s]')
        while True:
            match = NOT_WHITESPACE.search(document, pos)
            if not match:
                return
            pos = match.start()

            try:
                obj, pos = decoder.raw_decode(document, pos)
            except JSONDecodeError:
            # do something sensible if there's some error
                raise "decode_stacked problem"
            yield obj
    except:
        raise "decode_stacked fallita"
