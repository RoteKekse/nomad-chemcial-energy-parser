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


import json
import os
import datetime

from .helpers import set_multiple_data, set_data
from baseclasses.helper.utilities import find_sample_by_id, create_archive, get_entry_id_from_file_name, get_reference


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
        from baseclasses.helper.gamry_parser import get_header_and_data
        metadata, _ = get_header_and_data(filename=mainfile)

        measurements = []
        # if "_#1.DTA" in mainfile:
        #     if "CHRONOA" in metadata["TAG"]:
        #         from baseclasses.chemical_energy.chronoamperometry import CAPropertiesWithData
        #         from baseclasses.helper.gamry_archive import get_cam_properties_data
        #         from ce_nome_s import CE_NOME_Chronoamperometry_Multiple

        #         measurements.append(set_multiple_data(
        #             mainfile, CE_NOME_Chronoamperometry_Multiple, CAPropertiesWithData, get_cam_properties_data))
        #     if "EISPOT" in metadata["TAG"]:
        #         from baseclasses.chemical_energy.electorchemical_impedance_spectroscopy import EISPropertiesWithData
        #         from baseclasses.helper.gamry_archive import get_eis_properties_data
        #         from ce_nome_s import CE_NOME_ElectrochemicalImpedanceSpectroscopy_Multiple

        #         measurements.append(set_multiple_data(
        #             mainfile, CE_NOME_ElectrochemicalImpedanceSpectroscopy_Multiple, EISPropertiesWithData, get_eis_properties_data))

        if "COLLECT" in metadata["TAG"]:
            from baseclasses.chemical_energy.chronoamperometry import CAProperties
            from baseclasses.helper.gamry_archive import get_ca_properties
            from ce_nome_s import CE_NOME_Chronoamperometry
            nCA, mCA = set_data(
                mainfile, CE_NOME_Chronoamperometry, CAProperties)
            mCA.station = metadata.get("RINGPSTAT")

            from baseclasses.chemical_energy.cyclicvoltammetry import CVProperties
            from baseclasses.helper.gamry_archive import get_cv_properties
            from ce_nome_s import CE_NOME_CyclicVoltammetry

            nCV, mCV = set_data(
                mainfile, CE_NOME_CyclicVoltammetry, CVProperties, get_cv_properties)
            mCV.station = metadata.get("DISKPSTAT")

            nCA += "_CA.archive.json"
            nCV += "_CV.archive.json"
            eid_CA = get_entry_id_from_file_name(nCA, archive)
            eid_CV = get_entry_id_from_file_name(nCV, archive)

            mCA.connected_experiments = [get_reference(
                archive.metadata.upload_id, eid_CV)]
            mCV.connected_experiments = [get_reference(
                archive.metadata.upload_id, eid_CA)]

            measurements.append((nCA, mCA))
            measurements.append((nCV, mCV))

        if "CHRONOA" in metadata["TAG"]:
            from baseclasses.chemical_energy.chronoamperometry import CAProperties
            from baseclasses.helper.gamry_archive import get_ca_properties
            from ce_nome_s import CE_NOME_Chronoamperometry

            measurements.append(set_data(
                mainfile, CE_NOME_Chronoamperometry, CAProperties, get_ca_properties))
        if "CV" in metadata["TAG"]:
            from baseclasses.chemical_energy.cyclicvoltammetry import CVProperties
            from baseclasses.helper.gamry_archive import get_cv_properties
            from ce_nome_s import CE_NOME_CyclicVoltammetry

            measurements.append(set_data(
                mainfile, CE_NOME_CyclicVoltammetry, CVProperties, get_cv_properties))

        if "CHRONOC" in metadata["TAG"]:
            from baseclasses.chemical_energy.chronocoulometry import CCProperties
            from baseclasses.helper.gamry_archive import get_cc_properties
            from ce_nome_s import CE_NOME_Chronocoulometry

            measurements.append(set_data(
                mainfile, CE_NOME_Chronocoulometry, CCProperties, get_cc_properties))
        if "CORPOT" in metadata["TAG"]:
            from baseclasses.chemical_energy.opencircuitvoltage import OCVProperties
            from baseclasses.helper.gamry_archive import get_ocv_properties
            from ce_nome_s import CE_NOME_OpenCircuitVoltage

            measurements.append(set_data(
                mainfile, CE_NOME_OpenCircuitVoltage, OCVProperties, get_ocv_properties))

        if "EISPOT" in metadata["TAG"]:
            from baseclasses.chemical_energy.electorchemical_impedance_spectroscopy import EISProperties
            from baseclasses.helper.gamry_archive import get_eis_properties
            from ce_nome_s import CE_NOME_ElectrochemicalImpedanceSpectroscopy

            measurements.append(set_data(
                mainfile, CE_NOME_ElectrochemicalImpedanceSpectroscopy, EISProperties, get_eis_properties))

        archive.metadata.entry_name = os.path.basename(mainfile)

        sample_id = metadata.get("SAMPLEID")
        setup_id = metadata.get("ECSETUPID")
        environment_id = metadata.get("ENVIRONMENTID")
        sample_ref = find_sample_by_id(archive, sample_id)
        environment_ref = find_sample_by_id(archive, environment_id)
        setup_ref = find_sample_by_id(archive, setup_id)

        for name, measurement in measurements:
            if sample_ref is not None:
                measurement.samples = [sample_ref]
            if environment_ref is not None:
                measurement.environment = environment_ref
            if setup_ref is not None:
                measurement.setup = setup_ref
            if ".archive.json" not in name:
                name += ".archive.json"
            name = name.replace("#", "run")
            create_archive(measurement, archive, name)
