import subprocess
import os
import toml

def get_version_from_pyproject():
    try:
        # Load the pyproject.toml file
        pyproject_data = toml.load("pyproject.toml")
        # Extract the version from the project metadata
        return pyproject_data.get("project", {}).get("version", "unknown")
    except FileNotFoundError:
        print("pyproject.toml not found. Using default version.")
        return "unknown"
    except Exception as e:
        print(f"An error occurred while reading pyproject.toml: {e}")
        return "unknown"

def run_pytest():
    # Get version from pyproject.toml
    version = get_version_from_pyproject()

    # Set environment variables
    env = os.environ.copy()
    env["TESTOMATIO_SHARED_RUN"] = "1"
    env["TESTOMATIO_TITLE"] = f"smoke-{version}"

    # Pytest command
    pytest_command = [
        "pytest",
        "-p", "pytester",  # Load the pytester plugin
        "-m", "smoke",     # Run only tests with the "smoke" marker
        "-vv"              # Verbose output
    ]

    try:
        # Run the pytest command, streaming output to the console
        process = subprocess.Popen(
            pytest_command,
            env=env,
            stdout=None,  # Allow real-time streaming of stdout
            stderr=None,  # Allow real-time streaming of stderr
        )

        # Wait for the process to complete
        process.wait()

        # Check the exit code
        if process.returncode == 0:
            print("All tests passed successfully!")
        else:
            print(f"Some tests failed with exit code: {process.returncode}")

    except Exception as e:
        print(f"An error occurred while running pytest: {e}")

if __name__ == "__main__":
    run_pytest()
