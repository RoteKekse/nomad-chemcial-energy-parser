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
from baseclasses.helper.utilities import set_sample_reference, create_archive


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

        cam_measurements = None
        if "_#1.DTA" in mainfile:
            if "CHRONOA" in metadata["TAG"]:
                from baseclasses.chemical_energy.chronoamperometry import CAPropertiesWithData
                from baseclasses.helper.gamry_archive import get_cam_properties_data
                from ce_nome_s import CE_NOME_Chronoamperometry_Multiple

                measurement_name_overall, cam_measurements = set_multiple_data(
                    mainfile, CE_NOME_Chronoamperometry_Multiple, CAPropertiesWithData, get_cam_properties_data)
            if "EISPOT" in metadata["TAG"]:
                from baseclasses.chemical_energy.electorchemical_impedance_spectroscopy import EISPropertiesWithData
                from baseclasses.helper.gamry_archive import get_eis_properties_data
                from ce_nome_s import CE_NOME_ElectrochemicalImpedanceSpectroscopy_Multiple

                measurement_name_overall, cam_measurements = set_multiple_data(
                    mainfile, CE_NOME_ElectrochemicalImpedanceSpectroscopy_Multiple, EISPropertiesWithData, get_eis_properties_data)

        else:
            if "CHRONOA" in metadata["TAG"]:
                from baseclasses.chemical_energy.chronoamperometry import CAProperties
                from baseclasses.helper.gamry_archive import get_ca_properties
                from ce_nome_s import CE_NOME_Chronoamperometry

                measurement_name_overall, cam_measurements = set_data(
                    mainfile, CE_NOME_Chronoamperometry, CAProperties, get_ca_properties)
            if "CV" in metadata["TAG"]:
                from baseclasses.chemical_energy.cyclicvoltammetry import CVProperties
                from baseclasses.helper.gamry_archive import get_cv_properties
                from ce_nome_s import CE_NOME_CyclicVoltammetry

                measurement_name_overall, cam_measurements = set_data(
                    mainfile, CE_NOME_CyclicVoltammetry, CVProperties, get_cv_properties)

            if "CHRONOC" in metadata["TAG"]:
                from baseclasses.chemical_energy.chronocoulometry import CCProperties
                from baseclasses.helper.gamry_archive import get_cc_properties
                from ce_nome_s import CE_NOME_Chronocoulometry

                measurement_name_overall, cam_measurements = set_data(
                    mainfile, CE_NOME_Chronocoulometry, CCProperties, get_cc_properties)
            if "CORPOT" in metadata["TAG"]:
                from baseclasses.chemical_energy.opencircuitvoltage import OCVProperties
                from baseclasses.helper.gamry_archive import get_ocv_properties
                from ce_nome_s import CE_NOME_OpenCircuitVoltage

                measurement_name_overall, cam_measurements = set_data(
                    mainfile, CE_NOME_OpenCircuitVoltage, OCVProperties, get_ocv_properties)

            if "EISPOT" in metadata["TAG"]:
                from baseclasses.chemical_energy.electorchemical_impedance_spectroscopy import EISProperties
                from baseclasses.helper.gamry_archive import get_eis_properties
                from ce_nome_s import CE_NOME_ElectrochemicalImpedanceSpectroscopy

                measurement_name_overall, cam_measurements = set_data(
                    mainfile, CE_NOME_ElectrochemicalImpedanceSpectroscopy, EISProperties, get_eis_properties)

        archive.metadata.entry_name = os.path.basename(mainfile)

        if "SMPLID" in metadata or "ECCID" in metadata:
            from nomad.search import search
            for key in ["ECCID", "SMPLID"]:
                if key not in metadata:
                    continue
                search_id = metadata[key]
                query = {
                    'results.eln.lab_ids': search_id
                }
                search_result = search(
                    owner='all',
                    query=query,
                    user_id=archive.metadata.main_author.user_id)
                if len(search_result.data) == 1:
                    data = search_result.data[0]
                    upload_id, entry_id = data["upload_id"], data["entry_id"]
                    if data["entry_type"] == "CE_NOME_ElectroChemicalCell":
                        cam_measurements.electrochemical_cell = f'../uploads/{upload_id}/archive/{entry_id}#data'
                    if data["entry_type"] in ["CE_NOME_Electrode", "CE_NOME_Sample"]:
                        cam_measurements.working_electrode = f'../uploads/{upload_id}/archive/{entry_id}#data'

        # archive.data = cam_measurements
        if cam_measurements is not None:
            file_name = f'{measurement_name_overall}.archive.json'
            create_archive(cam_measurements, archive, file_name)
