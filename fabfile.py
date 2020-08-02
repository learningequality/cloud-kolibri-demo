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








# PROXY SERVICE
################################################################################

@task
def install_squid_proxy():
    """
    Install squid3 package and starts it so demoserver can be used as HTTP proxy.
    Note this rquires opening port 3128 on from the GCP console for this server,
    which can be done by applying the "Network tag" `allow-http-proxy-3128`.
    """
    with settings(warn_only=True):
         sudo('apt-get -y install squid3')
    put('config/etc_squid3_squid.conf', '/etc/squid3/squid.conf', use_sudo=True)
    sudo('service squid3 restart')
    puts('\n')
    puts(green('Proxy service started on ' + str(env.host)))
    puts('Next steps:')
    puts('  1. Visit https://console.cloud.google.com/compute/instances?project=kolibri-demo-servers&organizationId=845500209641&instancessize=50')
    puts('     and add the Network Tag  "allow-http-proxy-3128" to the server ' + env.effective_roles[0])
    puts('  2. After that you can append {}:{} to the PROXY_LIST used for cheffing.'.format(env.host, '3128'))

@task
def update_squid_proxy():
    """
    Update the /etc/squid3/squid.conf on all proxy hosts.
    Use this command to add new IP addresses to the lecheffers ACL group.
    """
    proxy_hosts = checkproxies()
    puts(green('Updating the proxy service config file /etc/squid3/squid.conf for'))
    puts(green('proxy_hosts = ' + str(proxy_hosts)))
    for host in proxy_hosts:
        env.host_string = host
        with hide('running', 'stdout', 'stderr'):
            hostname = run('hostname')
        puts(green('Updting proxy config on ' + hostname))
        sudo('service squid3 stop')
        put('config/etc_squid3_squid.conf', '/etc/squid3/squid.conf', use_sudo=True)
        sudo('service squid3 start')
    puts(green('All proxy servers updated successfully.'))


@task
def uninstall_squid_proxy():
    """
    Stop and uninstall squid3 proxy on the demoserver.
    """
    sudo('service squid3 stop')
    with settings(warn_only=True):
         sudo('apt-get -y purge squid3')
    puts(green('Proxy service removed from ' + str(env.host)))
    puts(blue('**Please remove {}:{} from PROXY_LIST used for cheffing.**'.format(env.host, '3128')))


@task
def checkproxies():
    """
    Check which demoservers have port 3128 open and is running a proxy service.
    """
    puts(green('Checking proxy service available on all demo servers.'))
    demo_servers = list(env.roledefs.items())
    proxy_hosts = []
    for role_name, role in demo_servers:
        assert len(role['hosts'])==1, 'Multiple hosts found for role'
        host = role['hosts'][0]
        print('Checking role_name=', role_name, 'host=', host)
        # check if we proxy port is open on host
        proxy_port_open = False
        port = 3128  # squid3 default proxy port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        proxy_port_open = True if result == 0 else False
        sock.close()
        if proxy_port_open:
            puts('    - proxy port open on {} demoserver'.format(role_name))
            proxy_hosts.append(host)
    PROXY_LIST_value = ';'.join(host+':3128' for host in proxy_hosts)
    puts(blue('Use the following command to set the PROXY_LIST env var:\n'))
    puts(blue('  export PROXY_LIST="' + PROXY_LIST_value + '"'))
    return proxy_hosts



# CATALOG DEMO SERVERS
################################################################################

STUDIO_URL = 'https://studio.learningequality.org'
API_PUBLIC_ENDPOINT = '/api/public/v1/channels'

CATALOG_URL = "https://catalog.learningequality.org"
API_CATALOG_ENDPOINT = "/api/catalog?page_size=200&public=true&published=true"

CATALOG_DEMO_SERVERS = {
    'ar': 'https://kolibri-catalog-ar.learningequality.org',
    'en': 'https://kolibri-catalog-en.learningequality.org',
    'es': 'https://kolibri-catalog-es.learningequality.org',
    'fr': 'https://kolibri-catalog-fr.learningequality.org',
    'hi': 'https://kolibri-catalog-hi.learningequality.org',
    'other': 'https://kolibri-demo.learningequality.org',
}




