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

from ce_nome_s import CE_NOME_UVvismeasurement
from baseclasses.helper.utilities import create_archive, search_class, get_reference

import os
import datetime

'''
This is a hello world style example for an example parser/converter.
'''


class UVvisParser(MatchingParser):
    def __init__(self):
        super().__init__(
            name='parsers/hysprintjv', code_name='HYSPRINTJV', code_homepage='https://www.example.eu/',
            supported_compressions=['gz', 'bz2', 'xz']
        )

    def parse(self, mainfile: str, archive: EntryArchive, logger):
        # Log a hello world, just to get us started. TODO remove from an actual parser.

        from baseclasses.helper.utilities import get_encoding
        with open(mainfile, "br") as f:
            encoding = get_encoding(f)

        mainfile_split = os.path.basename(mainfile).split('.')
        notes = ''
        if len(mainfile_split) > 2:
            notes = mainfile_split[1]

        uvvis = CE_NOME_UVvismeasurement()

        archive.metadata.entry_name = os.path.basename(mainfile)
        sample = search_class(archive, "CE_NOME_Sample")
        if sample is not None:
            upload_id, entry_id = sample["upload_id"], sample["entry_id"]
            uvvis.samples = [get_reference(upload_id, entry_id)]
        uvvis.name = f"{mainfile_split[0]} {notes}"
        uvvis.description = f"Notes from file name: {notes}"
        uvvis.data_file = [os.path.basename(mainfile)]
        uvvis.datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        file_name = f'{os.path.basename(mainfile)}.archive.json'
        create_archive(uvvis, archive, file_name)
