import re

from traitlets import Bool, Unicode
from textwrap import dedent
import uuid
import os

from . import NbGraderPreprocessor
from .. import utils
import marshal


class ObfuscateTests(NbGraderPreprocessor):

    begin_obfuscate_test_delimeter = Unicode(
        "BEGIN OBFUSCATE TESTS",
        help="The delimiter marking the beginning of obfuscate test cases"
    ).tag(config=True)

    end_obfuscate_test_delimeter = Unicode(
        "END OBFUSCATE TESTS",
        help="The delimiter marking the end of obfuscate tests cases"
    ).tag(config=True)

    obfuscate_correct_message = Unicode(
        "Your solution is correct :-)",
        help="This message is printed if solution is correct"
    ).tag(config=True)
    obfuscate_incorrect_message = Unicode(
        "Your solution is incorrect :-(",
        help="This message is printed if solution is incorrect"
    ).tag(config=True)
    obfuscate_implement_message = Unicode(
        "Please implement your solution above and remove 'raise NotImplementedError'",
        help="This message is printed if NotImplementedError is raised"
    ).tag(config=True)

    enforce_metadata = Bool(
        True,
        help=dedent(
            """
            Whether or not to complain if cells containing obfuscate test regions
            are not marked as grade cells. WARNING: this will potentially cause
            things to break if you are using the full nbgrader pipeline. ONLY
            disable this option if you are only ever planning to use nbgrader
            assign.
            """
        )
    ).tag(config=True)

    def _obfuscate_test_region(self, cell):
        """Find a region in the cell that is delimeted by
        `self.begin_obfuscate_test_delimeter` and
        `self.end_obfuscate_test_delimeter`. Replace that region with
        obfuscated code.

        This modifies the cell in place, and then returns True if a
        obfuscate test region was removed, and False otherwise.
        """
        # pull out the cell input/source
        lines = cell.source.split("\n")

        new_lines = []
        in_test = False
        removed_test = False

        hidden_code = list()

        for line in lines:

            if in_test and not self.end_obfuscate_test_delimeter in line:
                hidden_code.append(line)
            elif in_test and self.end_obfuscate_test_delimeter in line:
                code = list()
                code.append('try:')
                for i in hidden_code:
                    code.append('    ' + i)
                code.append('    print("%s")'%self.obfuscate_correct_message)
                code.append('except AssertionError:')
                code.append('    print("%s")'%self.obfuscate_incorrect_message)
                code.append('except NotImplementedError:')
                code.append('    print("%s")'%self.obfuscate_implement_message)
                code = '\n'.join(code)
                code_obj = compile(code, '<string>', 'exec')
                bytes = marshal.dumps( code_obj )

                new_lines.append('import marshal; exec(marshal.loads({bc}) )'.format(
                    bc = repr(bytes)
                ))
#                new_lines.append(code)


            # begin the test area
            if self.begin_obfuscate_test_delimeter in line:
                # check to make sure this isn't a nested BEGIN HIDDEN TESTS
                # region
                if in_test:
                    raise RuntimeError(
                        "Encountered nested begin tests statements")
                in_test = True
                removed_test = True

            # end the solution area
            elif self.end_obfuscate_test_delimeter in line:
                    in_test = False

            # add lines as long as it's not in the hidden tests region
            elif not in_test:
                new_lines.append(line)
        # we finished going through all the lines, but didn't find a
        # matching END statment
        if in_test:
            raise RuntimeError("No end tests statement found")

        # replace the cell source
        cell.source = "\n".join(new_lines)

        return removed_test

    def preprocess(self, nb, resources):
        nb, resources = super(ObfuscateTests, self).preprocess(nb, resources)

        if 'celltoolbar' in nb.metadata:
            del nb.metadata['celltoolbar']
        return nb, resources
    def __init__(self, **args):
        super().__init__(**args)
        self.deletefile = True
    def preprocess_cell(self, cell, resources, cell_index):
        # remove hidden test regions
        removed_test = self._obfuscate_test_region(cell)
        # determine whether the cell is a grade cell
        is_grade = utils.is_grade(cell)

        # check that it is marked as a grade cell if we remove a test
        # region -- if it's not, then this is a problem, because the cell needs
        # to be given an id
        if not is_grade and removed_test:
            if self.enforce_metadata:
                raise RuntimeError(
                    "Obfuscate test region detected in a non-grade cell; "
                    "please make sure all solution regions are within "
                    "'Autograder tests' cells."
                )

        return cell, resources
