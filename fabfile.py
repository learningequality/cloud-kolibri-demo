import dns.resolver
import json
import os
import time

from fabric.api import env, task, local, sudo, run
from fabric.api import get, put, require
from fabric.colors import red, green, blue, yellow
from fabric.context_managers import cd, prefix, show, hide, shell_env
from fabric.contrib.files import exists, sed, upload_template
from fabric.utils import puts


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
# KOLIBRI_PEX_URL = 'https://github.com/learningequality/kolibri/releases/download/v0.7.2/kolibri-0.7.2.pex'
# KOLIBRI_PEX_URL = 'https://github.com/learningequality/kolibri/releases/download/v0.8.0/kolibri-0.8.0.pex'
# KOLIBRI_PEX_URL = 'https://github.com/learningequality/kolibri/releases/download/v0.9.0/kolibri-0.9.0.pex'
KOLIBRI_PEX_URL = 'https://github.com/learningequality/kolibri/releases/download/v0.10.0-alpha4/kolibri-0.10.0.dev4.pex'

KOLIBRI_LANG_DEFAULT = 'en' # or 'sw-tz'
KOLIBRI_HOME = '/kolibrihome'
KOLIBRI_PORT = 9090
KOLIBRI_PEX_FILE = os.path.basename(KOLIBRI_PEX_URL.split("?")[0])  # in case ?querystr...
KOLIBRI_USER = 'kolibri'



# INVENTORY
################################################################################

