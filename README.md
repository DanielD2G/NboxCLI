# Nbox CLI

A command-line interface for interacting with [Nbox](https://github.com/norlis/nbox).

## About Nbox

Nbox is a centralized configuration management system. This CLI tool provides an easy way to interact with Nbox servers from the command line.

**Special thanks to the [Nbox project](https://github.com/norlis/nbox) for providing the management system.**

## Installation

### Install from Git Repository

You can install Nbox CLI directly from the repository using pip:

```bash
pip install git+https://github.com/DanielD2G/NboxCLI.git
```

### Install from Local Repository

If you have cloned the repository locally:

```bash
git clone https://github.com/DanielD2G/NboxCLI.git
cd nbox-cli
pip install -e .
```

## Configuration

Before using the CLI, you need to configure your Nbox URL:

```bash
nbox config
```

You will be prompted to enter:
- **NBOX URL**: The base URL of your Nbox server (e.g., `https://nbox.example.com`)

Then, authenticate with your credentials:

```bash
nbox login
```

You will be prompted to enter:
- **Username**: Your Nbox username
- **Password**: Your password

Alternatively, you can provide credentials directly using flags:

```bash
nbox login --username your-username --password your-password
# or using short flags
nbox login -u your-username -p your-password
```

The authentication token will be stored in `~/.config/nboxcli/credentials` and used for all subsequent requests.

## Usage

### Get a Single Entry by Key

Retrieve a configuration entry by its key:

```bash
nbox get-entry /global/example/debug
```

With JSON output:

```bash
nbox get-entry /global/example/debug --output json
```

Decrypt secure value:

```bash
nbox get-entry /global/example/secret --decrypt
```

### Get Entries by Path Prefix

Retrieve all entries matching a path prefix:

```bash
nbox get-path /global/example
```

With JSON output:

```bash
nbox get-path /global/example --output json
```

Decrypt secure values:

```bash
nbox get-path /global/example --decrypt
```

### Create a New Entry

Create a new configuration entry:

```bash
nbox create-entry /global/example/new-key "my value"
```

Create a secure entry:

```bash
nbox create-entry /global/example/secret "secret value" --secure
```

### Create Multiple Entries from File

Create multiple entries from a JSON file (Nbox format *Default*):

```bash
nbox create-entries nbox.json
```

Create entries from a .env file:

```bash
nbox create-entries .env --type dotenv --nbox-path /global/example
```

Skip changeset creation (no confirmation):

```bash
nbox create-entries nbox.json --type nbox --no-changeset
```

**Nbox JSON format:**
```json
[
  {
    "key": "/global/example/debug",
    "value": "true",
    "secure": false
  },
  {
    "key": "/global/example/api-key",
    "value": "secret123",
    "secure": true
  }
]
```

**Dotenv format (.env):**
```bash
DEBUG=true
API_KEY=secret123
DATABASE_URL=postgresql://localhost/db
```

### Remove an Entry

Remove a configuration entry:

```bash
nbox remove-entry /global/example/old-key
```

Skip confirmation:

```bash
nbox remove-entry /global/example/old-key --no-confirmation
```

## Available Commands

- `nbox config` - Configure Nbox URL
- `nbox login` - Authenticate and store access token
- `nbox get-entry <key>` - Get a single entry by key (use `--decrypt` for secure values)
- `nbox get-path <prefix>` - Get all entries matching a path prefix
- `nbox create-entry <key> <value>` - Create a new entry
- `nbox create-entries <source-file>` - Create multiple entries from a file (JSON or .env)
- `nbox remove-entry <key>` - Remove an entry by key

## Options

### Global Options

- `--output, -o` - Output format: `table` (default) or `json`

### get-entry Options

- `--decrypt, -d` - Decrypt secure values

### get-path Options

- `--decrypt` - Decrypt secure values

### create-entry Options

- `--secure, -s` - Mark entry as secure

### create-entries Options

- `--type` - Input format: `nbox` (default) or `dotenv`
- `--no-changeset` - Skip changeset creation and confirmation
- `<nbox-path>` - Required when using `--type dotenv`: the base path for entries

### remove-entry Options

- `--no-confirmation` - Skip delete confirmation

### login Options

- `--username, -u` - Username
- `--password, -p` - Password

## Requirements

- Python >= 3.12
- Dependencies are automatically installed via pip

