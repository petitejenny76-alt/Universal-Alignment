# External root of trust

The trusted host must provision the expected constitution fingerprint independently
of the object being verified. The demo loads `constitution.sha256`; a deployment
must protect that file and its distribution channel.

Never construct the expected root from `Constitution().integrity_hash` at startup.
The expected fingerprint, constitution bytes and law map are preserved from V1.1.
Package version 1.2.2-rc4 does not change the constitution's internal version.

This root verifies the canonical constitution payload only, not the gate code,
law map, signing keys, host or model. Protect those separately. The package file
manifest is unsigned and does not supply authenticity against a malicious writer.
