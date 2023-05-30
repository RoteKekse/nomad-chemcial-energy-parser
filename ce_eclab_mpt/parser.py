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
from baseclasses.helper.utilities import find_sample_by_id, create_archive

import os


'''
This is a hello world style example for an example parser/converter.
'''


class MPTParser(MatchingParser):
    def __init__(self):
        super().__init__(
            name='parsers/ceeclabmpt',
            code_name='CEMPT',
            supported_compressions=[
                'gz',
                'bz2',
                'xz'])

    def parse(self, mainfile: str, archive: EntryArchive, logger):

        mainfile_split = os.path.basename(mainfile).split('.')
        notes = mainfile_split[0]
        if len(mainfile_split) > 2:
            notes = mainfile_split[1]
        cam_measurements = None

        from baseclasses.helper.mps_file_parser import read_mpt_file
        metadata, _, technique = read_mpt_file(mainfile)

        if "Cyclic Voltammetry" in technique:
            from ce_wannsee_s import Wannsee_B307_CyclicVoltammetry_ECLab
            cam_measurements = Wannsee_B307_CyclicVoltammetry_ECLab()

        if "Open Circuit Voltage" in technique:
            from ce_wannsee_s import Wannsee_B307_OpenCircuitVoltage_ECLab
            cam_measurements = Wannsee_B307_OpenCircuitVoltage_ECLab()

        if "Potentio Electrochemical Impedance Spectroscopy" in technique:
            from ce_wannsee_s import Wannsee_B307_ElectrochemicalImpedanceSpectroscopy_ECLab
            cam_measurements = Wannsee_B307_ElectrochemicalImpedanceSpectroscopy_ECLab()

        archive.metadata.entry_name = os.path.basename(mainfile)

        sample_id = metadata.get("Electrode material")
        setup_id = metadata.get("Initial state")
        environment_id = metadata.get("Electrolyte")

        from baseclasses.chemical_energy import PotentiostatSetup
        setup_parameters = PotentiostatSetup()
        setup_params = metadata.get("Comments").split(",")
        for param in setup_params:
            if "=" not in param:
                continue
            try:
                key, value = param.split("=")
                setattr(setup_parameters, key.strip(), value.strip())
            except:
                pass

        cam_measurements.setup_parameters = setup_parameters
        cam_measurements.samples = [find_sample_by_id(archive, sample_id)]
        cam_measurements.environment = find_sample_by_id(
            archive, environment_id)
        cam_measurements.setup = find_sample_by_id(archive, setup_id)

        cam_measurements.name = f"{mainfile_split[0]} {notes}"
        cam_measurements.description = f"Notes from file name: {notes}"
        cam_measurements.data_file = os.path.basename(mainfile)

        if cam_measurements is not None:
            file_name = f'{os.path.basename(mainfile)}.archive.json'
            create_archive(cam_measurements, archive, file_name)
