import timeout_decorator
import subprocess
import shlex


def execute_program(cmd):
    args = shlex.split(cmd)
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    err = err.decode().strip()
    out = out.decode().strip()
    print(err)
    print(out)
    return err, out


def program_return_error(cmd):
    err, out = execute_program(cmd)
    return err


@timeout_decorator.timeout(10)
def execute_program_with_timeout(cmd):
    return execute_program(cmd)
