"""
Created on Mon Jun 23 18:35:11 2025

@author: P Jarrin (Geoazur, IRD, CNRS, France)

Check if a desired executable is installed in the OS

"""

import sys
import shutil
from colors import red

class ExecutableChecker:

    def __init__(self, tools):
        """
        tools: list of executable names to check
        """
        self.tools = tools if isinstance(tools, list) else [tools]
        self.paths = {}

        self._check_tools()

    def _check_tools(self):
        missing = []

        for tool in self.tools:
            path = shutil.which(tool)

            if path:
                self.paths[tool] = path
            else:
                missing.append(tool)

        if missing:
            for tool in missing:
                print(red(f" -- Error: Could not find {tool.upper()} in your system"))
            sys.exit()

    def get_path(self, tool):
        return self.paths.get(tool)

