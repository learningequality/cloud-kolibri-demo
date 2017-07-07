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
    }
}

env.user = 'ivan'

# GLOBAL SETTTINGS
CONFIG_DIR = './config'

# INSTANCE SETTTINGS
KOLIBRI_PEX_URL = 'https://github.com/learningequality/kolibri/releases/download/v0.4.3/kolibri-v0.4.3.pex'
KOLIBRI_LANG = 'en' # or 'sw-tz'
KOLIBRI_HOME = '/kolibrihome'
KOLIBRI_PORT = 9090
KOLIBRI_PEX_FILE = os.path.basename(KOLIBRI_PEX_URL)


@task
def info():
    run('ps -aux')

@task
def provision():
    msg="""
    Manual steps required. Use your favourite cloud host provider
    to provision a virtual machine running Debian. Edit this file
    (`fabfile.py`) to add the cloud host's IP address to `env.hosts`.
    """
    puts(green(msg))

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
