from OpenSSL import crypto
import sys
from pathlib import Path

def generate_cert(path: Path):
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)

    cert = crypto.X509()
    cert.get_subject().CN = 'localhost'
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')

    # Write private key then certificate into a single PEM file usable by runserver_plus
    with open(path, 'wb') as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    print(f'Wrote {path}')


if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('cert.pem')
    generate_cert(out)
