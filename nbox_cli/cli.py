import json
import pathlib
from typing import Literal, Optional

import inquirer
import typer
from pydantic import ValidationError
from rich import print_json
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table

from nbox_cli.client import NboxRequestClient
from nbox_cli.config import NboxConfig

app = typer.Typer()
console = Console()


def _get_client() -> NboxRequestClient:
    try:
        nbox_client = NboxRequestClient()
        nbox_client.validate_token()
        return nbox_client
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg and "expired" in error_msg.lower():
            typer.secho("\n❌ Your authentication token has expired. Please run 'nbox login' again.",
                        fg=typer.colors.RED)
            raise typer.Exit(code=1)

        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command(name="config")
def configure():
    typer.echo("Setting config")

    nbox_url = typer.prompt("NBOX URL")

    try:
        config = NboxConfig(nbox_url=nbox_url)
    except ValidationError as e:
        typer.secho("❌ Invalid config parameters", fg=typer.colors.RED)
        typer.echo(e)
        raise typer.Exit(code=1)

    config.save()

    typer.secho(f"✅ Config successfully saved", fg=typer.colors.GREEN)


@app.command(name="login")
def login(
        username: str = typer.Option(None, "--username", "-u", help="Username"),
        password: str = typer.Option(None, "--password", "-p", help="Password")
):
    typer.echo("Login to Nbox")

    if not username:
        username = typer.prompt("Username")
    if not password:
        password = typer.prompt("Password", hide_input=True)

    try:
        token = NboxRequestClient.login(username, password)
        typer.secho(f"✅ Login successful! Token saved.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"❌ Login failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _get_secret(nbox_request_client, key, output_type):
    result = nbox_request_client.get_secret_by_key(key)
    if not result:
        typer.secho(f"❌ Error: No secret found with key: {key}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if output_type == "table":
        typer.secho("✅ Parsed secret", fg=typer.colors.GREEN)
        table = Table()
        table.add_column("KEY")
        table.add_column("VALUE")
        table.add_row(
            key,
            str(result.get("value", "")))
        console.print(table)
    elif output_type == "json":
        print_json(json.dumps(result))


def _get_key(nbox_request_client, key, output_type):
    entry = nbox_request_client.get_entry_by_key(key)
    if not entry:
        typer.secho(f"❌ Error: No entry found with key: {key}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if output_type == "table":
        typer.secho("✅ Parsed entry", fg=typer.colors.GREEN)
        table = Table()
        table.add_column("KEY")
        table.add_column("VALUE")
        table.add_column("SECURE")
        table.add_row(
            entry.get("key", ""),
            str(entry.get("value", "")),
            str(entry.get("secure", "")),
        )
        console.print(table)
    elif output_type == "json":
        print_json(json.dumps(entry))


@app.command()
def get_entry(key: str,
              decrypt: bool = typer.Option(
                  False,
                  "--decrypt", "-d",
                  help="Decrypt a secure value"
              ),
              output_type: Literal["table", "json"] = typer.Option(
                  "table",
                  "--output", "-o",
                  help="Output format: 'table' or 'json'"
              )) -> str:
    if output_type not in ["table", "json"]:
        typer.secho(f"❌ Error: Format unavailable, only table or json supported", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    nbox_request_client = _get_client().entry
    try:
        if decrypt:
            _get_secret(nbox_request_client, key, output_type)
        else:
            _get_key(nbox_request_client, key, output_type)
    except Exception as e:
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def get_path(prefix: str,
             decrypt: bool = typer.Option(
                 False,
                 "--decrypt",
                 help="Decrypt secure values"
             ),
             output_type: Literal["table", "json"] = typer.Option(
                 "table",
                 "--output", "-o",
                 help="Output format: 'table' or 'json'"
             )) -> str:
    if output_type not in ["table", "json"]:
        typer.secho(f"❌ Error: Format unavailable, only table or json supported", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    nbox_request_client = _get_client().entry
    try:
        entries = nbox_request_client.get_entries_by_prefix(prefix, decrypt=decrypt)
    except Exception as e:
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not entries:
        typer.secho(f"❌ Error: No entries found with prefix: {prefix}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if output_type == "table":
        typer.secho(f"✅ Found {len(entries)} entries", fg=typer.colors.GREEN)
        table = Table(show_lines=True)
        table.add_column("KEY")
        table.add_column("VALUE")
        table.add_column("SECURE")

        for entry in entries:
            table.add_row(
                entry.get("key", ""),
                str(entry.get("value", "")),
                str(entry.get("secure", "")),
            )
        console.print(table)
    elif output_type == "json":
        print_json(json.dumps(entries))


@app.command()
def create_entry(key: str,
                 value: str,
                 secure: bool = typer.Option(
                     False,
                     "--secure", "-s",
                     help="Mark entry as secure"
                 )):
    nbox_request_client = _get_client().entry
    try:
        entry = nbox_request_client.get_entry_by_key(key)
    except Exception:
        entry = None

    table = Table()
    table.add_column("KEY")
    if entry:
        table.add_column("OLD VALUE")
        table.add_column("NEW VALUE")
    else:
        table.add_column("VALUE")
    table.add_column("SECURE")

    if entry:
        typer.echo("You are about to update the following entry:")
        table.add_row(
            entry.get("key", ""),
            str(entry.get("value", "")),
            value,
            str(secure),
        )
    else:
        typer.echo("You are about to create the following entry:")
        table.add_row(key, value, str(secure))

    console.print(table)

    confirm = typer.confirm("Do you want to proceed?")
    if not confirm:
        typer.secho("❌ Operation cancelled", fg=typer.colors.YELLOW)
        raise typer.Exit(code=0)

    try:
        nbox_request_client = NboxRequestClient().entry
        result = nbox_request_client.create_entry(key, value, secure)

    except Exception as e:
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(f"✅ Entry created successfully: {key}", fg=typer.colors.GREEN)


def _parse_env_file(content, nbox_path):
    lines = content.strip().split('\n')
    entries = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if '=' not in line:
            continue

        key, value = line.split('=', 1)
        key = key.strip().lower().replace("_", "-")
        value = value.strip()

        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]

        entries.append({
            'env_key': key,
            'value': value
        })

    if not entries:
        return []

    questions = [
        inquirer.Checkbox(
            'secure_keys',
            message="Select which entries should be marked as secure (use space to select, enter to confirm)",
            choices=[entry['env_key'] for entry in entries],
        ),
    ]

    answers = inquirer.prompt(questions)
    secure_keys = set(answers['secure_keys']) if answers else set()

    data = []
    for entry in entries:
        full_key = f"{nbox_path.rstrip('/')}/{entry['env_key']}"
        is_secure = entry['env_key'] in secure_keys

        data.append({
            'key': full_key,
            'value': entry['value'],
            'secure': is_secure
        })

    return data


def _parse_nbox_json(content):
    entries_json = json.loads(content)
    if not isinstance(entries_json, list):
        typer.secho("❌ Unsupported JSON format", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    data = []
    for entry in entries_json:
        if not isinstance(entry, dict):
            typer.secho("❌ Unsupported JSON format", fg=typer.colors.YELLOW)
            raise typer.Exit(code=1)

        if "key" not in entry or "value" not in entry:
            typer.secho("❌ Each entry must contain 'key' and 'value' fields", fg=typer.colors.YELLOW)
            raise typer.Exit(code=1)

        key = entry["key"].lstrip("/") if isinstance(entry["key"], str) else entry["key"]
        value = entry["value"]
        secure = entry.get("secure", False)

        data.append({
            "key": key.lower(),
            "value": value,
            "secure": secure
        })

    return data


@app.command()
def create_entries(source_file: str,
                   nbox_path: Optional[str] = None,
                   input_type: Literal["nbox", "dotenv"] = typer.Option(
                       "nbox", "--type",
                       help="Input format: 'nbox' for nbox style json | 'json' for a json with format {key:value} | 'dotenv' for an environment .env file with 'key=value'"
                   ),
                   no_changeset: bool = typer.Option(
                       False,
                       "--no--changeset",
                       help="Avoid creating the changeset"
                   )):
    table = Table(show_lines=True)
    table.add_column("KEY")
    if not no_changeset:
        table.add_column("OLD VALUE")
        table.add_column("NEW VALUE")
    else:
        table.add_column("VALUE")
    table.add_column("SECURE")

    nbox_request_client = _get_client().entry

    file = pathlib.Path(source_file)
    if not file.exists():
        typer.secho(f"❌ Error: File {file.absolute().__str__()} does not exist", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    content = file.open("r").read()

    if input_type == "nbox":
        data = _parse_nbox_json(content)
    elif input_type == "dotenv":
        if not nbox_path:
            typer.secho(
                f"❌ Error: No nbox path provided, you must provide an nbox path in order to use an environment file",
                fg=typer.colors.RED)
            raise typer.Exit(code=1)
        data = _parse_env_file(content, nbox_path)
    else:
        typer.secho(f"❌ No valid input option provided, use --help to view available options", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not no_changeset:
        spinner = Spinner("dots", text="Creating Changeset...")
        with Live(spinner, console=console):
            for entry in data:
                key = entry["key"].lower()
                path_parts = key.split('/')
                key_name = path_parts[-1].replace("-", '_')

                path_parts[-1] = key_name
                existing_key_name = ("/".join(path_parts))

                old_entry = nbox_request_client.get_entry_by_key(existing_key_name) or {}

                table.add_row(
                    key,
                    old_entry.get("value", ""),
                    str(entry.get("value", "")),
                    str(entry.get("secure", "")),
                )
    else:
        for entry in data:
            key = entry["key"].lower()
            table.add_row(
                key,
                str(entry.get("value", "")),
                str(entry.get("secure", "")),
            )

    console.print(table)

    confirm = typer.confirm("Do you want to proceed?")
    if not confirm:
        typer.secho("❌ Operation cancelled", fg=typer.colors.YELLOW)
        raise typer.Exit(code=0)

    try:
        typer.secho(f"✅ Entries created successfully: {len(data)}", fg=typer.colors.GREEN)
        result = nbox_request_client.create_entries(data)
    except Exception as e:
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def remove_entry(key: str,
                 delete_confirmation: bool = typer.Option(
                     True,
                     "--no-confirmation",
                     help="Disables the secure delete from the CLI, this allows you to delete the key without any confirmation (CAREFUL!)"
                 )) -> str:
    try:
        nbox_request_client = NboxRequestClient().entry
    except Exception as e:
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    try:
        entry = nbox_request_client.get_entry_by_key(key)
    except Exception as e:
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not entry:
        typer.secho(f"❌ Error: No entry with this key found", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if delete_confirmation:
        typer.echo("You are about to remove the following entry:")
        table = Table()
        table.add_column("KEY")
        table.add_column("VALUE")
        table.add_column("SECURE")
        table.add_row(
            entry.get("key", ""),
            str(entry.get("value", "")),
            str(entry.get("secure", "")),
        )
        console.print(table)

        confirm = typer.confirm("Do you want to proceed?")
        if not confirm:
            typer.secho("❌ Operation cancelled", fg=typer.colors.YELLOW)
            raise typer.Exit(code=0)

        try:
            result = nbox_request_client.delete_entry_by_key(key)
        except Exception as e:
            typer.secho(f"❌ Error: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

        typer.secho(f"✅ Entry removed successfully: {key}", fg=typer.colors.GREEN)
    else:
        try:
            result = nbox_request_client.delete_entry_by_key(key)
        except Exception as e:
            typer.secho(f"❌ Error: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

        typer.secho(f"✅ Entry removed successfully: {key}", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
