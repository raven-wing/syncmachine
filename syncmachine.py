#!/bin/python3
import argparse
import inotify.adapters
import logging
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory, TemporaryFile

exit_requested = False

def parse_args():
    parser = argparse.ArgumentParser(description='Synchronise host machine with docker-machine.')
    parser.add_argument('-v', '--verbosity', action="count", default=0, help="increase output verbosity")
    parser.add_argument('machine', type=str, help="name of docker machine")
    parser.add_argument('directory', type=str, help="directory which should be synchronized")
    return parser.parse_args()


def set_verbosity_level(numeric_level):
    MAX_LEVEL=50
    PYTHON_LOGGER_MULTIPLIER = 10
    logging.basicConfig(level=MAX_LEVEL-numeric_level*PYTHON_LOGGER_MULTIPLIER)


def wrap_synchronize(machine, directory):
    tempdir = create_temp_dir_on_host()
    create_dir_on_machine(machine, directory)
    mount_dir(machine, directory, tempdir.name)
    sync(directory, tempdir.name)
    for filename in files_notifier(directory):
        print(f"{filename}, {tempdir.name}")
    import time
    time.sleep(5)


def files_notifier(directory):
    i = inotify.adapters.Inotify()
    i.add_watch(directory)
    global exit_requested
    signal.signal(signal.SIGINT, lambda x,y: request_exit(directory))
    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event
        if exit_requested:
            break
        if 'IN_CLOSE_WRITE' in type_names:
            yield filename


def sync(source, destination):
    subprocess.run(["rsync", "-r", "--info=progress2", f"{source}", f"{destination}"])


def main():
    args = parse_args()
    set_verbosity_level(args.verbosity)
    wrap_synchronize(args.machine, args.directory)    

    
def create_temp_dir_on_host():
    directory = TemporaryDirectory()
    return directory

def create_dir_on_machine(machine, directory):
    subprocess.run(["docker-machine", "ssh", f"{machine}", f'mkdir -p {directory}'])


def mount_dir(machine, directory, tempdir):
    subprocess.run(["docker-machine", "mount",  f"{machine}:{directory}/", f"{tempdir}"])


def request_exit(directory):
    global exit_requested
    print("exit requested")
    exit_requested = True
    TemporaryFile(dir=directory)

if __name__ == "__main__":
    main()


