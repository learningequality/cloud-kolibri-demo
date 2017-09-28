Kolibri demo in the cloud
=========================

Setup a kolibri demo server from any channel.


TODO
----
Figure out if KOLIBRI_LANGUAGE is necessary for cmd line or a Facility setting now


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

  3. Go the IP address or hostname and complete the Kolibri setup wizard.
     By convention the Device Owner's username for demo servers is `devowner`.

  4. Optionally, you can generate sample student learning data, so that coach
     views will look more alive:

         fab -R mitblossoms-demo   generateuserdata


Updating
--------
To update the `mitblossoms-demo` server that currently runs an old version of Kolibri,
change `KOLIBRI_PEX_URL` in `fabfile.py` to the URL of the latest release and then run:

    fab -R mitblossoms-demo   update_kolibri

This will download the new pex, overwrite the startup script, and restart Kolibri.

You can also change the language of the Kolibri installation by passing the optional
argument `kolibri_lang`. For example, to switch the `mitblossoms-demo` server to
use French for the Kolibri user interface, run the command:

    fab -R mitblossoms-demo   update_kolibri:kolibri_lang=fr-fr

The people of Québec will love you and buy you a [poutine](https://en.wikipedia.org/wiki/Poutine).



Delete instance
---------------

    fab delete:mitblossoms-demo

