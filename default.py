"""
    Plugin for executing programs
"""

import sys

# plugin constants
__plugin__ = "Executor Plugin"
__author__ = "kitlaan"
__version__ = "0.1.0"

if __name__ == "__main__":
    import resources.lib.executor as plugin
    plugin.Main()

sys.modules.clear()
