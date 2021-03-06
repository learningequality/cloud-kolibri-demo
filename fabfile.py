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


# PREREQUISITES
# 1. SusOps engineer be part of the GCP project kolibri-demo-servers
# 2. The username $USER must be one of the default accounts created on instances, see:
#    https://console.cloud.google.com/compute/metadata?project=kolibri-demo-servers


# FAB SETTTINGS
################################################################################
env.user = os.environ.get('USER')  # assume ur local username == remote username
CONFIG_DIR = './config'

# GCP SETTINGS
################################################################################
GCP_PROJECT = 'kolibri-demo-servers'
GCP_ZONE = 'us-east1-d'
GCP_REGION = 'us-east1'
GCP_BOOT_DISK_SIZE = '30GB'


# KOLIBRI SETTTINGS
################################################################################
KOLIBRI_LANG_DEFAULT = 'en' # or 'sw-tz'
KOLIBRI_HOME = '/kolibrihome'
KOLIBRI_PORT = 9090
KOLIBRI_PEX_URL = 'https://github.com/learningequality/kolibri/releases/download/v0.13.2/kolibri-0.13.2.pex'
KOLIBRI_PEX_FILE = os.path.basename(KOLIBRI_PEX_URL.split("?")[0])  # in case ?querystr...
KOLIBRI_USER = 'kolibri'



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




# PROVIDIONING
################################################################################

@task
def create(instance_name):
    """
    Create a GCP instance `instance_name` and associate a static IP with it.
    """
    # puts(green('You may need to run `gcloud init` before running this command.'))
    # STEP 1: reserve a static IP address
    reserve_ip_cmd =  'gcloud compute addresses create ' + instance_name
    reserve_ip_cmd += ' --project ' + GCP_PROJECT
    reserve_ip_cmd += ' --region ' + GCP_REGION
    local(reserve_ip_cmd)
    #
    # STEP 2: provision instance
    create_cmd =  'gcloud compute instances create ' + instance_name
    create_cmd += ' --project ' + GCP_PROJECT
    create_cmd += ' --zone ' + GCP_ZONE
    create_cmd += ' --machine-type f1-micro'
    create_cmd += ' --boot-disk-size ' + GCP_BOOT_DISK_SIZE
    create_cmd += ' --image-project debian-cloud --image debian-8-jessie-v20170619'
    create_cmd += ' --address ' + instance_name
    create_cmd += ' --tags http-server,https-server'
    create_cmd += ' --format json'
    cmd_out = local(create_cmd, capture=True)
    cmd_result = json.loads(cmd_out)
    new_ip = cmd_result[0]['networkInterfaces'][0]['accessConfigs'][0]['natIP']
    puts(green('Created demo instance ' + instance_name + ' with IP ' + new_ip))
    puts(green('Add this paragraph to the dict `env.roledefs` in `fabfile.py`:'))
    puts(blue("    '%s': {"                                     % instance_name    ))
    puts(blue("        'hosts':['%s'],"                         % new_ip           ))
    puts(blue("        'channels_to_import': ['<channel_id>'],"                    ))
    puts(blue("        'facility_name': '" + instance_name.replace('-', ' ') + "',"))
    puts(blue("        'hostname': '%s.learningequality.org',"  % instance_name    ))
    puts(blue("    },"                                                             ))


@task
def delete(instance_name):
    """
    Delete the GCP instance `instance_name` and it's associated IP address.
    """
    delete_cmd = 'gcloud compute instances delete ' + instance_name + ' --quiet'
    delete_cmd += ' --project ' + GCP_PROJECT
    delete_cmd += ' --zone ' + GCP_ZONE
    local(delete_cmd)
    delete_ip_cmd = 'gcloud compute addresses delete ' + instance_name + ' --quiet'
    delete_ip_cmd += ' --project ' + GCP_PROJECT
    delete_ip_cmd += ' --region ' + GCP_REGION
    local(delete_ip_cmd)
    puts(green('Deleted instance ' + instance_name + ' and its static IP.'))