env.roledefs = {
    'mitblossoms-demo': {
        'hosts':['104.196.162.204'],
        'channels_to_import': ['913efe9f14c65cb1b23402f21f056e99'],
        'hostname': 'mitblossoms-demo.learningequality.org',
    },
    'unicef-demo': {
        'hosts':['104.196.196.6'],
        'channels_to_import': ['7db80873586841e4a1c249b2bb8ba62d'],
        'hostname': 'unicefdemo.learningequality.org',
    },
    'serlo-demo': {
        'hosts':['104.196.182.229'],
        'channels_to_import': ['c089800ef73e5ef0ac1d0d9e1d193147'],
        'hostname': 'serlo-demo.learningequality.org',
    },
    'te-demo': {
        'hosts':['35.190.168.15'],
        'channels_to_import': ['66cef05505fa550b970e69c3623e82ba'],
        'hostname': 'te-demo.learningequality.org',
    },
    'sikana-demo': {
        'hosts':['104.196.110.174'],
        'channels_to_import': [
            '3e9ffc29aa0b59c3bda8d8c7ed179685', # ZH
            '6583e111dac85239bb533f26fae6860d', # ZH-TW
            '757fe48770be588797d731b683fcc243', # RU
            '8ef625db6e86506c9a3bac891e413fff', # FR
            'cfa63fd45abf5b7390b1a41f3b4971bb', # TR
            'fe95a8142b7952e0a0856944a2295951', # PL
            '2871a3680d665bd1a8923660c8c0e1c7', # PT
            'c367b7d7cf625b9aa525972cad27c602', # PT-BR
            '30c71c99c42c57d181e8aeafd2e15e5f', # ES
            '3e464ee12f6a50a781cddf59147b48b1', # EN
        ],
        'hostname': 'sikana-demo.learningequality.org',
    },
    'african-storybook-demo': {
        'hosts':['35.185.108.58'],
        'channels_to_import': ['f9d3e0e46ea25789bbed672ff6a399ed'],
        'hostname': 'african-storybook-demo.learningequality.org', # Does not exist
    },
    'india-demo': {
        'hosts':['35.185.88.71'],
        'channels_to_import': ['053653a2a7fa436a8b3991115db18d25', # Touchable Earth
                               # '620ef30860a65e7d8b2607ed03cc318f', # Pratham Open School (not published yet)
                               '131e543dbecf5776bb13cfcfddf05605', # Pratham Books Storyweaver
                               # '620ef30860a65e7d8b2607ed03cc318f', # Khan Academy (hi)
        ],
        'hostname': 'no.hostname.because.temporary.org',
    },
    'tessa-demo': {
        'hosts':['35.185.77.25'],
        'channels_to_import': ['45605d184d985e74960015190a6f4e4f'],
        'hostname': 'tessa-demo.learningequality.org', # DNE
    },
    'grammar-demo': {
        'hosts':['35.196.177.88'],
        'channels_to_import': ['e1d48c95c88341e5ba3008e4d970a615'],
        'hostname': 'grammar-demo.learningequality.org', # DOES NOT EXIST
    },
    'unete-demo': {
        'hosts':['35.196.220.94'],
        'channels_to_import': ['4d2dea0cdd424c6ab5f76e8244507d6e'],
        'hostname': 'unete-demo.learningequality.org',
    },
    'engageny-demo': {
        'hosts':['104.196.8.90'],
        'channels_to_import': ['ff5988e9bc1b542c96b4568e20144457'],
        'hostname': 'engageny-demo.learningequality.org',
    },
    'aflatoun-demo': {
        'hosts':['35.196.3.200'],
        'channels_to_import': ['8a2d480dbc9b53408c688e8188326b16', '8166e765a0095bfaa49e98d034653dc5'],
        'hostname': 'aflatoun-demo.learningequality.org', # DNE yet
    },
    'openstax-demo': {
        'hosts':['35.196.171.6'],
        'channels_to_import': ['fc47aee82e0153e2a30197d3fdee1128'],
        'hostname': 'openstax-demo.learningequality.org', # DNE
    },
    'le-060-beta': {
        'hosts':['35.185.84.118'],
        'channels_to_import': [
            'fb51dae6df7545af8455aa3a0c32048d',   # Portion Control
            '2b1ca4c771594ff8b28e4a9f6534128b',   # Instant Schools (test)
            '93a5bfcfa2a74962be843288aefcfc0e',   # Khan Academy Hisabati (Tanzania)
            '11d9de56da744f98877cc9fe710bb78d',   # Instan Schools (Math)
        ],
        'facility_name': 'Test Server for 0.6 betas',
        'hostname': 'le-060-beta.learningequality.org',
    },
    'open-osmosis-demo': {
        'hosts':['35.196.195.91'],
        'channels_to_import': ['8b28761bac075deeb66adc6c80ef119c'],
        'facility_name': 'open osmosis demo',
        'hostname': 'open-osmosis-demo.learningequality.org',
    },
    'firki-demo': {
        'hosts':['35.196.111.235'],
        'channels_to_import': ['9fd964d4c40a5ea1b96c1bc1b3830e72'],
        'facility_name': 'firki demo',
        'hostname': 'firki-demo.learningequality.org',  # D.N.E.
    },
    'tahrir-academy-demo': {
        'hosts':['104.196.194.35'],
        'channels_to_import': ['310ec19477d15cf7b9fed98551ba1e1f'],
        'facility_name': 'Tahrir Academy Demo Server',
        'hostname': 'tahrir-academy-demo.learningequality.org',
    },
    'khanacademy': {
        'hosts':['104.196.215.244'],
        'channels_to_import': ['1ceff53605e55bef987d88e0908658c5'],
        'facility_name': 'Khan Academy Demo',
        'hostname': 'khanacademy.learningequality.org',
    },
    'edsitement-demo': {
        'hosts':['35.196.57.174'],
        'channels_to_import': ['2748b6a3569a55f5bd6e35a70e2be7ee'],
        'facility_name': 'EDSITEment demo',
        'hostname': 'edsitement-demo.learningequality.org',
    },
    'openupresources-demo': {
        'hosts':['104.196.183.152'],
        'channels_to_import': ['bafb26304c4a5286ae207764463a5a63'],
        'facility_name': 'OpenUp Resources (Illustrative Mathematics) demo',
        'hostname': 'openupresources-demo.learningequality.org',
    },
    'ict-essentials-demo': {
        'hosts':['35.196.123.247'],
        'channels_to_import': ['8c1eeee6cdbc5599b9e9d928ed793891'],
        'facility_name': 'Rwanda MoW ICT Essentials demo',
        'hostname': 'ict-essentials-demo.learningequality.org',
    },
    'beta4': {
        'hosts':['35.227.41.206'],
        'channels_to_import': [],
        'facility_name': 'Beta4 Test Server',
        'hostname': 'beta4.learningequality.org',
    },
    'ubongo-etl': {
        'hosts':['35.227.43.20'],
        'channels_to_import': [],
        'facility_name': 'ubongo etl',
        'hostname': 'ubongo-etl.learningequality.org',    # Does not exist
    },
    'pradigi-demo': {
        'hosts':['35.196.179.152'],
        'channels_to_import': ['f9da12749d995fa197f8b4c0192e7b2c'],  # PraDigi
        'facility_name': 'PraDigi Demo Server',
        'hostname': 'pradigi-demo.learningequality.org',
    },
    'teachengineering-demo': {
        'hosts':['35.185.118.57'],
        'channels_to_import': ['05ffba594e68590db3c58ee5f345228e'],
        'facility_name': 'teachengineering demo',
        'hostname': 'teachengineering-demo.learningequality.org',
    },
    'davidhu-demo': {
        'hosts':['35.231.113.78'],
        'channels_to_import': ['c150ea1d69495d37b5b0ac6f017e9bfb'],
        'facility_name': 'davidhu demo',
        'hostname': 'davidhu-demo.learningequality.org',  # Does not exist yet
    },
    'gdl-demo': {
        'hosts':['35.185.3.47'],
        'channels_to_import': ['0e173fca6e9052f8a474a2fb84055faf'],
        'facility_name': 'Global Digital Library demo',
        'hostname': 'gdl-demo.learningequality.org',
    },
    'pbs-demo': {
        'hosts':['35.229.41.226'],
        'channels_to_import': ['bc016b653d145d479ff3fe31b9ebd05d'],
        'facility_name': 'PBS demo',
        'hostname': 'pbs-demo.learningequality.org',
    },
    'readwritethink-demo': {
        'hosts':['35.231.98.159'],
        'channels_to_import': ['d6a3e8b17e8a5ac9b021f378a15afbb4'],
        'facility_name': 'readwritethink demo',
        'hostname': 'readwritethink-demo.learningequality.org',
    },
    'commonlit-demo': {
        'hosts':['35.231.45.26'],
        'channels_to_import': ['aa8d785452204e868ebc017fd65c3a58', '1556413bd74c45c59c46353e0be7dd90'],
        'facility_name': 'CommonLit Mexico Demo',
        'hostname': 'commonlit-demo.learningequality.org',
    },
    'tessindia-demo': {
        'hosts':['35.196.85.89'],
        'channels_to_import': ['eac7ff5d4647582d9bcbefea7323fcb1'],
        'facility_name': 'tessindia demo',
        'hostname': 'tessindia-demo.learningequality.org',
    },
    'artsedge-demo': {
        'hosts':['35.196.82.154'],
        'channels_to_import': ['ce1361bcf5955df596e8d988f7ba2c37'],
        'facility_name': 'artsedge demo',
        'hostname': 'artsedge-demo.learningequality.org',
    },
    'kabangla-demo': {
        'hosts':['35.190.185.23'],
        'channels_to_import': ['a03496a6de095e7ba9d24291a487c78d'],
        'facility_name': 'kabangla demo',
        'hostname': 'kabangla-demo.learningequality.org',
    },
    'lauren-demo': {
        'hosts':['35.185.120.102'],
        'channels_to_import': ['9f99140721665ab7802c01998e2d9c30',      # SHLS
                               'd23fa3e3916c5fbc81ec8aa18111744c'],     # Healing Classrooms
        'facility_name': 'lauren demo',
        'hostname': 'lauren-demo.learningequality.org',
    },
    'may-demo': {
        'hosts':['35.196.143.130'],
        'channels_to_import': ['0d07636e2f20510383a7d813c8d4233f',  # Learn English
                               'c7eda62c6489554a941058fa883e7c2c',  # Better World Ed
                               'faf284a5469d54b8b06881491196888e',  # Laboratoria
        ],
        'facility_name': 'May demo',
        'hostname': 'may-demo.learningequality.org',
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
    """
    install_base()
    stop_kolibri()
    download_kolibri()
    # no nginx, because already confured
    configure_kolibri()
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
        sudo('apt-get update -qq')
        # sudo('apt-get upgrade -y')  # no need + slows down process for nothing
        sudo('apt-get install -y software-properties-common')
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
