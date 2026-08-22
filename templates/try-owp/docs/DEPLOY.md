# Deploy this Try OWP instance

This directory is generated from the non-normative Try OWP deployment template.
The safest default public shape keeps the Python application on loopback and
puts a trusted HTTPS ingress in front of it:

```text
Internet
   |
 HTTPS
   v
trusted reverse proxy OR Cloudflare Tunnel
   |
127.0.0.1:8080
   v
Try OWP service (unprivileged system user)
   |
/var/lib/owp-field-lab/owp-field-lab.sqlite3
```

Configured public hostname: **__OWP_PUBLIC_HOSTNAME__**

## 1. Install the application

```bash
sudo useradd --system --home /var/lib/owp-field-lab --shell /usr/sbin/nologin owp-field-lab || true
sudo install -d -o owp-field-lab -g owp-field-lab -m 0700 /var/lib/owp-field-lab
sudo install -d -o owp-field-lab -g owp-field-lab -m 0700 /var/backups/owp-field-lab
sudo install -d -o root -g root -m 0755 /opt/owp-field-lab
sudo cp -a . /opt/owp-field-lab/
sudo chown -R root:root /opt/owp-field-lab
sudo chmod -R a-w /opt/owp-field-lab
/usr/bin/python3 --version
```

The application has no third-party Python runtime dependencies.

## 2. Secrets and environment

```bash
sudo install -m 0600 deploy/owp-field-lab.env.example /etc/owp-field-lab.env
sudoedit /etc/owp-field-lab.env
```

Set `GITHUB_TOKEN` only on the private host if you want authenticated GitHub API
rate limits. Never commit the populated environment file.

Keep `OWP_FIELD_LAB_HOST=127.0.0.1`. Do not bind the application directly to a
public interface merely to make the proxy work.

## 3. systemd

```bash
sudo cp deploy/owp-field-lab.service.example /etc/systemd/system/owp-field-lab.service
sudo systemctl daemon-reload
sudo systemctl enable --now owp-field-lab
curl -fsS http://127.0.0.1:8080/healthz
```

## 4A. Public ingress with Caddy

Use `deploy/Caddyfile.example` as the site definition after pointing DNS for
`__OWP_PUBLIC_HOSTNAME__` at this host. Caddy terminates HTTPS and proxies only
to the loopback application.

## 4B. Public ingress with Cloudflare Tunnel

Cloudflare recommends remotely-managed tunnels for most current deployments.
Create a tunnel and published application in the Cloudflare dashboard, map
`__OWP_PUBLIC_HOSTNAME__` to `http://127.0.0.1:8080`, then install `cloudflared`
on the host using the token supplied by Cloudflare. Treat that token as a
secret; do not place it in this repository or in logs you intend to share.

For a locally-managed/testing tunnel, `deploy/cloudflared-config.yml.example`
shows the current configuration shape. It includes a required catch-all 404
rule. Validate it before use:

```bash
cloudflared tunnel ingress validate
cloudflared tunnel ingress rule https://__OWP_PUBLIC_HOSTNAME__/
```

Current Cloudflare references:

- https://developers.cloudflare.com/tunnel/setup/
- https://developers.cloudflare.com/tunnel/advanced/local-management/configuration-file/
- https://developers.cloudflare.com/tunnel/advanced/local-management/as-a-service/linux/

## 5. Public smoke

After DNS/TLS is active:

1. open `https://__OWP_PUBLIC_HOSTNAME__/`;
2. check `https://__OWP_PUBLIC_HOSTNAME__/healthz`;
3. submit a disposable idea work item;
4. verify the private operator CLI sees it;
5. verify an incorrect customer token returns the same not-found shape as an
   unknown reference; and
6. confirm port 8080 is not directly reachable from the public internet.

## 6. Backup verification

```bash
sudo -u owp-field-lab env OWP_FIELD_LAB_DB=/var/lib/owp-field-lab/owp-field-lab.sqlite3 \
  /usr/bin/python3 -m owp_field_lab.admin verify-all

sudo -u owp-field-lab env OWP_FIELD_LAB_DB=/var/lib/owp-field-lab/owp-field-lab.sqlite3 \
  /usr/bin/python3 -m owp_field_lab.admin backup \
  --out /var/backups/owp-field-lab/field-lab-$(date +%F-%H%M%S).sqlite3
```

Restore a copy into a disposable path and run `verify-all` against it. A backup should be restored in a test environment before it is relied on for recovery.

## Security boundary

The public intake process intentionally does **not** clone/build/execute submitted
repositories. If this deployment later selects the RC3 Software Work Integrity
profile, exact-base/result builds belong in a disposable validator-controlled
environment separate from this intake process and separate from the provider's
workspace.
