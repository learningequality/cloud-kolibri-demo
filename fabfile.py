import json
import os

import fabric
from fabric.api import env, execute, task, local, sudo, run
from fabric.api import get, put, execute, require
from fabric.colors import red, green, blue, yellow
from fabric.context_managers import cd, prefix, show, hide, shell_env
from fabric.contrib.files import exists, sed, upload_template
from fabric.utils import puts


# ROLEDEFS
env.roledefs = {
    'unicef-demo': {
        'hosts': ['35.186.182.85'],
        'channels_to_import': ['7d28f53a13e04b309c26268491395f3e'],
        'hostname': 'unicefdemo.learningequality.org',
    },
    'mit-blossoms-demo': {
        'hosts':['35.197.13.137'],
        'channels_to_import': ['913efe9f14c65cb1b23402f21f056e99'],
        'hostname': 'mit-blossoms-demo.learningequality.org', # Does not exist
    },
    'touchable-earth-demo': {
        'hosts':['35.186.190.71'],
        'channels_to_import': ['66cef05505fa550b970e69c3623e82ba'],
        'hostname': 'te-demo.learningequality.org', # Does not exist
    },
    'serlo-demo': {
        'hosts':['35.188.227.233'],
        'channels_to_import': ['c089800ef73e5ef0ac1d0d9e1d193147'],
        'hostname': 'serlo-demo.learningequality.org', # Does not exist
    },
    #
    # NEW
    'mitblossoms-demo': {
        'hosts':['??'],
        'channels_to_import': ['???'],
        'hostname': '???.learningequality.org',
    }
}

# GLOBAL SETTTINGS
env.user = 'ivan'
CONFIG_DIR = './config'

# INSTANCE SETTTINGS
KOLIBRI_PEX_URL = 'https://files.slack.com/files-pri/T0KT5DC58-F664K783T/download/kolibri-v0.4.0-beta11-294-gd1737c50.pex?pub_secret=dbdfe634c7'
KOLIBRI_LANG = 'en' # or 'sw-tz'
KOLIBRI_HOME = '/kolibrihome'
KOLIBRI_PORT = 9090
KOLIBRI_PEX_FILE = os.path.basename(KOLIBRI_PEX_URL.split("?")[0]) # in case ?querystr...


# GCP settings
GCP_ZONE = 'us-east1-d'
GCP_REGION = 'us-east1'

@task
def info():
    run('ps -aux')


@task
def create(instance_name):
    # puts(green('You may need to run `gcloud init` before running this command.'))
    # STEP 1: provision a static IP address
    reserve_ip_cmd =  'gcloud compute addresses create ' + instance_name
    reserve_ip_cmd += ' --region ' + GCP_REGION
    local(reserve_ip_cmd)
    #
    # STEP 2: provision machien
    create_cmd =  'gcloud compute instances create ' + instance_name
    create_cmd += ' --zone ' + GCP_ZONE
    create_cmd += ' --machine-type f1-micro'
    create_cmd += ' --boot-disk-size 30GB'
    create_cmd += ' --image debian-8-jessie-v20170619'
    create_cmd += ' --address ' + instance_name
    create_cmd += ' --format json'
    cmd_out = local(create_cmd, capture=True)
    cmd_result = json.loads(cmd_out)
    new_ip = cmd_result[0]['networkInterfaces'][0]['accessConfigs'][0]['natIP']
    puts(green('Created demo instance ' + instance_name + ' with IP ' + new_ip))
    puts(green('Please update the dictionary `env.roledefs` in `fabfile.py`:'))
    # TODO: print exact dict template that user needed to add...


@task
def delete(instance_name):
    delete_cmd = 'gcloud compute instances delete ' + instance_name + ' --quiet'
    local(delete_cmd)
    delete_ip_cmd = 'gcloud compute addresses delete ' + instance_name + ' --quiet'
    local(delete_ip_cmd)
    puts(green('Deleted instance ' + instance_name + ' and its static IP.'))



@task
def demoserver():
    install_base()
    download_kolibri()
    configure_nginx()
    setup_kolibri()
    import_channels()
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
        run('wget --no-verbose {} -O {}'.format(KOLIBRI_PEX_URL, KOLIBRI_PEX_FILE))
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
def setup_kolibri():
    # startup script
    context = {
        'KOLIBRI_LANG': KOLIBRI_LANG,
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
def restart_kolibri():
    sudo('service nginx restart')
    sudo('service supervisor restart')


@task
def stop_kolibri():
    sudo('service nginx stop')
    sudo('service supervisor stop')

