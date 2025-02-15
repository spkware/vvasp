# This file for command line interface parsing stuff
# don't import qt if not needed so it doesnt run by default.
# I was thinking that the CLI can also just plot a figure from an saved file.
# like load saved planning

from .utils import *

def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(
        description="Volume Visualization and Stereotaxic Planning")
    parser.add_argument('-e','--experiment_file',
                        metavar='filepath',
                        type=str,
                        default=None,
                        nargs="?")
    
    parser.add_argument('--atlas_name',
                        metavar='atlas',
                        type=str,
                        default=None,
                        nargs="?")

    parser.add_argument('--min_tree_depth',
                        type=int,
                        default=6,
                        nargs="?")

    parser.add_argument('--max_tree_depth',
                        type=int,
                        default=8,
                        nargs="?")

    opts = parser.parse_args()

    from .widgets import QApplication, VVASPPlanner
    app = QApplication(sys.argv)
    #w = VVASP(filename = opts.filename,
    #          atlas_name = opts.atlas,)
    w = VVASPPlanner(**vars(opts))
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()
