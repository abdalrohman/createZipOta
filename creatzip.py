import argparse
import datetime
import logging
import os
import shutil
import subprocess
import sys

__version__ = '1.0.0'

# logging
log_level = logging.INFO
logging.basicConfig(
    format='%(asctime)s - %(filename)s:%(lineno)d\n\t\t%(levelname)-8s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=log_level
)

# store old path
old_path = os.getcwd()

# set time_now for zip_name and elapsed_time()
time_now = datetime.datetime.now()


def elapsed_time():
    time_end = datetime.datetime.now()
    elapsed = str(time_end - time_now)
    if elapsed is not None:
        print(f'\nElapsed time: {elapsed}')


def run_command(arg, verbose=None, **kwargs):
    """Runs the given command and returns the output.
    Args:
      arg: The command represented as a list of strings.
      verbose: Whether the commands should be shown. Default to the global
          verbosity if unspecified.
      kwargs: Any additional args to be passed to subprocess.run(), such as env,
          stdin, etc.
    Raises:
      RuntimeError: On non-zero exit from the command.
    """
    cmd = " ".join(arg)
    if verbose is True:
        logging.info("Running: \"%s\"", cmd)

    if 'universal_newlines' not in kwargs:
        kwargs['universal_newlines'] = True

    if 'shell' not in kwargs:
        kwargs['shell'] = True

    if 'bufsize' not in kwargs:
        kwargs['bufsize'] = -1

    proc = subprocess.run(arg, **kwargs)

    if proc.returncode != 0:
        raise RuntimeError(
            f"Failed to run command '{cmd}' (exit code {proc.returncode}):\n{proc.stderr}"
        )

    return proc.stdout, proc.stderr, proc.returncode


def create_zip(zn, path):
    # name zip archive with date and time
    zip_name = zn + '_' + time_now.strftime("%Y%m%d-%H%M") + '.zip'
    output = os.path.join(old_path, 'out')
    temp = os.path.join(output, 'temp')
    if not os.path.exists(temp):
        logging.info(f'Creat {temp}')
        os.makedirs(temp)

    try:
        # check platform and set soong_zip binary
        if sys.platform == 'linux':
            soong_zip = os.path.realpath('tools/bin/soong_zip')
            zip2zip = os.path.realpath('tools/bin/zip2zip')
        elif sys.platform == 'win32':
            soong_zip = os.path.realpath('tools/bin/soong_zip.exe')
            zip2zip = os.path.realpath('tools/bin/zip2zip.exe')
        else:
            logging.error(f'Not supported platform {sys.platform}')
            sys.exit(1)

        # before creat ota zip check META-INF folder
        if os.path.isdir(os.path.join(path, 'META-INF')):
            # change to zip dir
            logging.info(f'Changing directory to [{os.path.realpath(path)}]')
            os.chdir(path)

            # start creat zip ota
            soong_zip_cmd = [
                soong_zip, '-o',
                os.path.join(temp, zip_name), '-D', './'
            ]
            zip2zip_cmd = [
                zip2zip, '-i', os.path.join(temp, zip_name),
                '-o', os.path.join(output, zip_name)
            ]

            if sys.platform == 'linux':
                # when set shell=True on linux (error: output file path must be nonempty)
                run_command(soong_zip_cmd, verbose=True, shell=False)
                run_command(zip2zip_cmd, verbose=True, shell=False)
            elif sys.platform == 'win32':
                run_command(soong_zip_cmd, verbose=True)
                run_command(zip2zip_cmd, verbose=True)
        else:
            logging.error('Missing META-INF folder check and try again.')
            sys.exit(1)
    except KeyboardInterrupt:
        # remove not complete created zip when press ctrl+c
        if os.path.exists(os.path.join(output, zip_name)):
            logging.info(f'Removing [{os.path.join(output, zip_name)}]')
            os.remove(os.path.join(output, zip_name))
    finally:
        # remove temp dir when finish
        logging.info(f'Removing [{temp}]')
        shutil.rmtree(temp)


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] [ZIP_NAME]...",
        description="Tool for creat OTA rom zip.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-v", "--version", action="version",
        version=f"{parser.prog}: {__version__}"
    )
    parser.add_argument(
        'zip_name', type=str,
        help='Name of zip without (.zip) \n\teg: rom_name  out: rom_name_date-time.zip',
    )
    parser.add_argument(
        '-p', '--path', type=str, metavar='path', default='OTA',
        help='Path to files you want to creat OTA from them.'
    )
    return parser


if __name__ == '__main__':
    # use argparse to pass argument
    parser = init_argparse()
    args = parser.parse_args()

    # set zip_name
    zip_name = args.zip_name

    # specify zip_path
    zip_path = args.path

    # creat zip
    create_zip(zip_name, zip_path)

    # show elapsed time
    elapsed_time()
