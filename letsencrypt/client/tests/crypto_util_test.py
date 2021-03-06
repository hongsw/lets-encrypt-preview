"""Tests for letsencrypt.client.crypto_util."""
import datetime
import os
import pkg_resources
import unittest

import M2Crypto


RSA256_KEY = pkg_resources.resource_string(__name__, 'testdata/rsa256_key.pem')
RSA512_KEY = pkg_resources.resource_string(__name__, 'testdata/rsa512_key.pem')


class CreateSigTest(unittest.TestCase):
    """Tests for letsencrypt.client.crypto_util.create_sig."""

    def setUp(self):
        self.nonce = '\xec\xd6\xf2oYH\xeb\x13\xd5#q\xe0\xdd\xa2\x92\xa9'
        self.b64nonce = '7Nbyb1lI6xPVI3Hg3aKSqQ'
        self.signature = {
            'nonce': self.b64nonce,
            'alg': 'RS256',
            'jwk': {
                'kty': 'RSA',
                'e': 'AQAB',
                'n': 'rHVztFHtH92ucFJD_N_HW9AsdRsUuHUBBBDlHwNlRd3fp5'
                     '80rv2-6QWE30cWgdmJS86ObRz6lUTor4R0T-3C5Q',
            },
            'sig': 'SUPYKucUnhlTt8_sMxLiigOYdf_wlOLXPI-o7aRLTsOquVjDd6r'
                   'AX9AFJHk-bCMQPJbSzXKjG6H1IWbvxjS2Ew',
        }

    def _call(self, *args, **kwargs):
        from letsencrypt.client.crypto_util import create_sig
        return create_sig(*args, **kwargs)

    def test_it(self):
        self.assertEqual(
            self._call('message', RSA256_KEY, self.nonce), self.signature)

    def test_random_nonce(self):
        signature = self._call('message', RSA256_KEY)
        signature.pop('sig')
        signature.pop('nonce')
        del self.signature['sig']
        del self.signature['nonce']
        self.assertEqual(signature, self.signature)


class ValidCSRTest(unittest.TestCase):
    """Tests for letsencrypt.client.crypto_util.valid_csr."""

    def _call(self, csr):
        from letsencrypt.client.crypto_util import valid_csr
        return valid_csr(csr)

    def _call_testdata(self, name):
        return self._call(pkg_resources.resource_string(
            __name__, os.path.join('testdata', name)))

    def test_valid_pem_true(self):
        self.assertTrue(self._call_testdata('csr.pem'))

    def test_valid_pem_san_true(self):
        self.assertTrue(self._call_testdata('csr-san.pem'))

    def test_valid_der_false(self):
        self.assertFalse(self._call_testdata('csr.der'))

    def test_valid_der_san_false(self):
        self.assertFalse(self._call_testdata('csr-san.der'))

    def test_empty_false(self):
        self.assertFalse(self._call(''))

    def test_random_false(self):
        self.assertFalse(self._call('foo bar'))


class CSRMatchesPubkeyTest(unittest.TestCase):
    """Tests for letsencrypt.client.crypto_util.csr_matches_pubkey."""

    def _call_testdata(self, name, privkey):
        from letsencrypt.client.crypto_util import csr_matches_pubkey
        return csr_matches_pubkey(pkg_resources.resource_string(
            __name__, os.path.join('testdata', name)), privkey)

    def test_valid_true(self):
        self.assertTrue(self._call_testdata('csr.pem', RSA256_KEY))

    def test_invalid_false(self):
        self.assertFalse(self._call_testdata('csr.pem', RSA512_KEY))


class MakeKeyTest(unittest.TestCase):
    """Tests for letsencrypt.client.crypto_util.make_key."""

    def test_it(self):
        from letsencrypt.client.crypto_util import make_key
        M2Crypto.RSA.load_key_string(make_key(1024))


class ValidPrivkeyTest(unittest.TestCase):
    """Tests for letsencrypt.client.crypto_util.valid_privkey."""

    def _call(self, privkey):
        from letsencrypt.client.crypto_util import valid_privkey
        return valid_privkey(privkey)

    def test_valid_true(self):
        self.assertTrue(self._call(RSA256_KEY))

    def test_empty_false(self):
        self.assertFalse(self._call(''))

    def test_random_false(self):
        self.assertFalse(self._call('foo bar'))


class MakeSSCertTest(unittest.TestCase):
    """Tests for letsencrypt.client.crypto_util.make_ss_cert."""

    def test_it(self):
        from letsencrypt.client.crypto_util import make_ss_cert
        make_ss_cert(RSA256_KEY, ['example.com', 'www.example.com'])


class GetCertInfoTest(unittest.TestCase):
    """Tests for letsencrypt.client.crypto_util.get_cert_info."""

    def setUp(self):
        self.cert_info = {
            'not_before': datetime.datetime(
                2014, 12, 11, 22, 34, 45, tzinfo=M2Crypto.ASN1.UTC),
            'not_after': datetime.datetime(
                2014, 12, 18, 22, 34, 45, tzinfo=M2Crypto.ASN1.UTC),
            'subject': 'C=US, ST=Michigan, L=Ann Arbor, O=University '
                       'of Michigan and the EFF, CN=example.com',
            'cn': 'example.com',
            'issuer': 'C=US, ST=Michigan, L=Ann Arbor, O=University '
                      'of Michigan and the EFF, CN=example.com',
            'serial': 1337L,
            'pub_key': 'RSA 512',
        }

    def _call(self, name):
        from letsencrypt.client.crypto_util import get_cert_info
        self.assertEqual(get_cert_info(pkg_resources.resource_filename(
            __name__, os.path.join('testdata', name))), self.cert_info)

    def test_single_domain(self):
        self.cert_info.update({
            'san': '',
            'fingerprint': '9F8CE01450D288467C3326AC0457E351939C72E',
        })
        self._call('cert.pem')

    def test_san(self):
        self.cert_info.update({
            'san': 'DNS:example.com, DNS:www.example.com',
            'fingerprint': '62F7110431B8E8F55905DBE5592518F9634AC50A',
        })
        self._call('cert-san.pem')


class B64CertToPEMTest(unittest.TestCase):
    """Tests for letsencrypt.client.crypto_util.b64_cert_to_pem."""

    def test_it(self):
        from letsencrypt.client.crypto_util import b64_cert_to_pem
        self.assertEqual(
            b64_cert_to_pem(pkg_resources.resource_string(
                __name__, 'testdata/cert.b64jose')),
            pkg_resources.resource_string(__name__, 'testdata/cert.pem'))


if __name__ == '__main__':
    unittest.main()
