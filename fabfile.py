import os

import fabric
from fabric.api import env, execute, task, local, sudo, run
from fabric.api import get, put, execute, require
from fabric.colors import red, green, blue, yellow
from fabric.context_managers import cd, prefix, show, hide
from fabric.contrib.files import exists, sed, upload_template
from fabric.utils import puts


# HOSTS
env.hosts = [
    '35.188.234.160', # IP address of the demo server
]
env.user = 'ivan'

# GLOBAL SETTTINGS
CONFIG_DIR = './config'

# INSTANCE SETTTINGS
KOLIBRI_PEX_URL = 'https://github.com/learningequality/kolibri/releases/download/v0.4.0-beta10/kolibri-v0.4.0-beta10.pex'
CHANNELS_TO_IMPORT = ['7d28f53a13e04b309c26268491395f3e',]
DEMO_SERVER_HOSTNAME = 'unicef.kolibridemo.learningequality.org'
KOLIBRI_LANG = 'en' # or 'sw-tz'
KOLIBRI_HOME = '/kolibrihome'
KOLIBRI_PORT = 9090
KOLIBRI_PEX_FILE = os.path.basename(KOLIBRI_PEX_URL)


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
    if exists('/etc/nginx/sites-enabled/default'):
        sudo('rm /etc/nginx/sites-enabled/default')
    context = {
        'INSTANCE_PUBLIC_IP': env.host,
        'DEMO_SERVER_HOSTNAME': DEMO_SERVER_HOSTNAME,
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


@task
def import_channels(channel_id):
    """

    """
    base_cmd = 'python ' + os.path.join(KOLIBRI_HOME, KOLIBRI_PEX_FILE) + ' manage'
    with shell_env(KOLIBRI_HOME=KOLIBRI_HOME):
        for channel_id in CHANNELS_TO_IMPORT:
            run(base_cmd + ' importchannel -- network ' + channel_id)
            run(base_cmd + ' importcontent -- network ' + channel_id)


@task
def restart_kolibri():
    sudo('service nginx restart')
    sudo('service supervisor restart')
