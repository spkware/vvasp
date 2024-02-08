# This file for command line interface parsing stuff
# don't import qt if not needed so it doesnt run by default.
# I was thinking that the CLI can also just plot a figure from an saved file.
# like load saved planning

from .utils import *

def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Volume Visualization and Stereotaxic Planning")
    parser.add_argument('filename',
                        metavar='filename',
                        type=str,
                        default=None, # TODO: write the help for this
                        nargs="?")
    
    parser.add_argument('atlas',
                        metavar='atlas',
                        type=str,
                        default='CCF25', # TODO: write the help for this
                        nargs="?")

    opts = parser.parse_args()
    from .widgets import QApplication, VVASP
    app = QApplication(sys.argv)
    w = VVASP(filename = opts.filename,
              atlas = opts.atlas)
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()
