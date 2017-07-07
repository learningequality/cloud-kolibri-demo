Kolibri demo in the cloud
=========================

Setup a kolibri demo server from any channel.


Install
-------

    virtualenv -p python3  venv
    source venv/bin/activate
    pip install -r requirements.txt



Provision
---------

See [docs/gcp_instance.md](docs/gcp_instance.md).


Using
-----

  1. Provision a virtual machine (see [docs/gcp_instance.md](docs/gcp_instance.md).

  2. Update the `env.roledefs` info in `fabfile.py` inserting appropriate info:
      - A short name for this role, e.g., `serlo-demo`
      - The IP address of the new cloud host
      - The channel id to load into Kolibri
      - A hostname that nginx will listen to (optional)

  3. To provision the demo server, run the command:

         fab demoserver  -R serlo-demo

  4. Go the IP address or hostname and complete the Kolibri setup wizard



