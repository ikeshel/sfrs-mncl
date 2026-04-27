#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

import subprocess
from loguru import logger

# /mbs/driv/mbspexV3_5.10-64_DEB/bin/gosipcmd -r -x 0 0 0x200004
GOC_COMMAND = "/mbs/driv/mbspexV3_5.10-64_DEB/bin/gosipcmd"

#==============================================================================
class SSHCommander:

    #==========================================================================
    def __init__(self, hostname: str, username: str = 'ikeshel'):
        """Initialize SSH commander with host and user details."""
        self.hostname = hostname
        self.username = username
        # logger.debug(f"SSHCommander initialized for {username}@{hostname}")

    #==========================================================================
    def goc_read(self, sfp: int=0, dev: int=0, address: hex=0x0) -> tuple[int, str, str]:
        """Run a GOC command on the remote host."""
        ssh_command = [
            GOC_COMMAND,
            "-r",
            "-x",
            f"{sfp}",
            f"{dev}",
            f"{hex(address)}"
        ]
        logger.info(f"goc read: {ssh_command}")
        return self.run_command(ssh_command)

    #==========================================================================
    def goc_write(self, sfp: int=0, dev: int=0, address: hex=0x0, value: int=0) -> tuple[int, str, str]:
        """Run a GOC write command on the remote host."""
        ssh_command = [
            GOC_COMMAND,
            "-w",
            "-x",
            f"{sfp}",
            f"{dev}",
            f"{hex(address)}",
            f"{hex(value)}"
        ]
        logger.info(f"goc write: {ssh_command}")
        return self.run_command(ssh_command)

    #==========================================================================
    def run_command(self, command: list) -> tuple[int, str, str]:
        """
        Run a command on remote host via SSH.
        
        Returns:
            tuple: (return_code, stdout, stderr)
        """
        ssh_command = [
            "ssh",
            "-o", "ConnectTimeout=1",
            f"{self.username}@{self.hostname}",
        ]
        ssh_command.extend(command)

        logger.debug(f"Running command: {ssh_command}")
        
        try:
            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                timeout=3
            )
            
            logger.success(f"Command executed with return code {result.returncode}")
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
        return self.run_command([script_content])

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
        screen_command = [
            "screen", 
            "-S", 
            f"{screen_name}", 
            "-X", 
            "stuff", 
            f"'{command} \\n'"]
        logger.info(f"Running screen command: {screen_command}")
        return self.run_command(screen_command)

    #==========================================================================
    def run_screen_list(self, screen_name: str, command_list: list) -> tuple[int, str, str]:
        """
        Run a command in a named screen session.
        
        Args:
            screen_name: Name of the screen session
            command_list: List of commands to execute in the screen session
        
        Returns:
            tuple: (return_code, stdout, stderr)
        """
        screen_command = [
            f"screen", 
            f"-S", 
            f"{screen_name}", 
            f"-X", 
            f"stuff",
            f"'"]
        screen_command.extend(command_list)
        screen_command.append("\\n")
        screen_command.append("'")
        logger.debug(f"Screen command list: {screen_command}")
        logger.debug(f"Running screen command: {screen_command}")
        return self.run_command(screen_command)

#==============================================================================
# Test the SSHCommander class
#==============================================================================
def main():
    """Test the SSHCommander with a sample command."""
    commander = SSHCommander(hostname='x86l-170')
    screen_name = "mbs"
    list_of_commands = [
        '\x1A', # Ctrl+Z to suspend the screen session
        'cd ~/MUSIC', 
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

if __name__ == "__main__":

    # main()

    commander = SSHCommander(hostname='x86l-132')
    return_code, stdout, stderr = commander.goc_read(sfp=0, dev=0, address=0x200004)

    logger.info(f"GOC Read Return code: {return_code}")
    logger.info(f"GOC Read Output: {stdout}")
    if stderr:
        logger.error(f"GOC Read Error: {stderr}")
    