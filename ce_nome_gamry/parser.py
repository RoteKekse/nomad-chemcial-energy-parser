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

import os

from baseclasses.helper.utilities import find_sample_by_id, create_archive, get_entry_id_from_file_name, get_reference, search_class

from nomad.datamodel.metainfo.basesections import CompositeSystemReference
'''
This is a hello world style example for an example parser/converter.
'''


class GamryParser(MatchingParser):
    def __init__(self):
        super().__init__(
            name='parsers/cenomegamry',
            code_name='CENOMEGAMRY',
            code_homepage='https://www.example.eu/',
            supported_compressions=[
                'gz',
                'bz2',
                'xz'])

    def parse(self, mainfile: str, archive: EntryArchive, logger):
        # Log a hello world, just to get us started. TODO remove from an actual
        # parser.
        from baseclasses.helper.file_parser.gamry_parser import get_header_and_data
        metadata, _ = get_header_and_data(filename=mainfile)

        measurement_base, measurement_name = os.path.split(mainfile)

        measurements = []
        if "COLLECT" in metadata["TAG"]:
            from ce_nome_s import CE_NOME_Chronoamperometry, CE_NOME_CyclicVoltammetry
            mCA = CE_NOME_Chronoamperometry()
            mCA.station = metadata.get("RINGPSTAT")

            mCV = CE_NOME_CyclicVoltammetry()
            mCV.station = metadata.get("RINGPSTAT")

            nCA = f"{measurement_name}_CA.archive.json"
            nCV = f"{measurement_name}_CV.archive.json"
            eid_CA = get_entry_id_from_file_name(nCA, archive)
            eid_CV = get_entry_id_from_file_name(nCV, archive)

            mCA.connected_experiments = [get_reference(
                archive.metadata.upload_id, eid_CV)]
            mCV.connected_experiments = [get_reference(
                archive.metadata.upload_id, eid_CA)]

            measurements.append((nCA, mCA))
            measurements.append((nCV, mCV))

        if "CHRONOA" in metadata["TAG"]:
            from ce_nome_s import CE_NOME_Chronoamperometry
            measurements.append(
                (measurement_name, CE_NOME_Chronoamperometry()))

        if "CHRONOP" in metadata["TAG"]:
            from ce_nome_s import CE_NOME_Chronopotentiometry
            measurements.append(
                (measurement_name, CE_NOME_Chronopotentiometry()))

        if "CV" in metadata["TAG"]:
            from ce_nome_s import CE_NOME_CyclicVoltammetry
            measurements.append(
                (measurement_name, CE_NOME_CyclicVoltammetry()))

        if "CHRONOC" in metadata["TAG"]:
            from ce_nome_s import CE_NOME_Chronocoulometry
            measurements.append((measurement_name, CE_NOME_Chronocoulometry()))

        if "CORPOT" in metadata["TAG"]:
            from ce_nome_s import CE_NOME_OpenCircuitVoltage
            measurements.append(
                (measurement_name, CE_NOME_OpenCircuitVoltage()))

        if "EISPOT" in metadata["TAG"]:
            from ce_nome_s import CE_NOME_ElectrochemicalImpedanceSpectroscopy
            measurements.append(
                (measurement_name, CE_NOME_ElectrochemicalImpedanceSpectroscopy()))

        archive.metadata.entry_name = os.path.basename(mainfile)

        sample_id = metadata.get("SAMPLEID")
        setup_id = metadata.get("ECSETUPID")
        environment_id = metadata.get("ENVIRONMENTID")
        sample_ref = find_sample_by_id(archive, sample_id)
        environment_ref = find_sample_by_id(archive, environment_id)
        setup_ref = find_sample_by_id(archive, setup_id)

        if sample_ref is None:
            sample = search_class(archive, "CE_NOME_Sample")
            if sample is not None:
                upload_id, entry_id = sample["upload_id"], sample["entry_id"]
                sample_ref = get_reference(upload_id, entry_id)

        if environment_ref is None:
            environment = search_class(archive, "CE_NOME_Environment")
            if environment is not None:
                upload_id, entry_id = environment["upload_id"], environment["entry_id"]
                environment_ref = get_reference(upload_id, entry_id)

        if setup_ref is None:
            setup = search_class(archive, "CE_NOME_ElectroChemicalSetup")
            if setup is not None:
                upload_id, entry_id = setup["upload_id"], setup["entry_id"]
                setup_ref = get_reference(upload_id, entry_id)

        for name, measurement in measurements:
            measurement.data_file = measurement_name
            if sample_ref is not None:
                measurement.samples = [CompositeSystemReference(reference=sample_ref)]
            if environment_ref is not None:
                measurement.environment = environment_ref
            if setup_ref is not None:
                measurement.setup = setup_ref
            if ".archive.json" not in name:
                name += ".archive.json"
            name = name.replace("#", "run")
            create_archive(measurement, archive, name)
