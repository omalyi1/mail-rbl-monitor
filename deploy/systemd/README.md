# systemd Deployment

## Files

This directory contains example unit files for running `mail-rbl-monitor` as a one-shot service under `systemd`:

- `mail-rbl-monitor.service`
- `mail-rbl-monitor.timer`

## Install the unit files

Copy the files into `/etc/systemd/system/` on the target host:

```bash
sudo cp deploy/systemd/mail-rbl-monitor.service /etc/systemd/system/
sudo cp deploy/systemd/mail-rbl-monitor.timer /etc/systemd/system/
```

## Edit the placeholders

Update these placeholders in `mail-rbl-monitor.service`:

- `User=<MAIL_RBL_MONITOR_USER>`
- `Group=<MAIL_RBL_MONITOR_GROUP>`
- `WorkingDirectory=<MAIL_RBL_MONITOR_WORKDIR>`
- `EnvironmentFile=<MAIL_RBL_MONITOR_ENV_FILE>`

Recommended shape:

- use a dedicated service account
- point `WorkingDirectory=` at the checked-out repository path
- point `EnvironmentFile=` at a root-owned env file outside the repo, such as `/etc/mail-rbl-monitor/mail-rbl-monitor.env`

## Reload and enable

Reload `systemd` after editing the unit files:

```bash
sudo systemctl daemon-reload
```

Enable and start the timer:

```bash
sudo systemctl enable --now mail-rbl-monitor.timer
```

## Manual service run

Run the service once immediately:

```bash
sudo systemctl start mail-rbl-monitor.service
```

Check the service status:

```bash
sudo systemctl status mail-rbl-monitor.service
```

Check the timer status:

```bash
sudo systemctl status mail-rbl-monitor.timer
```

## Logs

Inspect recent service logs:

```bash
sudo journalctl -u mail-rbl-monitor.service -n 50
```

Follow logs live:

```bash
sudo journalctl -u mail-rbl-monitor.service -f
```

## Notes

- append `--json` to `ExecStart=` only if another wrapper is consuming machine-readable stdout
- keep the service `Type=oneshot`
- use the same `uv run mail-rbl-monitor` entrypoint documented elsewhere in the repo
