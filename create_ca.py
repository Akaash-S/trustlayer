from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import datetime
import os

def generate_ca():
    cert_dir = os.path.abspath("certs")
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)

    print("Generating CA key...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    print("Generating CA certificate...")
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"mitmproxy"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"mitmproxy"),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=3650)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True,
    ).sign(
        private_key, hashes.SHA256(), default_backend()
    )

    # Save Private Key + Cert (PEM format) - mitmproxy-ca.pem
    pem_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    pem_cert = cert.public_bytes(serialization.Encoding.PEM)

    with open(os.path.join(cert_dir, "mitmproxy-ca.pem"), "wb") as f:
        f.write(pem_key)
        f.write(pem_cert)

    # Save Cert Only (CER format for Windows) - mitmproxy-ca-cert.cer
    # Windows accepts PEM formatted certs with .cer extension too usually, 
    # but strictly .cer is often DER. mitmproxy page provides PEM renamed.
    # We will write PEM to .cer as that's what mitmproxy docs imply for the download.
    with open(os.path.join(cert_dir, "mitmproxy-ca-cert.cer"), "wb") as f:
        f.write(pem_cert)
        
    print(f"Success! Certificates saved to {cert_dir}")

if __name__ == "__main__":
    generate_ca()