# HIGH LEVEL API
################################################################################

@task
def demoserver():
    """
    Main setup command that does all the steps.
    """
    install_base()
    download_kolibri()
    configure_nginx()
    configure_kolibri()
    restart_kolibri(post_restart_sleep=65)  # wait for DB migration to happen...
    setup_kolibri()
    import_channels()
    restart_kolibri()
    puts(green('Kolibri demo server setup complete.'))


@task
def update_kolibri(kolibri_lang=KOLIBRI_LANG_DEFAULT):
    """
    Use this task to re-install kolibri:
      - (re)download the Kolibri pex from KOLIBRI_PEX_URL
      - overwrite the startup script /kolibrihome/startkolibri.sh
      - overwrite the supervisor script /etc/supervisor/conf.d/kolibri.conf.
    NOTE: this command fails sporadically; try two times and it will work.
    """
    # install_base()  # Mar 4: disabled because Debian 8 repos no longer avail.
    stop_kolibri()
    download_kolibri()
    # no nginx, because already confured
    configure_kolibri(kolibri_lang=kolibri_lang)
    restart_kolibri(post_restart_sleep=70)  # wait for DB migration to happen...
    # no need to create facily, assume already created
    import_channels()
    restart_kolibri()
    puts(green('Kolibri server update complete.'))


# SYSADMIN TASKS
################################################################################

@task
def install_base():
    """
    Install base system pacakges, add swap, and create application user.
    """
    # 1.
    puts('Installing base system packages (this might take a few minutes).')
    with hide('running', 'stdout', 'stderr'):
        sudo('curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -')
        sudo('apt-get update -qq')
        # sudo('apt-get upgrade -y')  # no need + slows down process for nothing
        sudo('apt-get install -y --force-yes software-properties-common')
        sudo('apt-get install -y curl vim git sqlite3')
        sudo('apt-get install -y python3 python-pip gettext python-sphinx')
        sudo('apt-get install -y nginx')
        sudo('apt-get install -y supervisor')

    # 2.
    if not exists('/var/swap.1'):
        puts('Adding 1G of swap file /var/swap.1')
        sudo('sudo /bin/dd if=/dev/zero of=/var/swap.1 bs=1M count=1024')
        sudo('sudo /sbin/mkswap /var/swap.1')
        sudo('sudo chmod 600 /var/swap.1')
        sudo('sudo /sbin/swapon /var/swap.1')
        # sudo /etc/fstab append:
        # /var/swap.1   swap    swap    defaults        0   0

    # 3.
    if not exists('/home/kolibri'):
        puts('Creating UNIX user ' + KOLIBRI_USER)
        sudo('useradd  --create-home ' + KOLIBRI_USER)

    puts(green('Base install steps finished.'))


@task
def download_kolibri():
    """
    Downloads and installs Kolibri `.pex` file to KOLIBRI_HOME.
    """
    if not exists(KOLIBRI_HOME):
        sudo('mkdir -p ' + KOLIBRI_HOME)
        sudo('chmod 777 ' + KOLIBRI_HOME)
    with cd(KOLIBRI_HOME):
        sudo('wget --no-verbose "{}" -O {}'.format(KOLIBRI_PEX_URL, KOLIBRI_PEX_FILE))
    sudo('chown -R {}:{}  {}'.format(KOLIBRI_USER, KOLIBRI_USER, KOLIBRI_HOME))
    puts(green('Kolibri pex downloaded.'))


