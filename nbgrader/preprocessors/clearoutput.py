from nbconvert.preprocessors import ClearOutputPreprocessor
from traitlets import Bool, Unicode
from . import NbGraderPreprocessor

class ClearOutput(NbGraderPreprocessor, ClearOutputPreprocessor):
    clear_deaktivate_id = Unicode(
        "DO NOT CLEAR OUTPUT",
        help="if ### <clear_deaktivate_id> is the first entry in a cell the output is not cleared"
    ).tag(config=True)

    def preprocess_cell(self, cell, resources, cell_index):
        if cell.source.startswith('### ' + self.clear_deaktivate_id):
            return cell, resources
        else:
            return super(ClearOutput, self).preprocess_cell(cell, resources, cell_index)
