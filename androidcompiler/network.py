"""Private Java proxy/TLS setup: a single bounded process, atomic verified cache.
TLS verification and Java's disabled-algorithm policy remain enabled.
"""
import hashlib, json, os, ssl, tempfile, urllib.request, urllib.parse
from pathlib import Path

TRUST_BUILDER = r'''
import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.security.cert.Certificate;
import java.security.cert.CertificateFactory;
import java.util.*;
class BuildTrust {
    static String fingerprint(Certificate cert) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(cert.getEncoded()));
    }
    public static void main(String[] args) throws Exception {
        char[] password = "changeit".toCharArray();
        KeyStore defaults = KeyStore.getInstance(new File(args[0]), password);
        KeyStore combined = KeyStore.getInstance("PKCS12");
        combined.load(null, password);
        Set<String> known = new HashSet<>();
        for (Enumeration<String> aliases = defaults.aliases(); aliases.hasMoreElements();) {
            String alias = aliases.nextElement();
            Certificate cert = defaults.getCertificate(alias);
            if (cert != null) {
                combined.setCertificateEntry(alias, cert);
                known.add(fingerprint(cert));
            }
        }
        Collection<? extends Certificate> certificates;
        try (InputStream in = Files.newInputStream(Path.of(args[1]))) {
            certificates = CertificateFactory.getInstance("X.509").generateCertificates(in);
        }
        int done = 0, added = 0;
        for (Certificate cert : certificates) {
            String id = fingerprint(cert);
            if (known.add(id)) { combined.setCertificateEntry("os-" + id, cert); added++; }
            done++;
            if (done % 50 == 0 || done == certificates.size())
                System.out.println("TLS certificates: " + done + "/" + certificates.size());
        }
        try (OutputStream out = Files.newOutputStream(Path.of(args[2]))) { combined.store(out, password); }
        // Read back using integrity checking before Python publishes the cache.
        KeyStore.getInstance(new File(args[2]), password);
        System.out.println("TLS ready: " + added + " additional trusted certificates; " + combined.size() + " total.");
    }
}
'''

def system_certificates():
    if os.name == 'nt':
        # Trust roots only: the intermediate CA store is not a source of anchors.
        return {cert for cert, encoding, trust in ssl.enum_certificates('ROOT')
                if encoding == 'x509_asn' and (trust is True or '1.3.6.1.5.5.7.3.1' in trust)}
    return set(ssl.create_default_context().get_ca_certs(binary_form=True))

def _valid_cache(trust, marker, digest):
    try:
        data = json.loads(marker.read_text('utf-8'))
        return (data.get('input') == digest and trust.stat().st_size > 0
                and data.get('sha256') == hashlib.sha256(trust.read_bytes()).hexdigest())
    except (OSError, ValueError):
        return False

def prepare_trust(java_home, base, runner, env, certs):
    runner.check()
    if not certs:
        runner.log('TLS: using the JDK default trust store (no additional system roots).')
        return []
    defaults = java_home/'lib/security/cacerts'
    h = hashlib.sha256(b'AndroidCompiler-trust-v2\0' + defaults.read_bytes())
    for cert in sorted(certs):
        h.update(len(cert).to_bytes(4, 'big')); h.update(cert)
    digest = h.hexdigest()
    trust = base/f'os-trust-v2-{digest[:24]}.p12'
    marker = trust.with_suffix('.json')
    if _valid_cache(trust, marker, digest):
        runner.log('TLS: reusing verified certificate cache.')
    else:
        runner.stage('Preparing secure connection certificates')
        runner.log(f'TLS: preparing {len(certs)} system roots in one Java process (maximum 120 seconds).')
        base.mkdir(parents=True, exist_ok=True)
        # Old v1 .p12 files (possibly partial) are never reused. No deletion of
        # user or OS certificate stores; temporary work is confined to this folder.
        with tempfile.TemporaryDirectory(prefix='trust-build-', dir=base) as temp:
            stage = Path(temp)
            source = stage/'BuildTrust.java'
            source.write_text(TRUST_BUILDER, encoding='utf-8')
            bundle = stage/'roots.pem'
            bundle.write_text(''.join(ssl.DER_cert_to_PEM_cert(c) for c in sorted(certs)), encoding='ascii')
            pending = stage/'trust.p12'
            java = java_home/'bin'/('java.exe' if os.name == 'nt' else 'java')
            runner.run([java, '-Dfile.encoding=UTF-8', source, defaults, bundle, pending], base, env, timeout=120)
            runner.check()
            if not pending.is_file() or not pending.stat().st_size:
                raise ValueError('TLS certificate preparation produced no trust store')
            metadata = {'input': digest, 'sha256': hashlib.sha256(pending.read_bytes()).hexdigest()}
            pending.replace(trust)
            ready = stage/'ready.json'; ready.write_text(json.dumps(metadata), encoding='utf-8'); ready.replace(marker)
    return ['-Djavax.net.ssl.trustStore='+str(trust),
            '-Djavax.net.ssl.trustStorePassword=changeit',
            '-Djavax.net.ssl.trustStoreType=PKCS12']

def java_network(java_home: Path, base: Path, runner, env):
    args=[]
    for scheme,url in urllib.request.getproxies().items():
        if scheme not in ('http','https'): continue
        p=urllib.parse.urlparse(url if '://' in url else 'http://'+url)
        if p.username or p.password: raise ValueError('Authenticated proxy is not supported automatically')
        if p.hostname:
            args.extend([f'-D{scheme}.proxyHost={p.hostname}',f'-D{scheme}.proxyPort={p.port or 80}'])
    args.extend(prepare_trust(java_home, base, runner, env, system_certificates()))
    return args
