#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD. See https://nomad-lab.eu for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from nomad.datamodel import EntryArchive
from nomad.parsing import MatchingParser

from ce_nome_s import (CE_NOME_Measurement,
                       CE_NOME_PumpRateMeasurement,
                       CE_NOME_PhaseFluorometryOxygen)


from baseclasses.helper.utilities import get_reference, create_archive, search_class
from nomad.datamodel.metainfo.basesections import CompositeSystemReference


import os
import datetime

'''
This is a hello world style example for an example parser/converter.
'''


class CENOMEcsvParser(MatchingParser):
    def __init__(self):
        super().__init__(
            name='parsers/CENOMEcsv', code_name='CENOMEcsv', code_homepage='https://www.example.eu/',
            supported_compressions=['gz', 'bz2', 'xz']
        )

    def parse(self, mainfile: str, archive: EntryArchive, logger):
        # Log a hello world, just to get us started. TODO remove from an actual parser.

        mainfile_split = os.path.basename(mainfile).split('.')
        notes = ''
        if len(mainfile_split) > 2:
            notes = mainfile_split[1]
        entry = CE_NOME_Measurement()

        if mainfile_split[-1].endswith("csv"):
            with open(mainfile) as f:
                first_line = f.readline()
            if first_line.startswith("Time;Push Pull"):
                entry = CE_NOME_PumpRateMeasurement()

            if first_line.startswith("1.5.1.23"):
                entry = CE_NOME_PhaseFluorometryOxygen()
        elif mainfile_split[-1].endswith("xlsx"):
            entry = CE_NOME_PhaseFluorometryOxygen()

        archive.metadata.entry_name = os.path.basename(mainfile)
        sample = search_class(archive, "CE_NOME_Sample")
        if sample is not None:
            upload_id, entry_id = sample["upload_id"], sample["entry_id"]
            entry.samples = [CompositeSystemReference(reference=get_reference(upload_id, entry_id))]

        environment = search_class(archive, "CE_NOME_Environment")
        if environment is not None:
            upload_id, entry_id = environment["upload_id"], environment["entry_id"]
            entry.environment = get_reference(upload_id, entry_id)

        setup = search_class(archive, "CE_NOME_ElectroChemicalSetup")
        if setup is not None:
            upload_id, entry_id = setup["upload_id"], setup["entry_id"]
            entry.setup = get_reference(upload_id, entry_id)

        entry.name = f"{mainfile_split[0]} {notes}"
        entry.description = f"Notes from file name: {notes}"
        try:
            entry.data_file = os.path.basename(mainfile)
        except:
            entry.data_file = [os.path.basename(mainfile)]
        entry.datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        file_name = f'{os.path.basename(mainfile)}.archive.json'
        create_archive(entry, archive, file_name)
