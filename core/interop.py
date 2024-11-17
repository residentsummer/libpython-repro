
__BORROWED = {}

def borrow(pyobj):
    __BORROWED[id(pyobj)] = pyobj
    return pyobj

def release(pyobj):
    del __BORROWED[id(pyobj)]
