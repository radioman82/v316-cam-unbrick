"""Check the real C parser/serializer and Zig PBKDF2 against independent vectors."""
import argparse
import hashlib
import re
import subprocess
import unittest

PARSER = None


class ConfigTests(unittest.TestCase):
    def run_config(self, data, mode=None, valid=True):
        if isinstance(data, str):
            data = data.encode('utf-8')
        result = subprocess.run([str(PARSER)] + ([mode] if mode else []), input=data, capture_output=True)
        self.assertEqual(result.returncode == 0, valid, result.stderr.decode(errors='replace'))
        return result.stdout

    def test_default_dhcp_and_roundtrip(self):
        source = 'ssid=Test WLAN\npassword=  literal # $() " \\ end  \n'
        out = self.run_config(source)
        self.assertIn(b'ip_mode=dhcp\n', out)
        self.assertIn(b'password=  literal # $() " \\ end  \n', out)
        self.assertEqual(self.run_config(out), out)

    def test_legacy_static_and_crlf(self):
        source = '\ufeffROUTER_SSID="Test WLAN"\r\nROUTER_PASS=\'Pass word #123\'\r\nCAM_IP="192.168.1.42"\r\nNETMASK=255.255.255.0\r\nGATEWAY=192.168.1.1\r\nSTREAM_PORT=8080\r\n'
        out = self.run_config(source)
        self.assertIn(b'ssid=Test WLAN\n', out)
        self.assertIn(b'ip_mode=static\n', out)
        self.assertIn(b'address=192.168.1.42\n', out)

    def test_psk_against_python(self):
        for ssid, password in [('IEEE', 'password'), ('WLAN Küche', '$(`not-a-command`) " \\ #')]:
            source = f'ssid={ssid}\npassword={password}\n'
            wpa = self.run_config(source, 'wpa').decode()
            expected = hashlib.pbkdf2_hmac('sha1', password.encode(), ssid.encode(), 4096, 32).hex()
            self.assertIn('    psk=' + expected + '\n', wpa)
            self.assertIn('    ssid=' + ssid.encode().hex() + '\n', wpa)
            self.assertNotIn(password, wpa)
            self.assertRegex(wpa, r'psk=[0-9a-f]{64}\n')

    def test_raw_psk(self):
        psk = 'a1' * 32
        self.assertIn(('psk=' + psk).encode(), self.run_config(f'ssid=Test\npassword={psk}\n', 'wpa'))

    def test_reject_malformed_inputs(self):
        base = b'ssid=Test\npassword=TestPass123\n'
        cases = [b'', base+b'ssid=Other\n', base+b'ROUTER_PASS=OtherPass\n', base+b'unknown=x\n',
                 b'ssid=Test\npassword=short\n', base+b'ip_mode=manual\n', base+b'http_port=8080;echo BAD\n',
                 base+b'http_port=0\n', base+b'http_port=65536\n', base+b'\x00', base+b'address=1\x1a2\n',
                 b'ssid=\xff\npassword=TestPass123\n', b'ssid=\xf0\x9f\npassword=TestPass123\n',
                 b'ssid='+b'x'*33+b'\npassword=TestPass123\n', base+b'#'+b'x'*4096,
                 b'ROUTER_SSID="Test";touch /tmp/bad\nROUTER_PASS=TestPass123\n',
                 base+b'ip_mode=static\naddress=192.168.1.42\nnetmask=255.0.255.0\n',
                 base+b'ip_mode=static\naddress=192.168.1.0\nnetmask=255.255.255.0\n',
                 base+b'ip_mode=static\naddress=192.168.1.42\nnetmask=255.255.255.0\ngateway=10.0.0.1\n']
        for value in cases:
            with self.subTest(value=value[:70]):
                self.run_config(value, valid=False)

    def test_ssid_and_password_boundaries(self):
        self.run_config('ssid='+'ä'*16+'\npassword=12345678\n')
        self.run_config('ssid='+'ä'*17+'\npassword=12345678\n', valid=False)
        self.run_config('ssid=Test\npassword='+'p'*63+'\n')
        self.run_config('ssid=Test\npassword='+'p'*64+'\n', valid=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parser')
    args = parser.parse_args()
    PARSER = args.parser
    unittest.main(argv=['test_config'], verbosity=2)
