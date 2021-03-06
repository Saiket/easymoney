#!/usr/bin/env python3
"""Entry point for the EasyMoney application."""


__copyright__ = 'Copyright © 2019, Erik Anderson, James Abernathy, and Tyler Gerritsen'
__license__ = 'MIT'


import os.path
import sys

def pythonw_disable_std_streams(
) -> None:
    """Disable output streams when running in console-less mode on Windows
    (using `pythonw`) to prevent a crash when Kivy attempts to print to
    unopened `stdout` and `stderr`.
    """
    python_filename_without_extension = os.path.splitext(
        os.path.basename(sys.executable))[0] 
    if python_filename_without_extension == 'pythonw':
        # Interpreter hasn't opened standard pipes
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

        # Don't waste time printing logs
        os.environ['KIVY_NO_CONSOLELOG'] = '1'

if __name__ == '__main__':
    # Disable streams before anything attempts to print
    pythonw_disable_std_streams()


# Store Kivy configuration and logs in a local folder
os.environ['KIVY_HOME'] = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '.kivy')

import kivy
kivy.require('1.9.0')

from model.sim_model import SimModel
from controller.sim_controller import SimController
from view.logging_view import LoggingView
from view.window_view import WindowView




def main() -> None:
    """Program entry point that opens the application window."""
    controller = SimController(SimModel())

    logger = LoggingView(controller)
    window = WindowView(controller)

    window.run()




if __name__ == '__main__':
    main()
