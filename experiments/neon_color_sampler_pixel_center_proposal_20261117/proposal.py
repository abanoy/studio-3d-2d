"""One call-site proposal only; returns bytes and never writes product sources."""
import hashlib

ORIGINAL_SHA256 = '7c2150ad2a5221bf3e81cad758cea609f46d414e8e2761c9b50cfb82598bf141'
BEFORE = b'\t\tvar wanted:=reference_pixel.get_pixel(int(native_point.x),int(native_point.y));var count: int=picker.captures;picker.arm();click(native_point);await settled()\r\n'
AFTER = BEFORE.replace(b'click(native_point)', b'click(native_point+Vector2(.5,.5))', 1)


def corrected_test(raw_bytes):
    assert type(raw_bytes) is bytes and hashlib.sha256(raw_bytes).hexdigest() == ORIGINAL_SHA256
    assert raw_bytes.count(BEFORE) == 1 and AFTER not in raw_bytes
    result = raw_bytes.replace(BEFORE, AFTER, 1)
    assert result.replace(AFTER, BEFORE, 1) == raw_bytes
    assert [line for line in result.splitlines(keepends=True) if b'check(' in line] == [line for line in raw_bytes.splitlines(keepends=True) if b'check(' in line]
    assert result.count(b'\r\n') == raw_bytes.count(b'\r\n')
    return result
