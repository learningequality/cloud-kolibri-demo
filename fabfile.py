import json
import os
import time

import fabric
from fabric.api import env, execute, task, local, sudo, run
from fabric.api import get, put, execute, require
from fabric.colors import red, green, blue, yellow
from fabric.context_managers import cd, prefix, show, hide, shell_env
from fabric.contrib.files import exists, sed, upload_template
from fabric.utils import puts


# ROLEDEFS
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
}


# GLOBAL SETTTINGS
env.user = os.environ.get('USER')  # assume ur local username == remote username
CONFIG_DIR = './config'

# KOLIBRI SETTTINGS
KOLIBRI_PEX_URL = 'https://github.com/learningequality/kolibri/releases/download/v0.5.0-beta8/kolibri-v0.5.0-beta8.pex'
KOLIBRI_LANG_DEFAULT = 'en' # or 'sw-tz'
KOLIBRI_HOME = '/kolibrihome'
KOLIBRI_PORT = 9090
KOLIBRI_PEX_FILE = os.path.basename(KOLIBRI_PEX_URL.split("?")[0])  # in case ?querystr...

# GCP SETTINGS
GCP_ZONE = 'us-east1-d'
GCP_REGION = 'us-east1'
GCP_BOOT_DISK_SIZE = '30GB'


@task
def create(instance_name):
    """
    Create a GCP instance `instance_name` and associate a static IP with it.
    """
    # puts(green('You may need to run `gcloud init` before running this command.'))
    # STEP 1: reserve a static IP address
    reserve_ip_cmd =  'gcloud compute addresses create ' + instance_name
    reserve_ip_cmd += ' --region ' + GCP_REGION
    local(reserve_ip_cmd)
    #
    # STEP 2: provision instance
    create_cmd =  'gcloud compute instances create ' + instance_name
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
    puts(blue("    '%s': {"                                     % instance_name ))
    puts(blue("        'hosts':['%s'],"                         % new_ip        ))
    puts(blue("        'channels_to_import': ['<channel_id>'],"                 ))
    puts(blue("        'hostname': '%s.learningequality.org',"  % instance_name ))
    puts(blue("    },"                                                          ))


@task
def delete(instance_name):
    """
    Delete the GCP instance `instance_name` and it's associated IP address.
    """
    delete_cmd = 'gcloud compute instances delete ' + instance_name + ' --quiet'
    local(delete_cmd)
    delete_ip_cmd = 'gcloud compute addresses delete ' + instance_name + ' --quiet'
    local(delete_ip_cmd)
    puts(green('Deleted instance ' + instance_name + ' and its static IP.'))



@task
def demoserver():
    """
    Main setup command that does all the steps.
    """
    install_base()
    download_kolibri()
    configure_nginx()
    setup_kolibri()
    restart_kolibri(post_restart_sleep=30)  # wait for DB migration to happen...
    import_channels()
    restart_kolibri()
    puts(green('Kolibri demo server setup complete.'))


@task
def install_base():
    """
    Updates base system and installs prerequisite system pacakges.
    """
    puts('Installing and updating base system (might take a few minutes).')
    with hide('running', 'stdout', 'stderr'):
        sudo('apt-get update -qq')
        sudo('apt-get upgrade -y')
        sudo('apt-get install -y software-properties-common curl')
        sudo('apt-get install -y python3 python-pip git gettext python-sphinx')
        sudo('apt-get install -y nginx')
        sudo('apt-get install -y supervisor')
    puts(green('Base packages installed.'))


@task
def download_kolibri():
    """
    Downloads and installs Kolibri `.pex` file to KOLIBRI_HOME.
    """
    if not exists(KOLIBRI_HOME):
        sudo('mkdir -p ' + KOLIBRI_HOME)
        sudo('chmod 777 ' + KOLIBRI_HOME)
    with cd(KOLIBRI_HOME):
        run('wget --no-verbose "{}" -O {}'.format(KOLIBRI_PEX_URL, KOLIBRI_PEX_FILE))
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
    sudo('ln -s /etc/nginx/sites-available/kolibri.conf /etc/nginx/sites-enabled/kolibri.conf')
    sudo('service nginx restart')
    puts(green('NGINX site kolibri.conf configured.'))


@task
def setup_kolibri(kolibri_lang=KOLIBRI_LANG_DEFAULT):
    """
    Setup kolibri startup script and supervisor config.
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

    upload_template(os.path.join(CONFIG_DIR, 'startkolibri.template.sh'),
                    os.path.join(KOLIBRI_HOME, 'startkolibri.sh'),
                    context=context,
                    mode='0755', use_jinja=True, use_sudo=True, backup=False)

    # supervisor config
    context = {
        'KOLIBRI_HOME': KOLIBRI_HOME,
    }
    upload_template(os.path.join(CONFIG_DIR,'supervisor_kolibri.template.conf'),
                    '/etc/supervisor/conf.d/kolibri.conf',
                    context=context, use_jinja=True, use_sudo=True, backup=False)
    sudo('service supervisor restart')
    puts(green('Kolibri start script and supervisor setup done.'))


@task
def import_channels():
    """
    Import the channels in `channels_to_import` using the command line interface.
    """
    current_role = env.effective_roles[0]
    channels_to_import = env.roledefs[current_role]['channels_to_import']
    base_cmd = 'python ' + os.path.join(KOLIBRI_HOME, KOLIBRI_PEX_FILE) + ' manage'
    with hide('stdout'):
        with shell_env(KOLIBRI_HOME=KOLIBRI_HOME):
            for channel_id in channels_to_import:
                run(base_cmd + ' importchannel -- network ' + channel_id)
                run(base_cmd + ' importcontent -- network ' + channel_id)
    puts(green('Channels ' + str(channels_to_import) + ' imported.'))


@task
def generateuserdata():
    """
    Generates student usage data to demonstrate more of Kolibri's functionality.
    """
    base_cmd = 'python ' + os.path.join(KOLIBRI_HOME, KOLIBRI_PEX_FILE) + ' manage'
    with shell_env(KOLIBRI_HOME=KOLIBRI_HOME):
        run(base_cmd + ' generateuserdata')
    puts(green('User data generation finished.'))


@task
def info():
    puts(green('Python version:'))
    run('python --version')
    puts(green('/kolibrihome contains:'))
    run('ls -ltr /kolibrihome')
    puts(green('Running processes:'))
    run('ps -aux')


@task
def restart_kolibri(post_restart_sleep=0):
    sudo('service nginx restart')
    sudo('service supervisor restart')
    if post_restart_sleep > 0:
        puts(green('Taking a pause for ' + str(post_restart_sleep) + 'sec to let migrations run...'))
        time.sleep(post_restart_sleep)


@task
def stop_kolibri():
    sudo('service nginx stop')
    sudo('service supervisor stop')


@task
def delete_kolibri():
    stop_kolibri()
    sudo('rm -rf ' + KOLIBRI_HOME)
    sudo('rm /etc/nginx/sites-available/kolibri.conf /etc/nginx/sites-enabled/kolibri.conf')
    sudo('rm /etc/supervisor/conf.d/kolibri.conf')


@task
def update_kolibri(kolibri_lang=None):
    """
    Use this task to re-install kolibri:
      - (re)download the Kolibri pex from KOLIBRI_PEX_URL
      - overwrite the startup script /kolibrihome/startkolibri.sh
      - overwrite the supervisor script /etc/supervisor/conf.d/kolibri.conf.
    """
    stop_kolibri()
    download_kolibri()
    setup_kolibri(kolibri_lang=kolibri_lang)
    restart_kolibri()

