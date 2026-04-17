# run_command Skill

Execute shell commands without asking for confirmation.

## Input

A shell command string.

## Output

JSON with:
- `stdout`: Command output
- `stderr`: Error output
- `returncode`: Exit code
- `success`: Boolean

## Usage

```bash
python run_shell.py "ls -la"
```

## Example Call

```json
{
  "command": "python run_shell.py \"echo hello\""
}
```