import timeout_decorator
import subprocess
import shlex
import os


class ShellExec:

    @staticmethod
    def execute_program(cmd, silent=False):
        args = shlex.split(cmd)
        p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        err = err.decode().strip()
        out = out.decode().strip()
        if not silent:
            print(err)
            print(out)
        return err, out

    @staticmethod
    def execute_system(cmd):
        os.system(cmd)

    @staticmethod
    def program_return_error(cmd):
        err, out = ShellExec.execute_program(cmd)
        return err

    @staticmethod
    @timeout_decorator.timeout(10)
    def execute_program_with_timeout(cmd):
        return ShellExec.execute_program(cmd)
