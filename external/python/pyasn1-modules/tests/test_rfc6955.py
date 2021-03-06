#
# This file is part of pyasn1-modules software.
#
# Created by Russ Housley
# Copyright (c) 2019, Vigil Security, LLC
# License: http://snmplabs.com/pyasn1/license.html
#

import sys

from pyasn1.codec.der.decoder import decode as der_decode
from pyasn1.codec.der.encoder import encode as der_encode

from pyasn1.type import univ

from pyasn1_modules import pem
from pyasn1_modules import rfc5280
from pyasn1_modules import rfc5480
from pyasn1_modules import rfc6402
from pyasn1_modules import rfc6955

try:
    import unittest2 as unittest

except ImportError:
    import unittest


class CertificationRequestTestCase(unittest.TestCase):
    pem_text = """\
MIIDPDCCArsCAQAwTjELMAkGA1UEBhMCVVMxETAPBgNVBAoTCFhFVEkgSW5jMRAw
DgYDVQQLEwdUZXN0aW5nMRowGAYDVQQDExFQS0lYIEV4YW1wbGUgVXNlcjCCAkEw
ggG2BgcqhkjOPgIBMIIBqQKBgQCUhOBFbH9pUWI+VoB8aOfFqZ6edHSU7ZCMHcTh
ShSC9dKUDBnjuRC7EbnlpfuOIVFjAoaqBrghNrZ/Nt/R1mhbeXwdWhR1H2qTdZPO
u5dyivAPI51H9tSzx/D05vYrwjLhiWe+fgau+NABa4sq9QLXtqhjlIOwGzF9Uhre
5QOFJwKBgCamMixaK9QzK1zcBodTP5AGYVA4PtK5fYEcEhDFDFPUZNGOMAcIjN0/
Ci8s1ht/V4bQ2rtuNioY6NO8cDF6SLZOGG7dHyIG6z/q1EFp2ZveR5V6cpHSCX9J
XDsDM1HI8Tma/wTVbn6UPQO49jEVJkiVqFzeR4i0aToAp4ae2tHNAiEA6HL6lvAR
QPXy3P07XXiUsYUB5Wk3IfclubpxSvxgMPsCYQCjkQHAqG6kTaBW/Gz+H6ewzQ+U
hwwlvpd2jevlpAldq4PNgAs1Z38MjqcxmDKFOUCdEZjY3rh/hpuvjWc9tna0YS8h
4UsOaP9TPofd2HFWaEfc9yBjSzxfeHGD5nCe4pIwGgMVABzVOg0Xgm0KgXWBRhCO
PtsJ5Jg0AgE3A4GEAAKBgBNjoYUEjEaoiOv0XqiTdK79rp6WJxJlxEwHBj4Y/pS4
qHlIvS40tkfKBDCh7DP9GgstnlDJeA+uauy1a2q+slzasp94LLl34nkrJb8uC1lK
k0v4s+yBNK6XR1LgqCmY7NGwyitveovbTo2lFX5+rzNiCZ4PEUSMwY2iEZ5T77Lo
oCEwHwYJKoZIhvcNAQkOMRIwEDAOBgNVHQ8BAf8EBAMCAwgwDAYIKwYBBQUHBgMF
AANtADBqMFIwSDELMAkGA1UEBhMCVVMxETAPBgNVBAoTCFhFVEkgSW5jMRAwDgYD
VQQLEwdUZXN0aW5nMRQwEgYDVQQDEwtSb290IERTQSBDQQIGANo5tuLLBBQtBXf+
Xo9l9a+tyVybAsCoiClhYw==
"""

    def setUp(self):
        self.asn1Spec = rfc6402.CertificationRequest()

    def testDerCodec(self):
        substrate = pem.readBase64fromText(self.pem_text)
        asn1Object, rest = der_decode(substrate, asn1Spec=self.asn1Spec)
        assert not rest
        assert asn1Object.prettyPrint()
        assert der_encode(asn1Object) == substrate

        spki_a = asn1Object['certificationRequestInfo']['subjectPublicKeyInfo']['algorithm']
        assert spki_a['algorithm'] == rfc5480.dhpublicnumber
        assert spki_a['algorithm'] in rfc5280.algorithmIdentifierMap.keys()
        params, rest = der_decode(spki_a['parameters'], asn1Spec=rfc6955.DomainParameters())
        assert not rest
        assert params.prettyPrint()
        assert der_encode(params) == spki_a['parameters']
        assert params['validationParms']['pgenCounter'] == 55

        sig_a = asn1Object['signatureAlgorithm']
        assert sig_a['algorithm'] == rfc6955.id_dhPop_static_sha1_hmac_sha1
        assert sig_a['algorithm'] in rfc5280.algorithmIdentifierMap.keys()
        assert sig_a['parameters'] == der_encode(univ.Null(""))

    def testOpenTypes(self):
        substrate = pem.readBase64fromText(self.pem_text)
        asn1Object, rest = der_decode(substrate,
           asn1Spec=self.asn1Spec,
           decodeOpenTypes=True)
        assert not rest
        assert asn1Object.prettyPrint()
        assert der_encode(asn1Object) == substrate

        spki_a = asn1Object['certificationRequestInfo']['subjectPublicKeyInfo']['algorithm']
        assert spki_a['algorithm'] == rfc5480.dhpublicnumber
        assert spki_a['parameters']['validationParms']['pgenCounter'] == 55

        sig_a = asn1Object['signatureAlgorithm']
        assert sig_a['algorithm'] == rfc6955.id_dhPop_static_sha1_hmac_sha1
        assert sig_a['parameters'] == univ.Null("")


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    import sys

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