@task
def configure_nginx():
    """
    Perform necessary NGINX configurations to forward HTTP traffic to kolibri.
    """
    current_role = env.effective_roles[0]
    demo_server_hostname = env.roledefs[current_role]['hostname']

    if exists('/etc/nginx/sites-enabled/default'):
        sudo('rm /etc/nginx/sites-enabled/default')
    context = {
        'INSTANCE_PUBLIC_IP': env.host,
        'DEMO_SERVER_HOSTNAME': demo_server_hostname,
        'KOLIBRI_HOME': KOLIBRI_HOME,
        'KOLIBRI_PORT': KOLIBRI_PORT,
    }
    upload_template(os.path.join(CONFIG_DIR,'nginx_site.template.conf'),
                    '/etc/nginx/sites-available/kolibri.conf',
                    context=context, use_jinja=True, use_sudo=True, backup=False)
    sudo('chown root:root /etc/nginx/sites-available/kolibri.conf')
    sudo('ln -s /etc/nginx/sites-available/kolibri.conf /etc/nginx/sites-enabled/kolibri.conf')
    sudo('chown root:root /etc/nginx/sites-enabled/kolibri.conf')
    sudo('service nginx reload')
    puts(green('NGINX site kolibri.conf configured.'))


@task
def configure_kolibri(kolibri_lang=KOLIBRI_LANG_DEFAULT):
    """
    Upload kolibri startup script and configure supervisor
    Args:
      - `kolibri_lang` in ['en','sw-tz','es-es','es-mx','fr-fr','pt-pt','hi-in']
    """
    # startup script
    context = {
        'KOLIBRI_LANG': kolibri_lang,
        'KOLIBRI_HOME': KOLIBRI_HOME,
        'KOLIBRI_PORT': KOLIBRI_PORT,
        'KOLIBRI_PEX_FILE': KOLIBRI_PEX_FILE,
    }

    startscript_path = os.path.join(KOLIBRI_HOME, 'startkolibri.sh')
    upload_template(os.path.join(CONFIG_DIR, 'startkolibri.template.sh'),
                    startscript_path,
                    context=context,
                    mode='0755', use_jinja=True, use_sudo=True, backup=False)
    sudo('chown {}:{} {}'.format(KOLIBRI_USER, KOLIBRI_USER, startscript_path))

    # supervisor config
    context = {
        'KOLIBRI_HOME': KOLIBRI_HOME,
        'KOLIBRI_USER': KOLIBRI_USER,
    }
    upload_template(os.path.join(CONFIG_DIR,'supervisor_kolibri.template.conf'),
                    '/etc/supervisor/conf.d/kolibri.conf',
                    context=context, use_jinja=True, use_sudo=True, backup=False)
    sudo('chown root:root /etc/supervisor/conf.d/kolibri.conf')
    sudo('service supervisor restart')
    time.sleep(2)
    puts(green('Kolibri start script and supervisor config done.'))


@task
def setup_kolibri(kolibri_lang=KOLIBRI_LANG_DEFAULT):
    """
    Setup kolibri facility so that
    Args:
      - `kolibri_lang` in ['en','sw-tz','es-es','es-mx','fr-fr','pt-pt','hi-in']
    """
    current_role = env.effective_roles[0]
    role = env.roledefs[current_role]
    facility_name = role.get('facility_name', current_role.replace('-', ' '))
    # facility setup script
    context = {
        'KOLIBRI_LANG': kolibri_lang,
        'KOLIBRI_FACILITY_NAME': facility_name,
    }
    upload_template(os.path.join(CONFIG_DIR, 'setupkolibri.template.sh'),
                    os.path.join(KOLIBRI_HOME, 'setupkolibri.sh'),
                    context=context,
                    mode='0755', use_jinja=True, use_sudo=True, backup=False)
    setup_script_path = os.path.join(KOLIBRI_HOME, 'setupkolibri.sh')
    sudo('chown {}:{} {}'.format(KOLIBRI_USER, KOLIBRI_USER, setup_script_path))
    sudo(setup_script_path, user=KOLIBRI_USER)
    puts(green('Kolibri facility setup done.'))


@task
def import_channels():
    """
    Import the channels in `channels_to_import` using the command line interface.
    """
    current_role = env.effective_roles[0]
    channels_to_import = env.roledefs[current_role]['channels_to_import']
    for channel_id in channels_to_import:
        import_channel(channel_id)
    puts(green('Channels ' + str(channels_to_import) + ' imported.'))


