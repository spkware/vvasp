# This file for command line interface parsing stuff
# don't import qt if not needed so it doesnt run by default.
# I was thinking that the CLI can also just plot a figure from an saved file.
# like load saved planning

from .utils import *

def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Volume Visualization and Stereotaxic Planning")
    parser.add_argument('--filename',
                        metavar='filename',
                        type=str,
                        default=None, # TODO: write the help for this
                        nargs="?")
    
    parser.add_argument('--atlas_name',
                        metavar='atlas',
                        type=str,
                        default=None, # TODO: write the help for this
                        nargs="?")

    parser.add_argument('--min_tree_depth',
                        type=int,
                        default=6, # TODO: write the help for this
                        nargs="?")

    parser.add_argument('--max_tree_depth',
                        type=int,
                        default=8, # TODO: write the help for this
                        nargs="?")

    opts = parser.parse_args()

    from .widgets import QApplication, VVASP
    app = QApplication(sys.argv)
    #w = VVASP(filename = opts.filename,
    #          atlas_name = opts.atlas,)
    w = VVASP(**vars(opts))
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()
