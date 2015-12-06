"""syschangemon exception classes."""

class SysChangeMonError(Exception):
    """Generic errors."""
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg

class SysChangeMonConfigError(SysChangeMonError):
    """Config related errors."""
    pass

class SysChangeMonRuntimeError(SysChangeMonError):
    """Generic runtime errors."""
    pass

class SysChangeMonArgumentError(SysChangeMonError):
    """Argument related errors."""
    pass