@task
def import_channel(channel_id):
    """
    Import the channels in `channels_to_import` using the command line interface.
    """
    base_cmd = 'python ' + os.path.join(KOLIBRI_HOME, KOLIBRI_PEX_FILE) + ' manage'
    with hide('stdout'):
        with shell_env(KOLIBRI_HOME=KOLIBRI_HOME):
            sudo(base_cmd + ' importchannel network ' + channel_id, user=KOLIBRI_USER)
            sudo(base_cmd + ' importcontent network ' + channel_id, user=KOLIBRI_USER)
    puts(green('Channel ' + channel_id + ' imported.'))


@task
def generateuserdata():
    """
    Generates student usage data to demonstrate more of Kolibri's functionality.
    """
    base_cmd = 'python ' + os.path.join(KOLIBRI_HOME, KOLIBRI_PEX_FILE) + ' manage'
    with shell_env(KOLIBRI_HOME=KOLIBRI_HOME):
        sudo(base_cmd + ' generateuserdata', user=KOLIBRI_USER)
    puts(green('User data generation finished.'))


@task
def restart_kolibri(post_restart_sleep=0):
    sudo('supervisorctl restart kolibri')
    if post_restart_sleep > 0:
        puts(green('Taking a pause for ' + str(post_restart_sleep) + 'sec to let migrations run...'))
        time.sleep(post_restart_sleep)

@task
def stop_kolibri():
    sudo('supervisorctl stop kolibri')

@task
def delete_kolibri():
    stop_kolibri()
    sudo('rm -rf ' + KOLIBRI_HOME)
    sudo('rm /etc/nginx/sites-available/kolibri.conf /etc/nginx/sites-enabled/kolibri.conf')
    sudo('rm /etc/supervisor/conf.d/kolibri.conf')



# UTILS
################################################################################

@task
def info():
    puts(green('Python version:'))
    run('python --version')
    puts(green('/kolibrihome contains:'))
    run('ls -ltr /kolibrihome')
    puts(green('Running processes:'))
    run('ps -aux')


@task
def list_instances(tsv=None):
    """
    Show list of all currently running demo instances.
    Optional tsv argument for easy copy-pasting into spreadsheets.
    """
    cmd = 'gcloud compute instances list'
    cmd += ' --project=kolibri-demo-servers'
    # cmd += ' --format=yaml'
    if tsv is not None:
        cmd += ' --format="csv[separator=\'\t\']('
        cmd += '''name,
                  zone.basename(),
                  networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP,
                  creationTimestamp.date(tz=LOCAL)
                  )"'''
    local(cmd)

@task
def checkdns():
    """
    Checks if DNS lookup matches hosts IP.
    """
    puts(blue('Checking DNS records for all demo servers.'))
    for role_name, role in env.roledefs.items():
        assert len(role['hosts'])==1, 'Multiple hosts found for role'
        host_ip = role['hosts'][0]
        hostname = role['hostname']
        results = []
        try:
            for rdata in dns.resolver.query(hostname, 'A'):
                results.append(rdata)
            results_text = [r.to_text().rstrip('.') for r in results]
            if host_ip in results_text:
                print('DNS for', role_name, 'OK')
            else:
                print('WRONG DNS for', role_name, 'Hostname:', hostname, 'Expected:', host_ip, 'Got:', results_text)
        except dns.resolver.NoAnswer:
            print('MISSING DNS for', role_name, 'Hostname:', hostname, 'Expected:', host_ip)

@task
def checkdiskspace():
    """
    Check available disk space on all demo servers.
    """
    puts(blue('Checking available disk space on all demo servers.'))
    demo_servers = list(env.roledefs.items())
    for role_name, role in demo_servers:
        assert len(role['hosts'])==1, 'Multiple hosts found for role'
        print('role_name', role_name)
        env.host_string = role['hosts'][0]
        run('df -h | grep /dev/sda1')


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
