Kolibri demo in the cloud
=========================

Setup a kolibri demo server from any channel.


Install
-------

    virtualenv -p python3  venv
    source venv/bin/activate
    pip install -r requirements.txt



Using
-----

  1. Provision a virtual machine (see [docs/gcp_instance.md](docs/gcp_instance.md).
  2. Update the `env.hosts` list in `fabfile.py` inserting the IP address of the host.
  3. Run

         fab demoserver

  4. Go the hostname and complete the setup wizard




