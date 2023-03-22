import traceback
import inspect

# from common_libs.ansible_driver.functions.mydebug import DebugBackTrace, DebugPrint
# DbgMsg = "aaaa"
# DebugPrint(os.path.basename(inspect.currentframe().f_code.co_filename), str(inspect.currentframe().f_lineno), DbgMsg)

def DebugPrint(func, file, line, msg):
    fd = open("/tmp/eno", "a")

    log = '<<%s>><<%s>><<%s>>:<<%s>>\n' % (file, func, str(line), str(msg))
    fd.write(log)

    fd.close()

def DebugBackTrace():
    print_backtrace = "---------------backtrace-------------\n"
    trace = inspect.currentframe()
    while trace:
        print_backtrace += '%s : %s : %s\n' % (trace.f_code.co_filename, trace.f_code.co_name, trace.f_lineno)
        trace = trace.f_back
    print_backtrace += "-------------------------------------\n"
    print(print_backtrace)