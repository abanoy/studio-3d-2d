"""Pure CPU bounded-reader successor checks; synthetic files only, no native calls."""
import hashlib
import stat
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import run_carrier as driver


def info(**changes):
    values=dict(st_dev=7,st_ino=11,st_size=3,st_mtime_ns=123456,st_nlink=1,
                st_mode=stat.S_IFREG|0o600,st_file_attributes=0x20)
    values.update(changes)
    return types.SimpleNamespace(**values)


class Stream:
    def __init__(self,payload):self.payload,self.requests,self.closed=payload,[],False
    def __enter__(self):return self
    def __exit__(self,*args):self.closed=True;return False
    def fileno(self):return 81
    def read(self,amount):self.requests.append(amount);return self.payload[:amount]


class FakePath:
    def __init__(self,payload=b'abc',before=None,after=None):
        self.before=before or info();self.after=after or self.before
        self.stream=Stream(payload);self.stats=0;self.opens=0
    def lstat(self):
        self.stats+=1
        return self.before if self.stats==1 else self.after
    def open(self,mode):
        if mode!='rb':raise AssertionError('must only read')
        self.opens+=1;return self.stream


class ReaderTests(unittest.TestCase):
    def read(self,path,pin=None,limit=driver.MAX_READ,opened=None,final_open=None):
        with patch.object(driver,'safe',side_effect=lambda value:value), \
             patch.object(driver.os,'fstat',side_effect=[opened or path.before,final_open or path.before]):
            return driver.read_checked(path,pin,limit)

    def test_small_file_requests_only_admitted_size_plus_one(self):
        path=FakePath()
        raw,row,_stamp=self.read(path)
        self.assertEqual(path.stream.requests,[4])
        self.assertEqual(raw,b'abc')
        self.assertEqual(row['sha256'],hashlib.sha256(raw).hexdigest())
        self.assertTrue(path.stream.closed)

    def test_locked_zero_byte_file_uses_one_byte_request_and_exact_empty_hash(self):
        path=FakePath(b'',info(st_size=0))
        raw,row,_stamp=self.read(path,(0,hashlib.sha256(b'').hexdigest()))
        self.assertEqual(path.stream.requests,[1])
        self.assertEqual(raw,b'')
        self.assertEqual(row['bytes'],0)

    def test_exact_custom_cap_still_requests_one_growth_detection_byte(self):
        path=FakePath(b'abcdefgh',info(st_size=8))
        raw,_row,_stamp=self.read(path,limit=8)
        self.assertEqual(raw,b'abcdefgh')
        self.assertEqual(path.stream.requests,[9])

    def test_oversize_refuses_before_open_or_buffer_request(self):
        path=FakePath(b'',info(st_size=9))
        with self.assertRaisesRegex(driver.Refusal,'^FILE_TYPE_OR_SIZE$'):self.read(path,limit=8)
        self.assertEqual(path.opens,0)
        self.assertEqual(path.stream.requests,[])

    def test_wrong_literal_size_still_refuses_before_open(self):
        path=FakePath()
        with self.assertRaisesRegex(driver.Refusal,'^BEFORE_READ_LITERAL_PIN_OR_SIZE_DIFFERS$'):
            self.read(path,(2,hashlib.sha256(b'ab').hexdigest()))
        self.assertEqual(path.opens,0)

    def test_growth_is_detected_even_if_stamp_were_restored_and_more_data_exists(self):
        path=FakePath(b'abcdef')
        with self.assertRaisesRegex(driver.Refusal,'^READ_CHANGED_FILE$'):self.read(path)
        self.assertEqual(path.stream.requests,[4])
        self.assertTrue(path.stream.closed)

    def test_shrink_is_detected_even_if_stamp_were_restored(self):
        path=FakePath(b'ab')
        with self.assertRaisesRegex(driver.Refusal,'^READ_CHANGED_FILE$'):self.read(path)
        self.assertEqual(path.stream.requests,[4])

    def test_opened_identity_change_refuses_without_read(self):
        path=FakePath()
        with self.assertRaisesRegex(driver.Refusal,'^FILE_CHANGED_BEFORE_READ$'):
            self.read(path,opened=info(st_ino=12))
        self.assertEqual(path.stream.requests,[])
        self.assertTrue(path.stream.closed)

    def test_after_read_identity_stamp_or_other_attribute_drift_still_refuses(self):
        for key,value in (('st_dev',8),('st_ino',12),('st_size',4),('st_mtime_ns',123457),
                          ('st_nlink',2),('st_file_attributes',0x21),('st_file_attributes',0x420)):
            with self.subTest(key=key,value=value):
                path=FakePath()
                with self.assertRaisesRegex(driver.Refusal,'^READ_CHANGED_FILE$'):
                    self.read(path,final_open=info(**{key:value}))
                self.assertEqual(path.stream.requests,[4])

    def test_final_path_replacement_or_rewrite_still_refuses(self):
        for change in (dict(st_ino=12),dict(st_mtime_ns=123457),dict(st_size=4)):
            with self.subTest(change=change):
                path=FakePath(after=info(**change))
                with self.assertRaisesRegex(driver.Refusal,'^READ_CHANGED_FILE$'):self.read(path)
                self.assertEqual(path.stream.requests,[4])

    def test_same_length_wrong_bytes_with_stable_stamps_still_fail_literal_hash(self):
        path=FakePath(b'axc')
        with self.assertRaisesRegex(driver.Refusal,'^LITERAL_PIN_DIFFERS$'):
            self.read(path,(3,hashlib.sha256(b'abc').hexdigest()))
        self.assertEqual(path.stream.requests,[4])

    def test_only_approved_recall_hint_can_change_in_stable_identity(self):
        path=FakePath(before=info(st_file_attributes=0x40020),after=info())
        raw,_row,_stamp=self.read(path,opened=info(),final_open=info())
        self.assertEqual(raw,b'abc')
        self.assertEqual(path.stream.requests,[4])

    def test_real_zero_and_small_regular_file_roundtrip_with_exact_pins(self):
        calls=[]
        original=Path.open
        class Counted:
            def __init__(self,stream):self.stream=stream
            def __enter__(self):self.stream.__enter__();return self
            def __exit__(self,*args):return self.stream.__exit__(*args)
            def fileno(self):return self.stream.fileno()
            def read(self,amount):calls.append(amount);return self.stream.read(amount)
        def open_counted(path,*args,**kwargs):return Counted(original(path,*args,**kwargs))
        with tempfile.TemporaryDirectory(prefix='has-read-amount-synthetic-') as temporary:
            for index,payload in enumerate((b'',b'abc',bytes(range(256))*4)):
                path=Path(temporary)/str(index);path.write_bytes(payload)
                before=path.stat()
                with patch.object(Path,'open',open_counted):
                    raw,row,_stamp=driver.read_checked(path,(len(payload),hashlib.sha256(payload).hexdigest()))
                self.assertEqual(raw,payload)
                self.assertEqual(row['bytes'],len(payload))
                self.assertEqual(path.stat().st_mtime_ns,before.st_mtime_ns)
        self.assertEqual(calls,[1,4,1025])


if __name__=='__main__':unittest.main()
