"""Translate OS proxy settings and trusted OS certificates for private Java.
No verification bypass, no mutation of global Java or the user's certificate store.
"""
import hashlib, os, ssl, urllib.request, urllib.parse
from pathlib import Path

def java_network(java_home: Path, base: Path, runner, env):
    args=[]
    for scheme,url in urllib.request.getproxies().items():
        if scheme not in ('http','https'):continue
        p=urllib.parse.urlparse(url if '://' in url else 'http://'+url)
        if p.username or p.password:raise ValueError('Authenticated proxy is not supported automatically')
        if p.hostname:
            args.extend([f'-D{scheme}.proxyHost={p.hostname}',f'-D{scheme}.proxyPort={p.port or 80}'])
    certs=set(ssl.create_default_context().get_ca_certs(binary_form=True))
    # Windows Python exposes the native root store even with embedded distribution.
    if os.name=='nt':
        for name in ('ROOT','CA'):
            for cert,encoding,trust in ssl.enum_certificates(name):
                if encoding=='x509_asn' and (trust is True or '1.3.6.1.5.5.7.3.1' in trust):certs.add(cert)
    if not certs:return args
    digest=hashlib.sha256(b''.join(sorted(certs))).hexdigest()[:20]
    trust=base/f'os-trust-{digest}.p12'
    if not trust.exists():
        import shutil
        shutil.copy2(java_home/'lib/security/cacerts',trust)
        keytool=java_home/'bin'/('keytool.exe' if os.name=='nt' else 'keytool')
        try:
            for cert in sorted(certs):
                alias=hashlib.sha256(cert).hexdigest()
                pem=base/'current-cert.der';pem.write_bytes(cert)
                try:runner.run([keytool,'-importcert','-noprompt','-trustcacerts','-alias','os-'+alias,'-file',pem,'-keystore',trust,'-storepass','changeit'],base,env,timeout=30)
                finally:pem.unlink(missing_ok=True)
        except Exception:trust.unlink(missing_ok=True);raise
    args.extend(['-Djavax.net.ssl.trustStore='+str(trust),'-Djavax.net.ssl.trustStorePassword=changeit'])
    return args