@task
def check_catalog_channels():
    """
    Obtain the list of public channels on Kolibri Studio and compare with the
    list of channels imported on the catalog demo servers. Prints the following:
      - list channels that are not present on any demo servers
      - list channels that are oudated (studio version > version on demo server)
      - list channels with missing or broken demo_server_url
    """
    # 1. Get Studio channels
    studio_channels = requests.get(STUDIO_URL + API_PUBLIC_ENDPOINT).json()
    studio_channels_by_id = dict((ch['id'], ch) for ch in studio_channels)
    print('Found', len(studio_channels_by_id), 'PUBLIC channels on Studio.')

    # 2. Get Catalog channels
    catalog_data = requests.get(CATALOG_URL + API_CATALOG_ENDPOINT).json()
    catalog_channels = catalog_data['results']
    catalog_channels_by_id = dict((ch['id'], ch) for ch in catalog_channels)
    print('Found', len(studio_channels_by_id), 'PUBLIC channels in Catalog.')

    # 3. Get Catalog demo server channels
    demoserver_channels = []
    for lang, demoserver in CATALOG_DEMO_SERVERS.items():
        # print('   - getting channel list from the', lang, 'demoserver...')
        channels = requests.get(demoserver + API_PUBLIC_ENDPOINT).json()
        for channel in channels:
            channel['demoserver'] = demoserver
            channel['lang'] = lang
            demoserver_channels.append(channel)
    # group all channels found by `channel_id`
    demoserver_channels_by_id = defaultdict(list)
    for ch in demoserver_channels:
        ch_id = ch['id']
        demoserver_channels_by_id[ch_id].append(ch)
    print('Found', len(demoserver_channels_by_id), 'channels on demoservers.')

    # Sanity check: Studio channels and Catalog channels should be identical
    studio_ids = set(studio_channels_by_id.keys())
    catalog_ids = set(catalog_channels_by_id.keys())
    if studio_ids != catalog_ids:
        print('WARNING: Studio PUBCLIC channels and Catalog channels differ!')


    # REPORT A: PUBLIC channels must be imported on at least one demoserver
    print('\n\nREPORT A: Check no channels missing from catalog demoservers:')
    for ch_id, studio_ch in studio_channels_by_id.items():
        if ch_id not in demoserver_channels_by_id:
            print(' - Cannot find', ch_id, studio_ch['name'])

    # REPORT B: Catalog demoservers must have the latest version of the channel
    print('\n\nREPORT B: Check channel versions on catalog demoservers:')
    for ch_id, studio_ch in studio_channels_by_id.items():
        latest_version = studio_ch["version"]
        if ch_id in demoserver_channels_by_id:
            demoserver_channels = demoserver_channels_by_id[ch_id]
            for channel in demoserver_channels:
                if channel["version"] < latest_version:
                    print(' - Channel', ch_id, studio_ch['name'], 'needs to be updated on', channel['demoserver'])

    # REPORT C: Catalog demoservers links must point to an existing channel
    print('\n\nREPORT C: Check the demo_server_url links in Catalog are good:')
    for ch_id, catalog_ch in catalog_channels_by_id.items():
        demo_server_url = catalog_ch["demo_server_url"]
        if demo_server_url:
            if ch_id not in demo_server_url:
                print(' - ERROR: demo_server_url', demo_server_url, 'does not contain', ch_id)
            parsed_url_obj = urlparse(demo_server_url)
            catalog_demoserver = parsed_url_obj.scheme + '://' + parsed_url_obj.netloc
            if ch_id in demoserver_channels_by_id:
                found = False
                demoserver_channels = demoserver_channels_by_id[ch_id]
                for channel in demoserver_channels:
                    if channel['demoserver'] == catalog_demoserver:
                        found = True
                if not found:
                    print(' - Channel', ch_id, catalog_ch['name'], 'has demo_server_url',
                        demo_server_url, 'but it is not present on that server')
        else:
            print(' - Channel', ch_id, catalog_ch['name'], 'does not have a demo_server_url')
