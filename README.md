Aug 3rd: the code in this repo has been moved to https://github.com/learningequality/content-automation-scripts, but fabfile in this repo is still required to update the old demoservers.

[LEGACY] Kolibri demo in the cloud
==================================

Setup a kolibri demo server from any pex and any content channel.


TODO
----
Figure out if KOLIBRI_LANGUAGE is necessary for cmd line or a Facility setting.



GCP Authentication and Authorization
------------------------------------
1. The SushOps engineer who will be running these scripts must be part of the GCP project
[`kolibri-demo-servers`](https://console.cloud.google.com/compute/instances?project=kolibri-demo-servers).
As a first step, try logging in via the web interface and check what can you see.

2. The SushOps engineer must be one of the default sudo accounts specified on the
"compute metadata" tab in the GCP console. The metadata field for ssh-keys must
contain the SushOps engineer's username and their public ssh key. To confirm, see
[here](https://console.cloud.google.com/compute/metadata?project=kolibri-demo-servers).
Note: The scripts assume the SushOps engineer's username on GCP metadata is the
same as on their laptop (Laptop username taken from `echo $USER`).

3. On the command line, you'll have to install `gcloud` command line tools, then
run this to do the complete GCP login song and dance via OAuth login etc:

    gcloud init

To test if you're logged in and authorized to access the GCP project run

    gcloud compute instances list --project=kolibri-demo-servers

You should see all VM instances in the GCP project `kolibri-demo-servers`.



Install
-------

    virtualenv -p python3  venv
    source venv/bin/activate
    pip install -r requirements.txt



Create instance
---------------
Suppose you want to setup a demo server called `mitblossoms-demo`. First you must
create the demo server instance:

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

**NOTE**: currenlty this command fails sporadically, so need to run it twice for it to work.


You can also change the language of the Kolibri installation by passing the optional
argument `kolibri_lang`. For example, to switch the `mitblossoms-demo` server to
use French for the Kolibri user interface, run the command:

    fab -R mitblossoms-demo   update_kolibri:kolibri_lang=fr-fr

The people of Québec will love you and buy you a [poutine](https://en.wikipedia.org/wiki/Poutine).



Delete instance
---------------

    fab delete:mitblossoms-demo

