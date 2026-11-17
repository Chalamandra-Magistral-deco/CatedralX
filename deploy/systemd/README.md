# systemd deployment templates

The files ending in `.example` are templates, not installable units. They contain no host-specific user or filesystem paths.

Before installation, create a dedicated service account and state/config directories, then render the placeholders in `chalamandra-catedralx-dispatch.service.example`:

- `@SERVICE_USER@`: dedicated unprivileged Linux account that runs the dispatcher.
- `@CATEDRALX_ROOT@`: absolute path to the checked-out CatedralX repository.
- `@CONFIG_FILE@`: absolute path to the protected environment file for the dispatcher.
- `@STATE_DIR@`: absolute writable state directory for CatedralX.

Review the rendered unit and confirm that the account can read the checkout/configuration and write only to the state directory. Keep the Agents API bound to the intended local endpoint or explicitly configure the endpoint in the environment. Install the rendered service as `chalamandra-catedralx-dispatch.service`; install the timer template as `chalamandra-catedralx-dispatch.timer` only after that service exists.

Do not install these examples verbatim, and do not assume any former VM, username, home directory, or deployment provider still exists.
