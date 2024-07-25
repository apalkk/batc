#!/usr/bin/env python3

import click
import os
import subprocess
import tempfile
import re
import datetime
import socket

partition_acc_name = re.search(r"^nexus([a-zA-Z]+)", socket.getfqdn()).group(1)


@click.group()
def batc():
    """
    A quick and dirty way to use slurm without much effort. Defaults are set to fit the CLIP Lab in UMIACS, but it should be generalizable for all lab partitions.
    
    For official UMIACS documentation: https://wiki.umiacs.umd.edu/umiacs/index.php/Main_Page
    
    For more detailed SLURM commands: https://docs.rc.fas.harvard.edu/kb/convenient-slurm-commands/
    
    For detailed fairshare calculations: https://github.com/fasrc/scalc
    """
    pass


@batc.command()
def setup():
    """
    Set up the environment by installing necessary packages and modifying .bashrc.
    
    This command installs conda and modifies the .bashrc file to add useful aliases
    and environment variables. It also ensures the setup is only performed once.
    """
    if os.getenv("BATC_SETUP") == "true":
        click.echo("Setup has already been completed")
        return

    os.system("pip install conda")

    lines_to_add = [
        f"alias scratch=\"cd /fs/nexus-scratch/{os.getenv('USER')}/\"",
        "export BATC_SETUP=true"
    ]

    bashrc_path = os.path.expanduser("~/.bashrc")

    with open(bashrc_path, 'a') as bashrc:
        bashrc.write("\n# Added by <batc>\n")
        for line in lines_to_add:
            bashrc.write(line + "\n")
        bashrc.write("# End of <batc>\n")

    os.system("source ~/.bashrc")


@batc.command()
@click.option('--job', default='default', help='The name of your job, default is "default"')
@click.option('--qos', default='default', help='Quality of Service, default is "default"')
@click.option('--ntasks', default=1, help='Number of tasks, default is 1')
@click.option('--cpu', default=1, help='Number of CPUs per task, default is 1')
@click.option('--mem', default='32', help='Memory in GB, default is 32')
@click.option('--gpu', default='rtxa4000:1', help='Type and number of GPUs, default is 1 rtx a4000 (rtxa4000:1)')
@click.option('--time', default='10:00', help='Time limit (HH:MM), default is 10:00')
@click.option('--pwd', default=os.getenv('PWD'), help=f"Working directory, default = {os.getenv('PWD')}")
@click.option('--conda_env', default=os.getenv('$CONDA_DEFAULT_ENV'), help=f'Conda environment to activate, default is {os.getenv('$CONDA_DEFAULT_ENV')}')
@click.option('--acc', default=partition_acc_name, help=f'Account name, default = {partition_acc_name}')
@click.option('--part', default=partition_acc_name, help=f'Partition name, default = {partition_acc_name}')
@click.option('--logfile', default='', help='Name of the log file generated when running the job. It contains job output. When default it is set based on the job name')
@click.option('--datafile', default='', help='Name of the data file generated during job submission. It contains job submission details. When default it is set based on the job name')
@click.option('-M', is_flag=True, help='Ignores qos, cpu, gpu, mem options and maxes out your job')
@click.argument('command')
def run(command, job, qos, ntasks, cpu, mem, gpu, time, pwd, conda_env, acc, part, datafile, logfile, m):
    """
    Submit a job to slurm with specified parameters. The default params should be accurate most of the time. Any errors will be shown in the datafile.
    The argument is the command enclosed in quotes ("python file.py -W") or script to be executed (file.py).
    In the case where the full command is not given, the file will be run by using base python. (file.py -> python file.py)

    To read more about Job QOS and partitions: https://wiki.umiacs.umd.edu/umiacs/index.php/Nexus#Partition_QoS
    To use sbatch directly: https://wiki.umiacs.umd.edu/umiacs/index.php/SLURM/JobSubmission#sbatch
    """
    if os.path.isfile(command):
        command = "python " + command
    if logfile == '':
        logfile = f"{job}.log"
    if datafile == '':
        datafile = f"{job}.data"
    if os.path.isfile(logfile):
        raise click.BadOptionUsage(
            option_name="--logfile", message="File with the same name as logfile already exists")
    if m:
        qos = 'huge-long'
        cpu = '4'
        gpu = 'rtxa4000:4'
        mem = '32'

    slurm_script = f"""#!/bin/bash
#SBATCH --job-name={job}
#SBATCH --qos={qos}
#SBATCH --partition={part}
#SBATCH --account={acc}
#SBATCH --ntasks={ntasks}
#SBATCH --cpus-per-task={cpu}
#SBATCH --mem={mem}gb
#SBATCH --gpus={gpu}
#SBATCH --time={time}
#SBATCH --output={pwd}/{logfile} # Redirect the output to a file

eval "$(conda shell.bash hook)"

# Activate conda environment
conda activate {conda_env}

# Run your Python script or other commands
{command}
"""

    stdout, stderr = "", ""
    with tempfile.NamedTemporaryFile(delete=True, mode='w') as temp_script:
        temp_script.write(slurm_script)
        temp_script.flush()  # Ensure the content is written to disk
        temp_script_path = temp_script.name
        process = subprocess.Popen(
            ['sbatch', temp_script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        stdout, stderr = process.communicate()

    if stdout is None:
        stdout = ""
    if stderr is None:
        stderr = ""

    pid_match = re.search(r"Submitted batch job (\d+)", str(stdout))

    if pid_match:
        pid = pid_match.group(1)
    else:
        pid = "Unknown PID"

    # Prepare lines to add to the log file
    lines_to_add = [
        f"PID : {pid}",
        " ",
        f"Time of job submission: {datetime.datetime.now()}",
        " ",
        "Sbatch script:",
        slurm_script,
        " ",
        "Std Out From Subprocess (If Any):",
        stdout,
        "Std Err (If Any):",
        stderr
    ]

    with open(os.path.join(os.getenv('PWD'), datafile), 'w') as log_file:
        log_file.write("\n# Details <batc> ::\n")
        for line in lines_to_add:
            log_file.write(str(line) + "\n")


if __name__ == '__main__':
    batc()
