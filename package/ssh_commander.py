#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"


import subprocess
from loguru import logger

#==============================================================================
class SSHCommander:

    #==========================================================================
    def __init__(self, hostname: str, username: str = 'ikeshel', port: int = 22):
        """Initialize SSH commander with host and user details."""
        self.hostname = hostname
        self.username = username
        self.port = port
        logger.info(f"SSHCommander initialized for {username}@{hostname}:{port}")

    #==========================================================================
    def run_command(self, command: str) -> tuple[int, str, str]:
        """
        Run a command on remote host via SSH.
        
        Returns:
            tuple: (return_code, stdout, stderr)
        """
        ssh_command = [
            "ssh",
            "-p", str(self.port),
            f"{self.username}@{self.hostname}",
            command
        ]
        
        logger.debug(f"Running command: {command} on {self.username}@{self.hostname}")
        
        try:
            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            logger.info(f"Command executed with return code {result.returncode}")
            if result.returncode != 0:
                logger.warning(f"Error output: {result.stderr}")
            
            return result.returncode, result.stdout, result.stderr
        
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out on {self.hostname}")
            raise
        except Exception as e:
            logger.error(f"SSH command failed: {e}")
            raise

    #==========================================================================
    def run_script(self, script_path: str) -> tuple[int, str, str]:
        """Run a local script on remote host."""
        logger.info(f"Running script {script_path} on {self.hostname}")
        with open(script_path, 'r') as f:
            script_content = f.read()
        return self.run_command(script_content)

    #==========================================================================
    def run_screen_command(self, screen_name: str, command: str) -> tuple[int, str, str]:
        """
        Run a command in a named screen session.
        
        Args:
            screen_name: Name of the screen session
            command: Command to execute in the screen session
        
        Returns:
            tuple: (return_code, stdout, stderr)
        """
        screen_command = f"screen -S {screen_name} -X stuff '{command}\\n'"
        logger.info(f"Running command in screen session '{screen_name}': {command}")
        return self.run_command(screen_command)

#==============================================================================
# Test the SSHCommander class
#==============================================================================
def main():
    """Test the SSHCommander with a sample command."""
    commander = SSHCommander(hostname='x86l-132')
    screen_name = "mbs"
    list_of_commands = [
        '\x1A', # Ctrl+Z to suspend the screen session
        'cd ~/ToF', 
        'quit', 
        'resl', 
        'mbs -dabc', 
        'help'
        ]
    for cmd in list_of_commands:
        try:
            return_code, stdout, stderr = commander.run_screen_command(screen_name, cmd)
            logger.info(f"Command: {cmd}")
            logger.info(f"Return code: {return_code}")
            logger.info(f"Output: {stdout}")
            if stderr:
                logger.error(f"{stderr}")
        except Exception as e:
            logger.error(f"Test failed for command '{cmd}': {e}")

    # try:
    #     # return_code, stdout, stderr = commander.run_command("screen -S com -X stuff 'echo okay\n'")
    #     # return_code, stdout, stderr = commander.run_command("whoami")
    #     return_code, stdout, stderr = commander.run_screen_command("com", "echo okay")
    #     print(f"Return code: {return_code}")
    #     print(f"Output: {stdout}")
    #     if stderr:
    #         print(f"Error: {stderr}")
    # except Exception as e:
    #     logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    main()