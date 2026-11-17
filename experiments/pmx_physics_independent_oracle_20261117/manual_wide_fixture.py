"""New manually dimensioned531-byte UTF16/mixed-width fixture; no parser.

All expected offsets in the tests were worked from the record equations before
either oracle/candidate was called. Two bodies/joints make ordering observable.
This is an authored declaration challenge, not a renderable or physical model.
"""
import struct


BODY0 = ['00000080', '01000000', '4523c17f', '0000807f', '000080ff',
         '0000803f', '00000040', '00004040', '000080bf', '00000000',
         '0000803e', '0000003f', '0000003e', '0000403f']
BODY1 = ['0000003f'] * 14
JOINT0 = ['00000080', '01000000', '4523c17f', '0000807f'] + ['00000000'] * 20
JOINT1 = ['000080bf'] * 24


def i(value): return struct.pack('<i', value)
def text(hex_payload):
    raw = bytes.fromhex(hex_payload)
    return i(len(raw)) + raw
def words(values): return bytes.fromhex(''.join(values))


HEADER = b'PMX ' + bytes.fromhex('00000040') + bytes([8, 0, 0, 4, 2, 1, 2, 4, 4])
# Model strings and four empty prefix tables end at49, then two bones.
PREFIX = HEADER + i(0) * 4 + i(0) * 4 + i(2)
BONE0 = text('a89a') + text('') + b'\0' * 12 + b'\xff\xff' + i(0) + b'\0\0' + b'\0' * 12
BONE1 = text('a89a') + text('4100') + b'\0' * 12 + b'\0\0' + i(0) + b'\0\0' + b'\0' * 12
BODY_A = text('3275') + text('') + b'\xff\xff' + b'\x00' + b'\xff\xff' + b'\x00' + words(BODY0) + b'\x01'
BODY_B = text('') + text('4200') + b'\x01\x00' + b'\x0f' + b'\x00\x80' + b'\x02' + words(BODY1) + b'\x02'
JOINT_A = text('507d') + text('') + b'\x00' + i(0) + i(1) + words(JOINT0)
JOINT_B = text('') + text('4a00') + b'\x00' + i(-1) + i(0) + words(JOINT1)
DATA = PREFIX + BONE0 + BONE1 + i(0) + i(0) + i(2) + BODY_A + BODY_B + i(2) + JOINT_A + JOINT_B
assert len(PREFIX) == 53 and len(BONE0) == 42 and len(BONE1) == 44
assert len(BODY_A) == len(BODY_B) == 73 and len(JOINT_A) == len(JOINT_B) == 115 and len(DATA) == 531
