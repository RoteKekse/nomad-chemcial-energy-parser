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

from nomad.datamodel.metainfo.basesections import CompositeSystemReference
from nomad.datamodel import EntryArchive
from nomad.parsing import MatchingParser
from nomad.datamodel.metainfo.annotations import (
    ELNAnnotation,
)
from nomad.datamodel.data import (
    EntryData,
)
from nomad.metainfo import (
    Quantity,
)
from nomad.datamodel.metainfo.basesections import (
    Activity,
)
import os

from baseclasses.helper.utilities import find_sample_by_id, create_archive, get_entry_id_from_file_name, get_reference, search_class

from ce_nome_s import CE_NOME_Chronoamperometry, CE_NOME_CyclicVoltammetry, \
    CE_NOME_Chronopotentiometry, CE_NOME_Chronopotentiometry, CE_NOME_Chronocoulometry, CE_NOME_OpenCircuitVoltage,\
    CE_NOME_ElectrochemicalImpedanceSpectroscopy, CE_NOME_LinearSweepVoltammetry


'''
This is a hello world style example for an example parser/converter.
'''


class ParsedGamryFile(EntryData):
    activity = Quantity(
        type=Activity,
        shape=["*"],
        a_eln=ELNAnnotation(
            component='ReferenceEditQuantity',
        )
    )


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
        connected_experiments = []
        # if "COLLECT" in metadata["TAG"] or ("CV" in metadata["TAG"] and "WE2CURVE" in metadata):
        if "METHOD" in metadata:
            methods = metadata.get("METHOD").split("-")
        else:
            methods = [metadata.get("TAG")]

        for method in methods:
            file_name = f"{measurement_name}_{method}.archive.json"
            eid = get_entry_id_from_file_name(file_name, archive)
            connected_experiments.append(get_reference(archive.metadata.upload_id, eid))
            if "CV" in method:
                measurements.append(
                    (eid, file_name, CE_NOME_CyclicVoltammetry()))

            if "LSV" in method:
                measurements.append(
                    (eid, file_name, CE_NOME_LinearSweepVoltammetry()))

            if "CHRONOA" in method or "CA" in method:
                measurements.append(
                    (eid, file_name, CE_NOME_Chronoamperometry()))

            if "CHRONOP" in method or "CP" in method:
                measurements.append(
                    (eid, file_name, CE_NOME_Chronopotentiometry()))

            if "CHRONOC" in method or "CC" in method:
                measurements.append((eid, file_name, CE_NOME_Chronocoulometry()))

            if "CORPOT" in method:
                measurements.append(
                    (eid, file_name, CE_NOME_OpenCircuitVoltage()))

            if "EISPOT" in method or "PEIS" in method:
                measurements.append(
                    (eid, file_name, CE_NOME_ElectrochemicalImpedanceSpectroscopy()))

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

        refs = []
        for idx, (eid, name, measurement) in enumerate(measurements):
            measurement.data_file = measurement_name
            measurement.connected_experiments = [c for c in connected_experiments if eid not in c]
            measurement.function = "Generator"
            if idx > 0:
                measurement.function = "Detector"
            if sample_ref is not None:
                measurement.samples = [CompositeSystemReference(reference=sample_ref)]
            if environment_ref is not None:
                measurement.environment = environment_ref
            if setup_ref is not None:
                measurement.setup = setup_ref
            name = name.replace("#", "run")
            create_archive(measurement, archive, name)
            refs.append(get_reference(archive.metadata.upload_id, eid))

        archive.data = ParsedGamryFile(activity=refs)
        archive.metadata.entry_name = measurement_name
