Kolibri demo in the cloud
=========================

Setup a kolibri demo server from any channel.


Install
-------

    virtualenv -p python3  venv
    source venv/bin/activate
    pip install -r requirements.txt


Create instance
---------------
Suppose you want to setup a demo server called `mitblossoms-demo`. First you must
create the demo server:

    gcloud init
    fab create:mitblossoms-demo

Note it's also possible to provision a virtual machine using web interface.
See [docs/gcp_instance.md](docs/gcp_instance.md) for more info.


Using
-----

  1. Update the `env.roledefs` info in `fabfile.py` inserting appropriate info:
      - Use the instance name as the key for this role, e.g., `mitblossoms-demo`
      - The IP address of the new cloud host (obtained when created)
      - The channel id to load into Kolibri (obtained from content curation server)
      - A hostname that nginx will listen to (optional)

  2. To provision the demo server, run the command:

         fab -R mitblossoms-demo   demoserver

  3. Go the IP address or hostname and complete the Kolibri setup wizard


Delete instance
---------------

    fab delete:mitblossoms-demo


