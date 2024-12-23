import os
import shutil
import click
from pathlib import Path
from platformdirs import user_config_path
from .client import RunPodClient
from .config import save_api_key, get_api_key

DEFAULT_SSH_KEY_NAME = "runpod"
DEFAULT_CONFIG_NAME = "config_runpod"
DEFAULT_SSH_USER = "root"


def get_ssh_dir() -> Path:
    return user_config_path("SSH") if os.name == "nt" else Path.home() / ".ssh"


def generate_ssh_config(
    pods: dict[str, tuple[str | None, int | None]],
    pod_filter: str | None = None,
    ssh_key_path: Path | None = None,
    ssh_user: str = DEFAULT_SSH_USER,
    enable_x11: bool = True,
) -> tuple[list[str], int]:
    config_template = """Host %s
  HostName %s
  Port %s
  User {ssh_user}
  IdentitiesOnly yes
  IdentityFile {ssh_key_path}
{x11_forward}"""

    configs: list[str] = []
    pods_added = 0
    ssh_key_path = ssh_key_path or get_ssh_dir() / DEFAULT_SSH_KEY_NAME
    x11_forward = "  ForwardX11 yes" if enable_x11 else ""

    for idx, (pod_name, (ip, port)) in enumerate(pods.items()):
        if pod_filter and not pod_name.startswith(pod_filter):
            click.echo(f"Skipping pod {pod_name}")
            continue

        formatted_pod_name = pod_name.replace(" ", "-") + f"--idx{idx}"

        if ip is not None and port is not None:
            click.echo(f"pod-{formatted_pod_name:<40} {ip}:{port}")
            configs.append(
                config_template.format(
                    ssh_key_path=ssh_key_path,
                    ssh_user=ssh_user,
                    x11_forward=x11_forward,
                )
                % (f"pod-{formatted_pod_name}", ip, port)
            )
            pods_added += 1

    return configs, pods_added


def check_ssh_key(ssh_key_path: Path) -> bool:
    if not ssh_key_path.exists():
        return False

    if os.name != "nt":
        mode = ssh_key_path.stat().st_mode
        if mode & 0o077:
            click.echo("Warning: SSH key has too open permissions. Fixing...")
            ssh_key_path.chmod(0o600)

    return True


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--config-dir", type=click.Path())
@click.option("--pod-filter", type=str)
@click.option("--config-name", type=str, default=DEFAULT_CONFIG_NAME)
@click.option("--ssh-key", type=click.Path())
@click.option("--ssh-user", type=str, default=DEFAULT_SSH_USER)
@click.option("--x11/--no-x11", default=True)
@click.option("--api-key")
def sync(
    config_dir: str | None,
    pod_filter: str | None,
    config_name: str,
    ssh_key: str | None,
    ssh_user: str,
    x11: bool,
    api_key: str | None,
) -> None:
    config_dir_path = (
        Path(os.path.expanduser(config_dir)) if config_dir else get_ssh_dir()
    )
    config_dir_path.mkdir(parents=True, exist_ok=True)

    ssh_key_path = Path(os.path.expanduser(ssh_key)) if ssh_key else None
    client = RunPodClient(api_key)
    pods = dict(client.get_all_running_pods())
    configs, pods_added = generate_ssh_config(
        pods,
        pod_filter=pod_filter,
        ssh_key_path=ssh_key_path,
        ssh_user=ssh_user,
        enable_x11=x11,
    )

    config_path = config_dir_path / config_name
    config_path.write_text("\n".join(configs))

    click.echo("\n✨ Summary:")
    click.echo(f"• Total pods found: {len(pods)}")
    click.echo(f"• Pods added to config: {pods_added}")
    click.echo(f"• Config written to: {config_path}")
    click.echo(
        f"• SSH key path: {ssh_key_path or (get_ssh_dir() / DEFAULT_SSH_KEY_NAME)}"
    )
    click.echo(f"• SSH user: {ssh_user}")
    click.echo(f"• X11 forwarding: {'enabled' if x11 else 'disabled'}")

    ssh_config = config_dir_path / "config"
    include_line = f"Include {config_name}"

    if ssh_config.exists():
        content = ssh_config.read_text()
        if include_line not in content:
            click.echo("\n🚨  Action needed:")
            click.echo(f"Add the following line to {ssh_config}:")
            click.echo(f"  {include_line}")
    else:
        click.echo(f"\n🚨  Note: No SSH config file found at {ssh_config}")
        click.echo("Create one with the following content:")
        click.echo(f"  {include_line}")


@cli.command()
@click.option("--api-key", prompt=True, hide_input=True)
def configure(api_key: str) -> None:
    save_api_key(api_key)
    click.echo("API key saved successfully!")


@cli.command()
def setup() -> None:
    click.echo("Welcome to RunPod SSH setup! 🚀\n")

    if not get_api_key():
        click.echo("First, let's configure your RunPod API key.")
        click.echo("You can find it at: https://runpod.io/console/user/settings")
        api_key = click.prompt("Please enter your API key", hide_input=True)
        save_api_key(api_key)
        click.echo("✅ API key saved successfully!\n")

    ssh_dir = get_ssh_dir()
    ssh_key_path = ssh_dir / DEFAULT_SSH_KEY_NAME

    if not check_ssh_key(ssh_key_path):
        click.echo("\nNo SSH key found at: " + str(ssh_key_path))
        if click.confirm("Would you like to generate a new SSH key?"):
            ssh_dir.mkdir(parents=True, exist_ok=True)
            os.system(f'ssh-keygen -t ed25519 -f "{ssh_key_path}" -N ""')
            click.echo("\n✅ SSH key generated!")

            pub_key = ssh_key_path.with_suffix(".pub").read_text().strip()
            click.echo("\nPlease add this public key to RunPod:")
            click.echo("1. Go to: https://runpod.io/console/user/settings")
            click.echo("2. Add this key under 'SSH Keys':\n")
            click.echo(pub_key)
            click.echo("\nPress Enter once you've added the key...")
            input()
        else:
            existing_key = click.prompt(
                "Please enter the path to your existing SSH key",
                type=click.Path(exists=True, path_type=Path),
            )
            if existing_key != ssh_key_path:
                if os.name == "nt":
                    shutil.copy2(existing_key, ssh_key_path)
                else:
                    ssh_key_path.symlink_to(existing_key)
                click.echo(f"\n✅ SSH key linked: {existing_key} -> {ssh_key_path}")

    ssh_config = ssh_dir / "config"
    include_line = f"Include {DEFAULT_CONFIG_NAME}"

    if ssh_config.exists():
        content = ssh_config.read_text()
        if include_line not in content:
            if click.confirm(
                f"\nWould you like to add '{include_line}' to your SSH config?"
            ):
                with ssh_config.open("a") as f:
                    f.write(f"\n{include_line}\n")
                click.echo("✅ SSH config updated!")
    else:
        if click.confirm(
            f"\nWould you like to create an SSH config file with '{include_line}'?"
        ):
            ssh_config.write_text(f"{include_line}\n")
            click.echo("✅ SSH config created!")

    click.echo("\n🎉 Setup complete! Try running: runpod-ssh sync")


def main() -> None:
    cli()
