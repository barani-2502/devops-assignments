import os
import subprocess
import sys

source, destination = sys.argv[1], sys.argv[2]

# The S3 settings come from the environment. Nothing is written to a file or the command line.
env = os.environ.copy()

result = subprocess.run(
    ["rclone", "--config", "/dev/null", "copy", source, destination, "--retries", "3"],
    env=env,
    capture_output=True,
    text=True,
)

print("exit code:", result.returncode)
print(result.stderr[-300:])
sys.exit(result.returncode)
