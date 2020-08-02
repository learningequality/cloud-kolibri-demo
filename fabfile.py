from collections import defaultdict
import dns.resolver
import json
import os
import time
import requests
import socket
from urllib.parse import urlparse

from fabric.api import env, task, local, sudo, run, settings
from fabric.api import get, put, require
from fabric.colors import red, green, blue, yellow
from fabric.context_managers import cd, prefix, show, hide, shell_env
from fabric.contrib.files import exists, sed, upload_template
from fabric.utils import puts





# INVENTORY
################################################################################

env.roledefs = {
    'pradigi-demo': {
        'hosts':['35.196.179.152'],
        'channels_to_import': [], # 'f9da12749d995fa197f8b4c0192e7b2c'],  # PraDigi
        'facility_name': 'PraDigi Demo Server',
        'hostname': 'pradigi-demo.learningequality.org',
    },
    #
    # QA DEMO SERVERS
    #
    'pradigi-demo-backup': {
        'hosts':['35.196.115.213'],
        'channels_to_import': [],
        #['f9da12749d995fa197f8b4c0192e7b2c',
        #                       'e6af491e90f642a9bf12d549bab662aa'],
        'facility_name': 'pradigi demo backup',
        'hostname': 'pradigi-demo-backup.learningequality.org',
    },
    'davemckee-demo': {
        'hosts':['35.231.153.103'],
        'channels_to_import': [
            '935cf973324c53b8aeeae1fea35e0ded',  # Noktta
            'ce1361bcf5955df596e8d988f7ba2c37',  # ArtsEdge
            'ddb7b46f75575d16aa2223ba822e1c06',  # NASASpacePlace
            '0d4fd88c4882573caa02110243b94c30',  # MIT-chemistry thing
            # '0d07636e2f20510383a7d813c8d4233f',  # British Council LearnEnglish
            'bafb26304c4a5286ae207764463a5a63',  # Illustrative Math
        ],
        'facility_name': 'Dave McKee Demo',
        'hostname': 'davemckee-demo.learningequality.org',
    },
    'alejandro-demo': {
        'hosts':['35.227.71.104'],
        'channels_to_import': [
            'da53f90b1be25752a04682bbc353659f',  # Ciencia NASA
            '2748b6a3569a55f5bd6e35a70e2be7ee',  # EDSITEment
            'e66cd89375845ebf864ea00005be902d',  # ELD Teacher Professional Course
            'faf284a5469d54b8b06881491196888e',  # Laboratoria
            '1d13b59b62b85470b61483fa63c530a2',  # Libretext OER Library
            'd6a3e8b17e8a5ac9b021f378a15afbb4',  # ReadWriteThink
            '41e303331a005007a38dbd85f6341b36',  # TeachEngineering
            '424bd5474e3d5e56980a2e6783eb0dc6',  # TeachEngineering (es)
            'eac7ff5d4647582d9bcbefea7323fcb1',  # TESSIndia
            'c4ad70f67dff57738591086e466f9afc',  # Proyecto Descartes (Ling Yi)
            # '668a1d198f2e5269939df31dd8c36efb',  # TED Talks Arabic Subtitles
        ],
        'facility_name': 'alejandro demo',
        'hostname': 'alejandro-demo.learningequality.org',
    },
    'kolibridemo-ar': {
        'hosts':['35.246.148.139'],
        'channels_to_import': [
            '9c22d36a81ba5eb0842f9192a18d9623',    # Abdulla Eid Network (العربيّة)
            'dd530f50b10e5864bad2f4c4d4050584',    # Sehha wa Sa’adah: Dubai Health Authority (العربيّة)
            'c150ea1d69495d37b5b0ac6f017e9bfb',    # 3asafeer (العربيّة)
            '935cf973324c53b8aeeae1fea35e0ded',    # Noktta (العربيّة)
            '77195c11baa05d3f886d02578cef80d0',    # Orange NGO (العربيّة)
            'e66cd89375845ebf864ea00005be902d',    # ELD Teacher Professional Development Courses (العربيّة)
            # 'd76da4d36cfd59279b575dfc6017aa13',    # Kamkalima (العربيّة)
            '3a9c1cbc13ca5efe8500e20307f90a57',    # PhET Interactive Simulation (العربيّة)
            '27bb0abc24d44dd9896be50d47b2357e',    # Living Values Education (العربيّة)
            '4f9d1fd5107c50c9a12376b242bcbd21',    # Sciences for Lower Secondary Learners (العربيّة)
            '0d4fd88c4882573caa02110243b94c30',    # Shamsuna Al-Arabiyah: MIT Basic Chemistry (Arabic Subtitles)
            '362ecc59a30e53539f7b8d7fd6f1fcc5',    # ELD King Khaled University Learning (العربيّة)
            '5310274534044fafbad6646a0716b299',    # MIT Blossoms (العربيّة)
            '28590de7af1a4e41824e7574625e1731',    # Math with Basil Al-Zubaidi (العربيّة)
            '310ec19477d15cf7b9fed98551ba1e1f',    # Tahrir Academy
            'b431ba9f16a3588b89700f3eb8281af0',    # Hsoub Academy (العربيّة)
            '09d96cfabec451309066517930bdab9f',    # Sikana (العربية)
            '668a1d198f2e5269939df31dd8c36efb',    # TED Talks Arabic Subtitles
            '0418cc231e9c5513af0fff9f227f7172',    # Free English with Hello Channel
            '61b75af2bb2c4c0ea850d85dcf88d0fd',    # Espresso English
            # 'fdd1dea75e375454b5d8cdcfb52400c2',    # Multaqaddarain K-12 (العربيّة)
            # 'be0ed086641952deb1515b4bb541f7c2',    # Khan Academy (Arabic)
            # 'e8e791651d785bb9b4502598e7f46a42',    # Multaqaddarain Adults (العربيّة)
            # 'f9d3e0e46ea25789bbed672ff6a399ed',    # African Storybook
            # '67f61db3988352249106eee4839e0519',    # Engage NY (العربيّة) [draft]
        ],
        'facility_name': 'New Arabic Demo',
        'hostname': 'kolibridemo-ar.learningequality.org',
    },
    'openupresources-demo': {  # Profuturo channels
        'hosts':['104.196.183.152'],
        'channels_to_import': [],
        'facility_name': 'OLD OpenUp Resources (Illustrative Mathematics) demo',
        'hostname': 'openupresources-demo.learningequality.org',
    },
}





